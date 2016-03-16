# -*- coding: utf-8 -*-
# voting app

from flask import Flask, render_template, request, jsonify, abort
from google.appengine.api import mail
from google.appengine.ext import ndb
from sendgrid import SendGridClient
from sendgrid import Mail
from models import VotingUser, Election
import secrets

from datetime import datetime
import uuid
import math
import logging

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['DEBUG'] = False  # turn to false on production

# make a secure connection to SendGrid
sg = SendGridClient(secrets.SENDGRID_ID, secrets.SENDGRID_PASSWORD, secure=True)


# -------- utils --------
def _get_data_from_token(ticked_id):
    """ Returns corresponding User and Election Object """
    logger.error('_is_valid_ticket Not Implemented Yet!!')
    election = Election.query().get()  # temp get any election
    return (VotingUser(), election)


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


@app.route("/register/<websafe_key>/", methods=['GET'])
def voting_index(websafe_key):
    election_key = ndb.Key(urlsafe=websafe_key)
    election = election_key.get()
    logger.error('Got election: %s', election)
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
    Output:
        is_sent: bool, an email is sent in this request.
        rest_wait_time: int, the rest wait time to send email in minute.
        voted: bool, whether the user is voted.
        error_message: str, be empty string if no error.
    """
    post_data = _get_post_data(request)
    lowercase_student_id = post_data.get('student_id').lower()
    forced_send = True if post_data.get('forced_send') == 'true' else False
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
            voting_user = VotingUser(
                    student_id=lowercase_student_id, voted=False, token=token)
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


@app.route("/vote/<token>/", methods=['GET', 'POST'])
def get_ticket(token):
    user, election = _get_data_from_token(token)
    if not user:
        abort(404)
    if request.method == 'GET':
        if user.voted:
            return render_template('alreadyvoted.html')
        else:
            election = election.deep_serialize()
            return render_template('vote.html', election=election,
                                   token=token)
    elif request.method == 'POST':
        logger.error('POST vote/<token>/ not implemented')
        return abort(500)


@app.errorhandler(404)
def page_not_found(error):
    logger.error('404 not found %s', request)
    msg = 'voting: 404 not found %s' % request
    return msg

if __name__ == "__main__":
    app.run()
