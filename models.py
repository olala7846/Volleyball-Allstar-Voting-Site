#!/user/bin/env python

"""
GAE Datastore models
"""

from datetime import datetime
from protorpc import messages
from google.appengine.ext import ndb


class Election(ndb.Model):
    """ Single Vote Event (e.g. 2016 Volleyball Allstar Game

    name is used for db query,
    for human readable name plse use title and description
    """
    description = ndb.StringProperty()
    end_date = ndb.DateTimeProperty()
    name = ndb.StringProperty()
    start_date = ndb.DateTimeProperty()
    started = ndb.BooleanProperty(default=True)
    title = ndb.StringProperty()

    @classmethod
    def unfinished_elections(cls):
        """ get first first 20 unfinished elections """
        now = datetime.now()
        qry = Election.query(cls.end_date > now)
        elections = qry.order(-cls.end_date).fetch(20)
        return elections

    def serialize(self):
        """ convert Election object to python dictionary """
        data = {
            'description': self.description,
            'end_date': self.end_date.isoformat(),
            'start_date': self.start_date.isoformat(),
            'title': self.title,
            'websafe_key': self.key.urlsafe(),
        }
        return data

    @property
    def positions(self):
        """ Returns Positions under the same entity group """
        positions = Position.query(ancestor=self.key).fetch()
        return positions

    # TODO(Olala): need to cache this method call
    def deep_serialize(self):
        """ Get the nested voting """
        data = self.serialize()
        position_dict_list = [p.deep_serialize() for p in self.positions]
        data['positions'] = position_dict_list
        return data


class Position(ndb.Model):
    """ Single Vote Event (e.g. 2016 Volleyball Allstar Game

    name is used for db query,
    for human readable name please use title and description
    """
    candidate_keys = ndb.KeyProperty(repeated=True)
    description = ndb.StringProperty()
    name = ndb.StringProperty()
    num_elected = ndb.IntegerProperty()
    title = ndb.StringProperty()
    votes_per_person = ndb.IntegerProperty()

    @property
    def candidates(self):
        candidates = ndb.get_multi(self.candidate_keys)
        return sorted(candidates, key=lambda x: x.voting_index)

    def serialize(self):
        """ convert Position object to python dictionary """
        data = {
            'description': self.description,
            'num_elected': self.num_elected,
            'title': self.title,
            'votes_per_person': self.votes_per_person,
        }
        return data

    def deep_serialize(self):
        data = self.serialize()
        data['candidates'] = [c.serialize() for c in self.candidates]
        return data


class Candidate(ndb.Model):
    """ Candidate in a single vote

    key: election_id.position_id.candidate_id as key
    """
    avatar = ndb.StringProperty()
    department = ndb.StringProperty()
    description = ndb.TextProperty()
    name = ndb.StringProperty()
    num_votes = ndb.IntegerProperty(default=0)
    voting_index = ndb.IntegerProperty()

    def serialize(self):
        """ convert Position object to python dictionary """
        data = {
            'id': self.key.urlsafe(),
            'avatar': self.avatar,
            'department': self.department,
            'description': self.description,
            'name': self.name,
            'num_votes': self.num_votes,
            'voting_index': self.voting_index,
        }
        return data


class VotingUser(ndb.Model):
    """ Representing a single user in a election
        election_key: target election ndb key
        token: generated uuid for user
        votes: selected candidate keyes
    """
    election_key = ndb.KeyProperty(kind=Election, required=True)
    student_id = ndb.StringProperty()
    voted = ndb.BooleanProperty(default=False)
    token = ndb.StringProperty()
    votes = ndb.KeyProperty(kind=Candidate, repeated=True)
    email_count = ndb.IntegerProperty(default=0)
    create_time = ndb.DateTimeProperty(auto_now_add=True)
    vote_time = ndb.DateTimeProperty()


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
