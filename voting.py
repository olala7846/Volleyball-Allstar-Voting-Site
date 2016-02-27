# -*- coding: utf-8 -*-
# voting app

from flask import Flask, render_template, request, jsonify
from google.appengine.api import mail
from models import VotingUser, Election
import uuid
import math
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['DEBUG'] = True  # turn to false on production


@app.route("/")
@app.route("/voting/")
def welcome():
    elections = [e.to_dict() for e in Election.unfinished_elections()]
    content = {'elections': elections}
    logger.error('unfinished elections: %s', elections)
    return render_template('welcome.html', content=content)


@app.route("/voting/<voting_id>")
def voting_index(voting_id):
    return 'voting id : %s' % voting_id


def _send_voting_email(voting_user):
    """ Create voting user and send voting email with token to user
    Input:
        voting_user: VotingUser, the user to be sent.
    Output:
        is_sent: bool, an email is sent successfully.
    """
    # Send email by gmail api
    voting_link = "http://ntuvb-allstar.appspot.com/voting/"\
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
    lowercase_student_id = request.form.get('student_id').lower()
    forced_send = True if request.form.get('forced_send') == 'true' else False
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


@app.errorhandler(404)
def page_not_found(error):
    logger.error('404 not found %s', request)
    msg = 'voting: 404 not found %s' % request
    return msg

if __name__ == "__main__":
    app.run()
