#!/user/bin/env python

"""
GAE Datastore models
"""

from datetime import datetime
from protorpc import messages
from protorpc import message_types
from google.appengine.ext import ndb


class Election(ndb.Model):
    """ Single Vote Event (e.g. 2016 Volleyball Allstar Game

    name is used for db query,
    for human readable name plse use title and description
    """
    name = ndb.StringProperty()
    title = ndb.StringProperty()
    description = ndb.StringProperty()
    start_date = ndb.DateTimeProperty()
    end_date = ndb.DateTimeProperty()
    started = ndb.BooleanProperty(default=True)

    @classmethod
    def unfinished_elections(cls):
        """ get first first 20 unfinished elections """
        now = datetime.now()
        qry = Election.query(cls.end_date > now)
        elections = qry.order(-cls.end_date).fetch(20)
        return elections

    def to_dict(self):
        data = {
            'title': self.title,
            'description': self.description,
            'websafe_key': self.key.urlsafe(),
        }
        return data

    # please cache this!!
    def full_election_data(self):
        """ Get the nested voting """
        positions = Position.query(ancestor=self.key).fetch()
        positions_dict = [pos.to_dict() for pos in positions]

        data = {
            'title': self.title,
            'description': self.description,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'positions': positions_dict,
        }
        return data


class Position(ndb.Model):
    """ Single Vote Event (e.g. 2016 Volleyball Allstar Game

    name is used for db query,
    for human readable name please use title and description
    """
    name = ndb.StringProperty()
    title = ndb.StringProperty()
    description = ndb.StringProperty()
    votes_per_person = ndb.IntegerProperty()
    num_elected = ndb.IntegerProperty()
    candidate_keys = ndb.KeyProperty(repeated=True)

    def to_dict(self):
        return {'pos': self.key}


class Candidate(ndb.Model):
    """ Candidate in a single vote

    key: election_id.position_id.candidate_id as key
    """
    voting_index = ndb.IntegerProperty()
    name = ndb.StringProperty()
    description = ndb.TextProperty()
    department = ndb.StringProperty()
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
    email_count = ndb.IntegerProperty(default=0)
    create_time = ndb.DateTimeProperty(auto_now_add=True)


# API protorpc Messages
class ElectionForm(messages.Message):
    """ message to create/update Election model """
    name = messages.StringField(1)
    description = messages.StringField(2)
    start_date = messages.StringField(3, required=True)
    end_date = messages.StringField(4, required=True)
    websafe_key = messages.StringField(5)


class WebsafekeyForm(messages.Message):
    """ message containing only one key """
    websafe_key = messages.StringField(1)
