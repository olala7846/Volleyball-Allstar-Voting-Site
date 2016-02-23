#!/user/bin/env python

"""
voting_backend.py -- backgend (apiserver + tasks) for voting app

create by olala7846@gmail.com

"""

import logging
import dateutil.parser
import wrapt

import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote

from google.appengine.ext import ndb
from models import Election, Position
from models import ElectionForm, PositionForm

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
    see http://stackoverflow.com/questions/12763938/why-doesnt-appengine-auto-convert-datetime-to-utc-when-calling-put
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

    del data['web_safe_key']
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


# -------- API --------
@endpoints.api(name='voting', version='v1',
               description='2016 allstar voting api')
class VotingApi(remote.Service):
    """ allstar voting api """

    @endpoints.method(ElectionForm, ElectionForm, path='create_election',
                      http_method='POST', name='createElection')
    def create_election(self, request):
        """ Creates new Election
        start_date, end_date should be ISO format
        """
        websafekey = _create_election(request)
        logger.info("Created Election %s", websafekey)
        return request

    @endpoints.method(PositionForm, PositionForm, path='create_position',
                      http_method='POST', name='createPosition')
    @admin_only
    def create_position(self, request):
        """ Creates new Position
        parent_key is the target Election datastore key
        start_date, end_date should be ISO format
        """
        websafekey = _create_position(request)
        logger.info("Created Position %s", websafekey)
        return request

    @endpoints.method(message_types.VoidMessage, SimpleMessage,
                      path='factory_reset', http_method='GET',
                      name='factoryReset')
    @admin_only
    def factory_reset(self, request):
        """ Factory reset voting with data
        Should create Election, Role, and import data
        """
        return SimpleMessage(msg="Not Implemented Yet")


api = endpoints.api_server([VotingApi])  # register API
