# -*- coding: utf-8 -*-
# voting app

from flask import Flask, render_template, request, jsonify, abort
from google.appengine.api import mail
from google.appengine.ext import ndb
from models import VotingUser, Election

from datetime import datetime
from itertools import groupby
import uuid
import math
import logging

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['DEBUG'] = True  # turn to false on production


# -------- utils --------
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


@app.template_filter('aj')
def angular_js_filter(s):
    """ example: {{'angular expressioins'|aj}} """
    return '{{'+s+'}}'


def _send_voting_email(voting_user):
    """ Create voting user and send voting email with token to user
    Input:
        voting_user: VotingUser, the user to be sent.
    Output:
        is_sent: bool, an email is sent successfully.
    """
    # Send email by gmail api
    voting_link = "http://ntuvb-allstar.appspot.com/vote/"\
                  + voting_user.token
    email_content = u"投票請進：" + voting_link
    base_mail_options = {"sender": "ins.huang@gmail.com",
                         "to": voting_user.student_id + "@ntu.edu.tw",
                         "subject": "2016台大排球明星賽投票認證信",
                         "body": email_content}

    mail.send_mail(**base_mail_options)

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


@app.route("/register/<websafe_key>/", methods=['GET'])
def voting_index(websafe_key):
    election_key = ndb.Key(urlsafe=websafe_key)
    election = election_key.get()
    if not election or not election.started:
        abort(404)
    election_data = election.serialize()
    content = {'election': election_data}
    return render_template('register.html', content=content)


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
    """
    post_data = _get_post_data(request)
    lowercase_student_id = post_data.get('student_id').lower()
    forced_send = True if post_data.get('forced_send') == 'true' else False
    election_key = post_data['election_key']
    is_sent = False
    error_message = ""
    rest_wait_time = 0

    try:
        # Get VotingUser with given lowercase_student_id
        voting_user = VotingUser.query(
                VotingUser.student_id == lowercase_student_id).get()

        if voting_user:
            # Only send voting email to existing user when forced_send is set
            # and less than 3 emails are sent for the user.
            rest_wait_time = _get_rest_wait_time(voting_user)
            if voting_user.email_count == 0 or (
                    forced_send and rest_wait_time == 0):
                is_sent = _send_voting_email(voting_user)
        else:
            # If VotingUser does not exist, create one and send email
            token = str(uuid.uuid4().hex)
            election_key_object = ndb.Key(urlsafe=election_key)
            voting_user = VotingUser(
                    election_key=election_key_object,
                    student_id=lowercase_student_id,
                    voted=False,
                    token=token)
            key = voting_user.put()
            key.get()  # for strong consistency
            is_sent = _send_voting_email(voting_user)
    except Exception, e:
        logger.error("Error in send_voting_email")
        logger.error("student_id: %s, forced_send: %s" % (
            lowercase_student_id, forced_send))
        logger.error(e)
        error_message = "寄送認證信失敗，請聯絡工作人員。"

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
    """ get vote page with url in email """
    user = _get_user_from_token(token)
    if user is None:
        abort(404)

    if user.voted:
        return render_template('alreadyvoted.html')
    else:
        election = user.election_key.get()
        election_dict = election.deep_serialize()
        return render_template('vote.html',
                               election=election_dict,
                               token=token)  # pass token for angular


@app.route("/api/vote/<token>/", methods=['POST'])
def vote_with_data(token):
    """ get vote page with url in email """
    user = _get_user_from_token(token)
    post_data = request.get_json()
    candidate_ids = post_data['candidate_ids']
    if user is None:
        return abort(500, {'message': 'stop this ...'})

    # check vote count valid
    candidate_keys = [ndb.Key(urlsafe=key) for key in candidate_ids]
    candidates = ndb.get_multi(candidate_keys)

    def _get_position_key(candidate):
        return candidate.key.parent()
    candidates = sorted(candidates, key=_get_position_key)
    for key, group in groupby(candidates, key=_get_position_key):
        position = key.get()
        if position.votes_per_person < len(list(group)):
            return abort(500, {'message': 'ilegal vote'})

    try:
        _do_vote(user.key, candidate_keys)
    except Exception, e:
        logger.error('Exception while _do_vote: %s', e)
        abort(500)
    return "success"


@ndb.transactional(xg=True, retries=3)
def _do_vote(user_key, candidate_keys):
    """ save vote to db after checked data """
    # check user not voted
    user = user_key.get()  # check latest value
    if user.voted:
        return False

    user.votes = candidate_keys
    user.voted = True
    user.put()

    candidates = ndb.get_multi(candidate_keys)
    for candidate in candidates:
        candidate.num_votes = candidate.num_votes + 1
    ndb.put_multi(candidates)

    return True


@app.errorhandler(404)
def page_not_found(error):
    logger.error('404 not found %s', request)
    msg = 'voting: 404 not found %s' % request
    return msg

if __name__ == "__main__":
    app.run()
