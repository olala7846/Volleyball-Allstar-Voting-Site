#!/user/bin/env python

"""
voting_backend.py -- backgend (apiserver + tasks) for voting app

create by olala7846@gmail.com

"""

import logging
import dateutil.parser

import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote

from google.appengine.ext import ndb
from models import Election
from models import ElectionForm

logger = logging.getLogger(__name__)


# -------- Messages --------
class Greeting(messages.Message):
    """Greeting that stores a message."""
    message = messages.StringField(1)


class GreetingCollection(messages.Message):
    """Collection of Greetings."""
    items = messages.MessageField(Greeting, 1, repeated=True)


STORED_GREETINGS = GreetingCollection(items=[
    Greeting(message='hello world!'),
    Greeting(message='goodbye world!'),
])


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


# sample transaction for later use
@ndb.transactional
def insert_if_absent(note_key, note):
    fetch = note_key.get()
    if fetch is None:
        note.put()
        return True
    return False


# -------- API --------
@endpoints.api(name='voting', version='v1',
               description='2016 allstar voting api')
class VotingApi(remote.Service):
    """ allstar voting api """

    @endpoints.method(message_types.VoidMessage, GreetingCollection,
                      path='greeting', http_method='GET',
                      name='greeting')
    def greeting(self, request):
        """ Sample gretting api """
        return STORED_GREETINGS

    @endpoints.method(ElectionForm, ElectionForm, path='create_election',
                      http_method='POST', name='createElection')
    def create_election(self, request):
        """ Creates new Election
        start_date, end_date should be ISO format
        """
        websafekey = _create_election(request)
        logger.info("Created Election %s", websafekey)
        return request


api = endpoints.api_server([VotingApi])  # register API
