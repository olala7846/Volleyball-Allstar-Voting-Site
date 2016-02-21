#!/user/bin/env python

"""
voting_backend.py -- backgend (apiserver + tasks) for voting app

create by olala7846@gmail.com

"""
import endpoints
from protorpc import message
from protorpc import remote

from google.appengine.ext import ndb
from models import Election, Candidate, Voter


# -------- Messages --------

class CreateElectionRequest(message.Message):


# -------- API --------

@endpoints.api(
    name='voting_api', version='v1', description='2016 allstar voting api')
class AllstarVotingApi(remote.Service):
    """ allstar api """

    @endpoints.method(

    def createElection(self, request):
        """ Creates new election """



api = endpoints.api_server([AllstarVotingApi])  # register API
