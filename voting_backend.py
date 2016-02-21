#!/user/bin/env python

"""
voting_backend.py -- backgend (apiserver + tasks) for voting app

create by olala7846@gmail.com

"""
import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote

from google.appengine.ext import ndb
from models import Election

package = 'Hello'


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


# -------- API --------
@endpoints.api(name='voting_api', version='v1',
               description='2016 allstar voting api')
class VotingApi(remote.Service):
    """ allstar api """

    @endpoints.method(message_types.VoidMessage, GreetingCollection,
                      path='create_election', http_method='GET',
                      name='voting.create_election')
    def createElection(self, request):
        """ Creates new election """
        election = Election()
        election.put()
        return STORED_GREETINGS


api = endpoints.api_server([VotingApi])  # register API
