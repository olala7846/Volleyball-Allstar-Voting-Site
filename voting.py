# -*- coding: utf-8 -*-
# voting app

from flask import Flask, render_template, request, jsonify, abort
from google.appengine.ext import ndb
from sendgrid import SendGridClient
from sendgrid import Mail
from models import VotingUser, Election
import secrets
from dateutil import parser

from datetime import datetime
from itertools import groupby
import uuid
import math
import logging

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['DEBUG'] = True  # turn to false on production

# make a secure connection to SendGrid
sg = SendGridClient(secrets.SENDGRID_ID, secrets.SENDGRID_PASSWORD, secure=True)


# -------- utils --------
@ndb.transactional(retries=3)
def _get_or_create_voting_user(websafe_election_key, student_id):
    election_key = ndb.Key(urlsafe=websafe_election_key)
    if election_key is None:
        raise Exception('Invalid election key')
    if student_id != student_id.lower():
        raise Exception('Student ID should be lower case')
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


def _get_post_data(request):
    """ returns post data both form/json format """
    content_type = request.headers['Content-Type']
    post_data = None
    if 'application/x-www-form-urlencoded' in content_type:
        post_data = request.form
    elif 'application/json' in content_type:
        post_data = request.get_json()
    else:
        logger.error('Unexpected Content-Type format: %s',
                     content_type)
    return post_data


@ndb.transactional(xg=True, retries=3)
def _do_vote(user_key, candidate_keys):
    """ Save vote to database after integrity check
    user_key: VotingUser ndb key
    candidate_yes: list of Candidate ndb key
    """
    # check user not voted
    user = user_key.get()  # check latest value
    if user.voted:
        logger.error('_do_vote: %s already voted', user.student_id)
        raise Exception('Already voted')

    user.votes = candidate_keys
    user.voted = True
    user.put()

    candidates = ndb.get_multi(candidate_keys)
    for candidate in candidates:
        candidate.num_votes = candidate.num_votes + 1
    ndb.put_multi(candidates)


@app.template_filter('aj')
def angular_js_filter(s):
    """ example: {{'angular expressioins'|aj}} """
    return '{{'+s+'}}'


@app.template_filter('datetime')
def format_datetime(date_string):
    """ format ISO string into MM/DD/YYYY """
    date = parser.parse(date_string)
    return date.strftime('%m/%d/%Y')


def _send_voting_email(voting_user):
    """ Create voting user and send voting email with token to user
    Input:
        voting_user: VotingUser, the user to be sent.
    Output:
        is_sent: bool, an email is sent successfully.
    """
    # Make email content with token-link
    voting_link = "http://ntuvb-allstar.appspot.com/vote/"\
                  + voting_user.token
    email_content = u"投票請進：" + voting_link

    # Send email by gmail api
    message = Mail()
    message.set_subject("2016台大排球明星賽投票認證信")
    message.set_text(email_content)
    message.set_from("ins.huang@gmail.com")
    message.add_to(voting_user.student_id + "@ntu.edu.tw")
    sg.send(message)

    # Record email count
    voting_user.email_count += 1
    key = voting_user.put()
    key.get()  # for strong consistency

    logger.info("Email is sent to %s" % voting_user.student_id)
    return True


def _get_rest_wait_time(voting_user):
    """ Create voting user and send voting email with token to user
    Input:
        voting_user: VotingUser, the user to be sent.
    Output:
        rest_wait_time: int, the rest wait time in minute.
    """
    if voting_user.email_count > 0:
        time_since_create = (datetime.now() - voting_user.create_time)
        minute_diff = int(time_since_create.total_seconds() / 60)
        minutes_should_wait = 10 * math.pow(2, voting_user.email_count - 1)
        if minute_diff < minutes_should_wait:
            return minutes_should_wait - minute_diff
    return 0


# -------- pages --------
@app.route("/", methods=['GET'])
def welcome():
    elections = [e.serialize() for e in Election.unfinished_elections()]
    return render_template('welcome.html', elections=elections)


@app.route("/register/<websafe_election_key>/", methods=['GET'])
def voting_index(websafe_election_key):
    election_key = ndb.Key(urlsafe=websafe_election_key)
    election = election_key.get()
    if not election or not election.started:
        abort(404)
    election_data = election.serialize()
    return render_template('register.html', election=election_data)


@app.route("/api/send_voting_email", methods=["POST"])
def send_voting_email():
    """ Create voting user and send voting email with token to user
    Input:
        student_id: string, student_id.
        forced_send: bool, send voting email anyway.
        election_key: target election urlsafe key
    Output:
        is_sent: bool, an email is sent in this request.
        rest_wait_time: int, the rest wait time to send email in minute.
        voted: bool, whether the user is voted.
        error_message: str, be empty string if no error.
    Error message:
        returns 200 OK but with response.data
        'already voted'
        'send fail'
    """
    post_data = _get_post_data(request)
    lowercase_student_id = post_data.get('student_id').lower()
    forced_send = True if post_data.get('forced_send') == 'true' else False
    websafe_election_key = post_data['election_key']
    is_sent = False
    error_message = ""
    rest_wait_time = 0

    voting_user = _get_or_create_voting_user(
            websafe_election_key, lowercase_student_id)
    if voting_user.voted:
        return 'already voted'

    try:
        # Only send voting email to existing user when forced_send is set
        # and less than 3 emails are sent for the user.
        rest_wait_time = _get_rest_wait_time(voting_user)
        if voting_user.email_count == 0 or (
                forced_send and rest_wait_time == 0):
            is_sent = _send_voting_email(voting_user)
    except Exception, e:
        logger.error("Error in send_voting_email")
        logger.error("student_id: %s, forced_send: %s" % (
            lowercase_student_id, forced_send))
        logger.error(e)
        return 'send fail'

    # TODO: use time instead of email count to constrain user.
    result = {
        "is_sent": is_sent,
        "rest_wait_time": rest_wait_time,
        "voted": voting_user.voted,
        "error_message": error_message
    }
    return jsonify(**result)


@app.route("/vote/<token>/", methods=['GET'])
def get_vote_page(token):
    """ Display vote page from url in email

    <token>: unique token stored in UserProfile
    """
    user = _get_user_from_token(token)
    if user is None:
        abort(404)

    if user.voted:
        websafe_election_key = user.election_key.urlsafe()
        return already_voted(websafe_election_key)
    else:
        election = user.election_key.get()
        election_dict = election.deep_serialize()
        return render_template('vote.html',
                               election=election_dict,
                               token=token)  # pass token for angular


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
    return "success"


@app.route("/results/<websafe_election_key>/", methods=['GET'])
def see_results(websafe_election_key):
    election = ndb.Key(urlsafe=websafe_election_key).get()
    election_dict = election.deep_serialize()
    return render_template('results.html', election=election_dict)


@app.route("/mail_sent/", methods=['GET'])
def mail_sent():
    message = u"信件已寄出"
    url = {
        'title': u'前往台大信箱',
        'href': 'https://wmail1.cc.ntu.edu.tw/imp/login.php'
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


@app.route("/error/", methods=['GET'])
def error_page():
    message = u"發生錯誤，請稍後再試或聯絡工作人員"
    return render_template('message.html', message=message)


@app.errorhandler(404)
def page_not_found(error):
    logger.error('404 not found: %s', request)
    msg = 'voting: 404 not found %s' % request
    return msg


if __name__ == "__main__":
    app.run()
