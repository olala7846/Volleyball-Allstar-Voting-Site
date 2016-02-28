# -*- coding: utf-8 -*-
# voting app

from flask import Flask, render_template, request, jsonify
from google.appengine.api import mail
from models import VotingUser
import uuid
import logging

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['DEBUG'] = True  # turn to false on production


@app.route("/")
@app.route("/voting/")
def welcome():
    votings = ['voting1', 'voting2']
    content = {'votings': votings}
    return render_template('welcome.html', content=content)


@app.route("/voting/<voting_id>")
def voting_index(voting_id):
    return 'voting id : %s' % voting_id


def _send_voting_email(voting_user):
    """ Create voting user and send voting email with token to user
    Input:
        voting_user: VotingUser, the userto be sent.
    Output:
        is_sent: bool, an email is sent successfully.
    """
    # TODO: use time instead of email count to constrain user.
    voting_user.email_count += 1
    key = voting_user.put()
    key.get()  # for strong consistency

    # Send email by gmail api
    voting_link = "http://ntuvb-allstar.appspot.com/voting/" + voting_user.token
    email_content = u"投票請進：" + voting_link
    base_mail_options = {"sender": "ins.huang@gmail.com",
                         "to": voting_user.student_id + "@ntu.edu.tw",
                         "subject": "2016台大排球明星賽投票認證信",
                         "body": email_content}

    mail.send_mail(**base_mail_options)

    logger.info("Email is sent to %s" % voting_user.student_id)
    return True


@app.route("/api/send_voting_email", methods=["POST"])
def send_voting_email():
    """ Create voting user and send voting email with token to user
    Input:
        student_id: string, student_id.
        forced_send: bool, send voting email anyway.
    Output:
        is_sent: bool, an email is sent in this request.
        sent_count: int, the count of emails sent for the student_id.
        voted: bool, whether the user is voted.
        error_message: str, be empty string if no error.
    """
    lowercase_student_id = request.form.get('student_id').lower()
    forced_send = True if request.form.get('forced_send') == 'true' else False
    is_sent = False
    error_message = ""

    try:
    # Get VotingUser with given lowercase_student_id
    voting_user = VotingUser.query(VotingUser.student_id == lowercase_student_id).get()

    if voting_user:
        # Only send voting email to existing user when forced_send is set
        # and less than 3 emails are sent for the user.
        if forced_send and voting_user.email_count < 3:
            is_sent = _send_voting_email(voting_user)
    else:
        # If VotingUser does not exist, create one and send email
        token = str(uuid.uuid4().hex)
        voting_user = VotingUser(student_id=lowercase_student_id, voted=False, token=token)
        key = voting_user.put()
        key.get()  # for strong consistency
        is_sent = _send_voting_email(voting_user)
    except Exception, e:
        logger.error("Error in send_voting_email")
        logger.error("student_id: %s, forced_send: %s" % (lowercase_student_id, forced_send))
        logger.error(e)
        error_message = "寄送認證信失敗，請聯絡工作人員。"

    # TODO: use time instead of email count to constrain user.
    result = {
        "is_sent": is_sent,
        "email_count": voting_user.email_count if voting_user else 0,
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
