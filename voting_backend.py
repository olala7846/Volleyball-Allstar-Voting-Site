#!/user/bin/env python

"""
voting_backend.py -- backgend (apiserver + tasks) for voting app

create by olala7846@gmail.com

"""

import logging
import dateutil.parser
import wrapt
from datetime import datetime

import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote

from google.appengine.ext import ndb
from models import Election, Position, Candidate
from models import ElectionForm, WebsafekeyForm
from settings import ELECTION_DATA, POSITION_DATA

logger = logging.getLogger(__name__)

ADMIN_EMAILS = ["olala7846@gmail.com", "ins.huang@gmail.com"]


class SimpleMessage(messages.Message):
    """ Simple protorpc message """
    msg = messages.StringField(1, required=True)


# -------- Utilites --------
def _is_admin(user):
    if user is None:
        return False
    user_email = user.email()
    return user_email in ADMIN_EMAILS


@wrapt.decorator
def admin_only(wrapped, instance, args, kwargs):
    current_user = endpoints.get_current_user()
    if not _is_admin(current_user):
        raise endpoints.UnauthorizedException('This API is admin only')
    return wrapped(*args, **kwargs)


def remove_timezone(timestamp):
    """ Remove timezone completly
    see http://stackoverflow.com/questions/12763938/
    """
    # date not tested
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
    # TODO(olala): require authentication
    data = request_to_dict(request)
    election = Election(**data)
    election.put()

    return election


def _create_position(request):
    # get and remove ancestor key
    websafe_election_key = getattr(request, 'election_key')
    election_key = ndb.Key(Election, websafe_election_key)
    data = request_to_dict(request)
    del data['election_key']
    logger.error('populate with data %s', data)

    # allocate position_id and position
    position_id = ndb.Model.allocate_ids(size=1, parent=election_key)[0]
    position_key = ndb.Key(Position, position_id, parent=election_key)
    position = Position(key=position_key)
    position.populate(**data)
    position.put()
    return position


def _factory_election_data(websafe_election_key):
    """ Factory database with data from settings.py """
    # create or update election
    election = None
    if websafe_election_key is not None:
        election_key = ndb.Key(urlsafe=websafe_election_key)
        election = election_key.get()
    else:
        election = Election()
    election.populate(**ELECTION_DATA)
    election_key = election.put()

    for pos_data in POSITION_DATA:
        data_dictionaries = pos_data['data']
        del pos_data['data']

        position_name = pos_data['name']
        position = Position.query(ancestor=election_key).\
            filter(Position.name == position_name).get()
        if position is None:
            position_id = ndb.Model.allocate_ids(
                    size=1, parent=election_key)[0]
            position_key = ndb.Key(Position, position_id, parent=election_key)
            position = Position(key=position_key)
        position.populate(**pos_data)
        position.put()

        # remove all roles under position
        candidate_keys = position.candidate_keys
        candidates = ndb.get_multi(candidate_keys)
        ndb.delete_multi(candidates)

        # create all roles from data
        candidates = []
        for index, data_dict in enumerate(data_dictionaries):
            candidate_id = ndb.Model.allocate_ids(
                    size=1, parent=election_key)[0]
            candidate_key = ndb.Key(Candidate, candidate_id,
                                    parent=election_key)
            candidate = Candidate(key=candidate_key)
            data_dict['voting_index'] = index
            candidate.populate(**data_dict)
            candidates.append(candidate)
        position.candidate_keys = ndb.put_multi(candidates)
        position.put()

    return "update all data successfully"


def _update_unended_elections():
    """ iterate unfinished elections and update its status """
    qry = Election.query(Election.finished == False)
    election_iterator = qry.iter()
    now = datetime.now()
    cnt = 0
    for elect in election_iterator:
        if elect.end_date < now:
            elect.finished = True
            elect.put()
            cnt = cnt + 1
    return cnt


# -------- API --------
@endpoints.api(name='voting', version='v1',
               description='2016 allstar voting api')
class VotingApi(remote.Service):
    """ allstar voting api """

    @endpoints.method(ElectionForm, ElectionForm, path='create_election',
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
        """ Factory reset voting with data
        Should create Election, Role, and import Candidate data

        Though accecting ElectionForm, only websafe_key is required
        """
        # get websafe_election_key if in request
        if not request.websafe_key:
            raise endpoints.BadRequestException("require electino key")
        result = _factory_election_data(None)
        return SimpleMessage(msg=result)

    @endpoints.method(message_types.VoidMessage, SimpleMessage,
                      path='update_election_status', http_method='GET',
                      name='updateElectionStatus')
    def update_election_status(self, request):
        """ Updates the election.finished status """
        cnt = _update_unended_elections()
        msg = '%d elections finished' % cnt
        return SimpleMessage(msg=msg)


api = endpoints.api_server([VotingApi])  # register API
