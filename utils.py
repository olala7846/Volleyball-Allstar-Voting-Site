# -*- coding: utf-8 -*-
# utils.py

from datetime import datetime
from google.appengine.ext import ndb
from models import VotingUser, Election
from google.appengine.api.taskqueue import Queue, Task
import uuid


@ndb.transactional(retries=3)
def get_or_create_voting_user(websafe_election_key, student_id):
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


def get_user_from_token(token):
    """ Returns corresponding VotingUser """
    user = VotingUser.query(VotingUser.token == token).get()
    return user


@ndb.transactional(xg=True, retries=3)
def do_vote(user_key, candidate_keys):
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
    user.vote_time = datetime.now()
    user.put()


def send_voting_email(voting_user):
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

