#!/user/bin/env python

"""
GAE Datastore models
"""

from datetime import datetime
from google.appengine.ext import ndb


class Election(ndb.Model):
    """ Single Vote Event (e.g. 2016 Volleyball Allstar Game """
    name = ndb.StringProperty()
    description = ndb.StringProperty()
    start_date = ndb.DateTimeProperty()
    end_date = ndb.DateTimeProperty()
    positions = ndb.KeyProperty(repeat=True)


class Position(ndb.Model):
    """ Single Vote Event (e.g. 2016 Volleyball Allstar Game """
    name = ndb.StringProperty()
    description = ndb.StringProperty()
    votes_per_person = ndb.IntegerProperty()
    num_elected = ndb.IntegerProperty()


class Candidate(ndb.Model):
    """ Candidate in a single vote

    key: election_id.position_id.candidate_id as key
    """
    voting_index = ndb.IntegerProperty()
    name = ndb.StringProperty()
    description = ndb.TextProperty()
    avatar = ndb.StringProperty()
    num_votes = ndb.IntegerProperty()


class Vote(ndb.Model):
    """ People who vote and who they vote """
    positoin = ndb.KeyProperty(kind=Position)
    candidates = ndb.KeyProperty(kind=Candidate, repeat=True)


class VotingUser(ndb.Model):
    """ election_id.student_id """
    student_id = ndb.StringProperty()
    voted = ndb.BooleanProperty()
    token = ndb.StringProperty()
    votes = ndb.KeyProperty(kind=Vote, repeate=True)


# Utility

def generate_election(description=None, start_time=None, end_time=None):
    election = Election(description=description,
                        start_time=start_time,
                        end_time=end_time,
                        create_time=datetime.now())
    election.put()
    return election


# sample transaction for later use
@ndb.transactional
def insert_if_absent(note_key, note):
    fetch = note_key.get()
    if fetch is None:
        note.put()
        return True
    return False
