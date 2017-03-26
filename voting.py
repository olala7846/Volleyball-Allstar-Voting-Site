# -*- coding: utf-8 -*-
# voting app
from datetime import datetime
from dateutil import parser
from flask import Flask, render_template, request
from flask import abort, redirect
from google.appengine.ext import ndb
from itertools import groupby
from models import Election
from sendgrid import Mail
from sendgrid import SendGridClient
from voting_backend import _update_election_status
from utils import get_or_create_voting_user
from utils import get_user_from_token
from utils import send_voting_email
from utils import sanitize_email_local_part
from utils import do_vote

import logging
import secrets
import pytz

logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='./templates')
app.config['DEBUG'] = False

# make a secure connection to SendGrid
sg = SendGridClient(
    secrets.SENDGRID_ID, secrets.SENDGRID_PASSWORD, secure=True)


# Define template filters
@app.template_filter('aj')
def angular_js_filter(s):
    """ example: {{'angular expressioins'|aj}} """
    return '{{'+s+'}}'


@app.template_filter('datetime')
def format_datetime(date_string):
    """ Formats no tzinfo datetime to Asia/Taipei date string """
    UTC = pytz.utc
    TAIPEI_TZ = pytz.timezone('Asia/Taipei')

    no_tz_dt = parser.parse(date_string)
    local_dt = no_tz_dt.replace(tzinfo=UTC).astimezone(TAIPEI_TZ)
    return local_dt.strftime('%m/%d/%Y %H:%M')


# -------- pages --------
@app.route("/", methods=['GET'])
def landing_page():
    """Find all available elections"""
    elections = [e.serialize() for e in Election.available_elections()]
    return render_template('landing.html', elections=elections)


@app.route("/register/<websafe_election_key>/", methods=['GET', 'POST'])
def register_vote(websafe_election_key):
    if request.method == 'GET':
        election_key = ndb.Key(urlsafe=websafe_election_key)
        election = election_key.get()
        if not election or not election.can_vote:
            abort(404)
        election_data = election.serialize()
        return render_template('register.html', election=election_data)

    elif request.method == 'POST':
        post_data = request.form
        if 'student_id' not in post_data:
            abort(500)

        raw_sid = post_data.get('student_id').lower()
        sanitized_sid = sanitize_email_local_part(raw_sid)
        try:
            voting_user = get_or_create_voting_user(
                websafe_election_key, sanitized_sid)
        except ValueError as e:
            logger.error('Error creating user: %s', e.message)
            abort(500)

        if voting_user.voted:
            voted_url = "/voted/%s/" % websafe_election_key
            return redirect(voted_url, 301)
        elif not voting_user.mail_sent_recently:
            # sent mail if not recently sent
            try:
                send_voting_email(voting_user)
            except Exception:
                logger.error('Error sending mail: %s', sanitized_sid)
                return abort(500)
        else:
            logger.info('mail not really sent')

        return redirect('/mail_sent', 301)


@app.route("/vote/<token>/", methods=['GET'])
def get_vote_page(token):
    """ Display vote page from url in email

    <token>: unique token stored in UserProfile
    """
    user = get_user_from_token(token)
    if user is None:
        abort(404)

    election = user.key.parent().get()
    if not isinstance(election, Election):
        logger.error('Got user without election as ancestor')
        abort(500)

    if not election.can_vote:
        msg = u'投票已結束'
        return render_template('message.html', message=msg)

    if user.voted:
        voted_url = "/voted/%s/" % user.election_key.urlsafe()
        return redirect(voted_url, code=301)
    else:
        election = user.election_key.get()
        election_dict = election.cached_deep_serialize()
        return render_template('vote.html',
                               election=election_dict,
                               token=token,
                               user=user)  # pass token for angular


@app.route("/api/vote/<token>/", methods=['POST'])
def vote_with_data(token):
    """ Save user selected candidates in database and update
        user.voted and candidate.num_votes

    <token>: unique token relative to a VotingUser
    candidate_ids: list of datastore candidate keys
        in urlsafe format
    """
    user = get_user_from_token(token)
    post_data = request.get_json()
    candidate_ids = post_data['candidate_ids']
    logger.info('receive %s vote', user)
    if user is None:
        return abort(403, 'Invalid token')

    # check vote count valid
    candidate_keys = [ndb.Key(urlsafe=key) for key in candidate_ids]
    candidates = ndb.get_multi(candidate_keys)

    def _get_position_key(candidate):
        return candidate.key.parent()
    candidates = sorted(candidates, key=_get_position_key)
    for key, group in groupby(candidates, key=_get_position_key):
        position = key.get()
        if position.votes_per_person < len(list(group)):
            return abort(403, 'Invalid votes')

    try:
        do_vote(user.key, candidate_keys)
    except Exception:
        abort(403, 'Transaction fail')
    return 'success'


@app.route("/results/<websafe_election_key>/", methods=['GET'])
def see_results(websafe_election_key):
    # Get result of last minute
    election = ndb.Key(urlsafe=websafe_election_key).get()
    election_dict = election.cached_deep_serialize()
    return render_template('results.html', election=election_dict)


@app.route("/mail_sent/", methods=['GET'])
def mail_sent():
    message = u"信件寄送中..."
    url = {
        'title': u'前往台大信箱',
        'href': 'http://mail.ntu.edu.tw/'
    }
    return render_template('message.html', message=message, url=url)


@app.route("/sent_failed/", methods=['GET'])
def sent_failed():
    message = u"郵件寄送失敗，請稍候再試一次"
    url = {
        'title': u'回投票首頁',
        'href': '/'
    }
    return render_template('message.html', message=message, url=url)


@app.route("/voted/<websafe_election_key>/", methods=['GET'])
def already_voted(websafe_election_key):
    election = ndb.Key(urlsafe=websafe_election_key).get()
    if not election:
        abort(500)
    message = u"抱歉，您已經投過票"
    url = {
        'title': u'觀看投票結果',
        'href': '/results/'+websafe_election_key
    }
    return render_template('message.html', message=message, url=url)


@app.errorhandler(500)
@app.route("/error/", methods=['GET'])
def error_page():
    message = u"發生錯誤，請稍後再試或聯絡工作人員"
    return render_template('message.html', message=message)


@app.errorhandler(404)
def page_not_found(error):
    logger.error('404 not found: %s', request)
    msg = u'<i class="fa fa-frown-o"></i> %s' % u'Oops! 迷路了嗎？'
    return render_template('message.html', message=msg)


"""
Mail handler
"""


@app.route("/queue/mail", methods=['POST'])
def send_mail():
    """
    Send email with sendgrid sdk
    """
    to_email = request.form.get('to')
    subject = request.form.get('subject')
    body = request.form.get('body')
    text_body = request.form.get('text_body')
    from_email = request.form.get('from')

    utf8_body = body.encode('utf-8')
    utf8_text_body = text_body.encode('utf-8')

    message = Mail()
    message.set_subject(subject)
    message.set_html(utf8_body)
    message.set_text(utf8_text_body)
    message.set_from(from_email)
    message.add_to(to_email)
    sg.send(message)
    logger.info("Email is sent to %s" % to_email)
    return ('', 204)


@app.route("/cron/update_status", methods=['GET'])
def update_status():
    running_cnt = _update_election_status()
    msg = '%d elections running, now: %s' % (running_cnt, datetime.now())
    return msg


if __name__ == "__main__":
    app.run()
