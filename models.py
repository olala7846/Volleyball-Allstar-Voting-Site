# -*- coding: utf-8 -*-
# GAE datastore model
from protorpc import messages
from google.appengine.ext import ndb
from google.appengine.api import memcache
from datetime import datetime, timedelta

import hashlib
import logging
logger = logging.getLogger(__name__)

EMAIL_SEND_INTERVAL_MIN = 10


class Election(ndb.Model):
    """ Single Vote Event (e.g. 2016 Volleyball Allstar Game
    name: simple english name for developer
    title: human readable name
    can_see_results: should never vote or display results
    can_vote: can vote
    """
    description = ndb.StringProperty()
    start_date = ndb.DateTimeProperty(auto_now_add=True)
    end_date = ndb.DateTimeProperty(auto_now_add=True)
    title = ndb.StringProperty()
    can_vote = ndb.BooleanProperty(default=True)
    can_see_results = ndb.BooleanProperty(default=True)

    @classmethod
    def available_elections(cls):
        """ returns elections either can vote or can display retults"""
        qry = Election.query(ndb.OR(
            Election.can_vote == True,
            Election.can_see_results == True))
        elections = qry.order(-cls.start_date).fetch(20)
        return elections

    def serialize(self):
        """ convert Election object to python dictionary """
        data = {
            'description': self.description,
            'end_date': self.end_date.isoformat(),
            'start_date': self.start_date.isoformat(),
            'title': self.title,
            'websafe_key': self.key.urlsafe(),
            'can_vote': self.can_vote,
            'can_see_results': self.can_see_results,
        }
        return data

    @property
    def positions(self):
        """Gets all Positions under the same entity group
        normally 5 positions (Setter, Outside, Left, Middle
        Right, Libero) under one election
        """
        positions = Position.query(ancestor=self.key).fetch()
        return positions

    def cached_deep_serialize(self):
        ELECTION_CACHE_KEY = self.key.urlsafe() + '_serialized'
        data = memcache.get(ELECTION_CACHE_KEY)
        if data is not None:
            return data
        else:
            data = self.deep_serialize()
            memcache.add(ELECTION_CACHE_KEY, data, 60)
            return data

    def deep_serialize(self):
        """ Get the nested voting """
        data = self.serialize()
        position_dict_list = [p.deep_serialize() for p in self.positions]
        data['positions'] = position_dict_list
        return data


# 排球站位(舉球,主攻,欄中,輔舉,自由...)
class Position(ndb.Model):
    """Represents a player specialization
    name: english name for developer
    title: readable chinese name for display
    """
    # reference to list of Candidates
    candidate_keys = ndb.KeyProperty(repeated=True)
    description = ndb.StringProperty()
    name = ndb.StringProperty()
    num_elected = ndb.IntegerProperty()
    title = ndb.StringProperty()
    votes_per_person = ndb.IntegerProperty()

    @property
    def candidates(self):
        """Returns all candidates running for this Position"""
        candidates = ndb.get_multi(self.candidate_keys)
        return sorted(candidates, key=lambda x: x.voting_index)

    def serialize(self):
        """ convert Position object to python dictionary """
        data = {
            'description': self.description,
            'num_elected': self.num_elected,
            'name': self.name,
            'title': self.title,
            'votes_per_person': self.votes_per_person,
        }
        return data

    def deep_serialize(self):
        """Also serialize foreign key entities"""
        data = self.serialize()
        data['candidates'] = [c.serialize() for c in self.candidates]
        return data


# 候選人
class Candidate(ndb.Model):
    """ Candidate in a single Election
    key: election_id.position_id.candidate_id as key
    """
    avatar = ndb.StringProperty()  # 照片id
    department = ndb.StringProperty()  # 系級
    description = ndb.TextProperty()  # 球員描述
    name = ndb.StringProperty()  # 姓名
    num_votes = ndb.IntegerProperty(default=0)  # 目前票數
    voting_index = ndb.IntegerProperty()  # 排序用index

    def serialize(self):
        """ convert Position object to python dictionary """
        data = {
            'id': self.key.urlsafe(),
            'avatar_url': self.avatar_url,
            'department': self.department,
            'description': self.description,
            'name': self.name,
            'num_votes': self.num_votes,
            'voting_index': self.voting_index,
        }
        return data

    @property
    def avatar_url(self):
        """ returns self.avatar if set or hash self.name as avatar """
        # TODO(Olala): name may conflict (between elections)
        # use other hash method
        if self.avatar:
            return self.avatar
        else:
            # hash self.name as image path
            unicode_name = self.name.encode('utf-8')
            hax_file_name = hashlib.md5(unicode_name).hexdigest()
            return '/img/candidates/%s.jpg' % hax_file_name


class VotingUser(ndb.Model):
    """ Representing a single user (normally a student,
    staff, professor ...) in a single Election. should be
    under the same entity group of Election. view
    utils.get_or_create_voting_user()

    election_key: target election voted on
    token: generated uuid for user
    votes: voted candidate keyes
    """
    student_id = ndb.StringProperty()
    voted = ndb.BooleanProperty(default=False)
    token = ndb.StringProperty()
    votes = ndb.KeyProperty(kind=Candidate, repeated=True)
    create_time = ndb.DateTimeProperty(auto_now_add=True)
    vote_time = ndb.DateTimeProperty()
    last_time_mail_queued = ndb.DateTimeProperty()

    @property
    def election_key(self):
        return self.key.parent()

    @property
    def mail_sent_recently(self):
        if not self.last_time_mail_queued:
            return False
        else:
            now = datetime.now()
            time_since_last_send = now - self.last_time_mail_queued
            min_resend_duration = timedelta(minutes=EMAIL_SEND_INTERVAL_MIN)
            return time_since_last_send < min_resend_duration


##### Google Cloud Endpoints #####
# API protorpc Messages
class ElectionForm(messages.Message):
    """ message to create/update Election model """
    title = messages.StringField(1)
    description = messages.StringField(2)
    start_date = messages.StringField(3, required=True)
    end_date = messages.StringField(4, required=True)
    websafe_key = messages.StringField(5)


class WebsafekeyForm(messages.Message):
    """ message containing only one key """
    websafe_key = messages.StringField(1)
