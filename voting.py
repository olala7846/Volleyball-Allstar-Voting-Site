# -*- coding: utf-8 -*-
# voting app

from datetime import datetime
from dateutil import parser
from flask import Flask, render_template, request
from flask import abort, redirect
from google.appengine.api.taskqueue import Queue, Task
from google.appengine.ext import ndb
from itertools import groupby
from models import VotingUser, Election
from sendgrid import Mail
from sendgrid import SendGridClient
from voting_backend import _update_election_status
import logging
import secrets
import uuid
import pytz

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['DEBUG'] = True

# make a secure connection to SendGrid
sg = SendGridClient(secrets.SENDGRID_ID,
                    secrets.SENDGRID_PASSWORD,
                    secure=True)


# -------- utils --------
@ndb.transactional(retries=3)
def _get_or_create_voting_user(websafe_election_key, student_id):
    election_key = ndb.Key(urlsafe=websafe_election_key)
    if election_key is None:
        raise ValueError('Invalid election key')
    if student_id != student_id.lower():
        raise ValueError('Student ID should be lower case')

    voting_user_key = ndb.Key(VotingUser, student_id, parent=election_key)
    voting_user = voting_user_key.get()
    if not voting_user:
        token = str(uuid.uuid4().hex)
        voting_user = VotingUser(id=student_id,
                                 student_id=student_id,
                                 parent=election_key,
                                 token=token)
        voting_user_key = voting_user.put()
    return voting_user


def _get_user_from_token(token):
    """ Returns corresponding VotingUser """
    user = VotingUser.query(VotingUser.token == token).get()
    return user


@ndb.transactional(xg=True, retries=3)
def _do_vote(user_key, candidate_keys):
    """ Save vote to database after integrity check
    user_key: VotingUser ndb key
    candidate_yes: list of Candidate ndb key
    """
    # check user not voted
    user = user_key.get()  # check latest value
    if user.voted:
        raise Exception('Already voted')

    candidates = ndb.get_multi(candidate_keys)
    for candidate in candidates:
        candidate.num_votes = candidate.num_votes + 1
    ndb.put_multi(candidates)

    user.votes = candidate_keys
    user.voted = True
    user.put()


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


def _send_voting_email(voting_user):
    """ Create voting user and add voting email to mail-queue
    Input:
        voting_user: VotingUser, the user to be sent.
    """
    # Make email content with token-link
    election = voting_user.key.parent().get()
    if not isinstance(election, Election):
        msg = 'voting_user should have election as ndb ancestor'
        raise ValueError(msg)

    voting_link = "http://ntuvb-allstar.appspot.com/vote/"\
                  + voting_user.token
    from_email = "NTUManVolley@gmail.com"
    email_body = (
        u"<h3>您好 {student_id}:</h3>"
        u"<p>感謝您參與{election_title} <br>"
        u"<h4><a href='{voting_link}'> 投票請由此進入 </a></h4> <br>"
        u"<p><b style=\"color: red\">此為您個人的投票連結，請勿轉寄或外流</b><br>"
        u"若您未參與本次投票，請直接刪除本封信件 <br>"
        u"任何疑問請來信至: {help_mail} <br></p>"
    ).format(
        student_id=voting_user.student_id,
        election_title=election.title,
        voting_link=voting_link,
        help_mail=from_email)
    text_body = u"投票請進: %s" % voting_link
    email_subject = election.title+u"投票認證信"
    to_email = voting_user.student_id+"@ntu.edu.tw"

    queue = Queue('mail-queue')
    queue.add(Task(
        url='/queue/mail',
        params={
            'subject': email_subject,
            'body': email_body,
            'text_body': text_body,
            'to': to_email,
            'from': from_email,
        }
    ))

    voting_user.last_time_mail_queued = datetime.now()
    key = voting_user.put()
    key.get()  # for strong consistency


# -------- pages --------
@app.route("/", methods=['GET'])
def welcome():
    elections = [e.serialize() for e in Election.available_elections()]
    return render_template('welcome.html', elections=elections)


@app.route("/register/<websafe_election_key>/", methods=['GET', 'POST'])
def voting_index(websafe_election_key):
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

        lowercase_student_id = post_data.get('student_id').lower()
        try:
            voting_user = _get_or_create_voting_user(
                    websafe_election_key, lowercase_student_id)
        except ValueError as e:
            logger.error('Error creating user: %s', e.message)
            abort(500)

        if voting_user.voted:
            voted_url = "/voted/%s/" % websafe_election_key
            return redirect(voted_url, 301)
        elif not voting_user.mail_sent_recently:
            # sent mail if not recently sent
            try:
                _send_voting_email(voting_user)
            except Exception:
                logger.error('Error sending mail: %s', lowercase_student_id)
                return abort(500)
        else:
            logger.info('mail not really sent')

        return redirect('/mail_sent', 301)


@app.route("/vote/<token>/", methods=['GET'])
def get_vote_page(token):
    """ Display vote page from url in email

    <token>: unique token stored in UserProfile
    """
    user = _get_user_from_token(token)

    election = user.key.parent().get()
    if not isinstance(election, Election):
        logger.error('Got user without election as ancestor')
        abort(500)

    if not election.can_vote:
        msg = u'投票已結束'
        return render_template('message.html', message=msg)

    if user is None:
        abort(404)

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
    user = _get_user_from_token(token)
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
        _do_vote(user.key, candidate_keys)
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
