#!/user/bin/env python

"""
voting_backend.py -- backgend (apiserver + tasks) for voting app

create by olala7846@gmail.com
"""

import logging
import dateutil.parser
import wrapt
import json
from datetime import datetime

import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote

from google.appengine.ext import ndb
from google.appengine.api import oauth
from models import Election, Position, Candidate, VotingUser
from models import ElectionForm, WebsafekeyForm
from settings import ELECTION_DATA, POSITION_DATA

DEBUG = True
logger = logging.getLogger(__name__)


class SimpleMessage(messages.Message):
    """ Simple protorpc message """
    msg = messages.StringField(1, required=True)


# -------- Utilites --------
@wrapt.decorator
def admin_only(wrapped, instance, args, kwargs):
    endpoint_user = endpoints.get_current_user()
    if endpoint_user is None:
        raise endpoints.UnauthorizedException('This API is admin only')

    scope = 'https://www.googleapis.com/auth/userinfo.email'
    is_admin = oauth.is_current_user_admin(scope)
    # only execute when user is admin or running local server
    if DEBUG or is_admin:
        return wrapped(*args, **kwargs)
    else:
        raise endpoints.UnauthorizedException('This API is admin only')


def remove_timezone(timestamp):
    """ Remove timezone completly
    see http://stackoverflow.com/questions/12763938/
    """
    # date not tested
    if timestamp.tzinfo:
        timestamp = timestamp.replace(tzinfo=None) - timestamp.utcoffset()

    return timestamp


def request_to_dict(request):
    """ parse request (protorpc message) into dictionary

    xxx_date will be parsed to datetime as ISO format
    """
    # copy data from request
    data = {}
    for field in request.all_fields():
        val = getattr(request, field.name)
        if field.name.endswith('_date'):
            try:
                date_val = dateutil.parser.parse(val)
                val = remove_timezone(date_val)
            except (ValueError, OverflowError):
                pass
            else:
                data[field.name] = val
        else:
            data[field.name] = val

    del data['websafe_key']
    return data


def _create_election(request):
    data = request_to_dict(request)
    election = Election(**data)
    election.put()

    return election


def _factory_election_data(websafe_election_key):
    """ Factory database with data from settings.py """
    # create or update election
    if websafe_election_key is not None:
        election_key = ndb.Key(urlsafe=websafe_election_key)
        election = election_key.get()
    else:
        election = Election()
    election.populate(**ELECTION_DATA)
    election_key = election.put()

    for pos_data_orig in POSITION_DATA:
        # avoid directly delete on setting objects
        pos_data = pos_data_orig.copy()
        position_data = pos_data['data']
        del pos_data['data']

        position_name = pos_data['name']
        position = Position.query(ancestor=election_key).\
            filter(Position.name == position_name).get()
        if position is None:
            logger.debug('creating new position entity')
            position_id = ndb.Model.allocate_ids(
                    size=1, parent=election_key)[0]
            position_key = ndb.Key(Position, position_id, parent=election_key)
            position = Position(key=position_key)

        position.populate(**pos_data)
        position_key = position.put()

        # remove all roles under position
        ndb.delete_multi(position.candidate_keys)

        # create all roles from data
        candidates = []
        for index, data_dict in enumerate(position_data):
            candidate_id = ndb.Model.allocate_ids(
                    size=1, parent=position_key)[0]
            candidate_key = ndb.Key(
                    Candidate, candidate_id, parent=position_key)
            candidate = Candidate(key=candidate_key)
            data_dict['voting_index'] = index
            candidate.populate(**data_dict)
            candidates.append(candidate)
        position.candidate_keys = ndb.put_multi(candidates)
        position.put()

    return "update all data successfully"


def _update_election_status():
    """ iterate all elections and update can_vote status

    return: number of votes running
    """
    qry = Election.query()
    election_iterator = qry.iter()
    cnt = 0
    for election in election_iterator:
        now = datetime.utcnow()
        if election.start_date <= now and now <= election.end_date:
            election.can_see_results = True
            election.can_vote = True
            cnt = cnt + 1
        else:
            election.can_vote = False
        election.put()
    return cnt


def _clean_id(student_id):
    clean_id = student_id.replace(" ", "")
    return clean_id


def _election_health_check(websafe_election_key):
    """ Checks election vote integrity """
    election_key = ndb.Key(urlsafe=websafe_election_key)
    election = election_key.get()
    if not election:
        return "no such election %s" % websafe_election_key

    all_user_query = VotingUser.query(ancestor=election_key)

    # aggregate votes
    dirty = []
    results = {}
    for user in all_user_query.iter():
        student_id = user.student_id
        clean_student_id = _clean_id(student_id)
        if student_id != clean_student_id:
            dirty.append(student_id)
            continue

        for vote_key in user.votes:
            try:
                results[vote_key] += 1
            except KeyError:
                results[vote_key] = 1

    # save results as readable json string
    readable_results = {}
    for candidate_key, count in results.iteritems():
        candidate = candidate_key.get()
        readable_results[candidate.name] = {'calc_cnt': count}

    # get vote count in database
    candidate_query = Candidate.query(ancestor=election_key)
    for candidate in candidate_query.iter():
        name = candidate.name
        count = candidate.num_votes
        try:
            readable_results[name]['db_cnt'] = count
        except KeyError:
            readable_results[name] = {'db_cnt': count, 'calc_cnt': 0}

    diff_data = {}
    for name, data in readable_results.iteritems():
        if data['calc_cnt'] != data['db_cnt']:
            diff_data[name] = data['db_cnt'] - data['calc_cnt']

    message = {
        'raw_data': readable_results,
        'diff_data': diff_data,
        'dirty': dirty
    }
    json_str = json.dumps(message)
    return json_str


# -------- API --------
@endpoints.api(
    name='voting', version='v1', description='2016 allstar voting api')
class VotingApi(remote.Service):
    """ allstar voting api """

    @endpoints.method(
        ElectionForm, ElectionForm, path='create_election',
        http_method='POST', name='createElection')
    @admin_only
    def create_election(self, request):
        """ Creates new Election
        start_date, end_date should be ISO format
        """
        websafekey = _create_election(request)
        logger.info("Created Election %s", websafekey)
        return request

    @endpoints.method(WebsafekeyForm, SimpleMessage,
                      path='setup_election', http_method='GET',
                      name='setupElection')
    @admin_only
    def setup_election(self, request):
        """ Populates election data
        Should create Election first, and privde election data
        """
        # get websafe_election_key if in request
        if not request.websafe_key:
            raise endpoints.BadRequestException("require election key")
        result = _factory_election_data(request.websafe_key)
        return SimpleMessage(msg=result)

    @endpoints.method(message_types.VoidMessage, SimpleMessage,
                      path='update_election_status', http_method='GET',
                      name='updateElectionStatus')
    @admin_only
    def update_election_status(self, request):
        """ Updates the election.running status """
        running_cnt = _update_election_status()
        msg = '%d elections running, now: %s' % (running_cnt, datetime.now())
        return SimpleMessage(msg=msg)

    @endpoints.method(WebsafekeyForm, SimpleMessage,
                      path='health_check', http_method='GET',
                      name='healthCheck')
    def health_check(self, request):
        """ Checks votes integrity """
        if not request.websafe_key:
            raise endpoints.BadRequestException("require election_key")
        msg = _election_health_check(request.websafe_key)
        return SimpleMessage(msg=msg)


api = endpoints.api_server([VotingApi])  # register API
