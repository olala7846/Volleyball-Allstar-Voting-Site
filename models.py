#!/user/bin/env python

"""
GAE Datastore models
"""

from datetime import datetime
from protorpc import messages
from protorpc import message_types
from google.appengine.ext import ndb


class Election(ndb.Model):
    """ Single Vote Event (e.g. 2016 Volleyball Allstar Game """
    name = ndb.StringProperty()
    description = ndb.StringProperty()
    start_date = ndb.DateTimeProperty()
    end_date = ndb.DateTimeProperty()
    positions = ndb.KeyProperty(repeated=True)


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
    candidates = ndb.KeyProperty(kind=Candidate, repeated=True)


class VotingUser(ndb.Model):
    """ election_id.student_id """
    student_id = ndb.StringProperty()
    voted = ndb.BooleanProperty()
    token = ndb.StringProperty()
    votes = ndb.KeyProperty(kind=Vote, repeated=True)


# API protorpc Messages
class ElectionForm(messages.Message):
    """ message to create/update Election model """
    name = messages.StringField(1)
    description = messages.StringField(2)
    start_date = messages.StringField(3, required=True)
    end_date = messages.StringField(4, required=True)
    web_safe_key = messages.StringField(5)


class PositionForm(messages.Message):
    """ message to create/update Position model """
    name = messages.StringField(1)
    description = messages.StringField(2)
    votes_per_person = messages.IntegerField(3)
    num_elected = messages.IntegerField(4)
    election_key = messages.StringField(5)
    web_safe_key = messages.StringField(6)
