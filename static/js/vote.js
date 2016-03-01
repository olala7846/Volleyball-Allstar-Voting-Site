/* global _ */
// vote.js
angular.module('voteApp', [])
  .controller('VoteController', ['$scope', '$window', function($scope, $window){
    $scope.election = $window.data;
    var positions = $scope.election.positions;

    $scope.validateVotes = function(){
      for(var i in positions){
        var position = positions[i];
        var votesPerPerson = position.votes_per_person;
        var candidates = position.candidates;
        var results = _.countBy(candidates, function(candidate){
          return candidate.selected? 'selected':'notSelected';
        });
        position.voted = results.selected || 0;
        position.valid = position.voted <= votesPerPerson;
      }
    };

    function updateCandidate(candidate){
      if(!candidate.selected){
        candidate.selected = false;
      }
      candidate.btnTitle = candidate.selected? '收回選票':'投他一票';
    }

    $scope.toggleCandidate = function(candidate) {
      if(!candidate.selected){
        candidate.selected = true;
      } else {
        candidate.selected = false;
      }
      updateCandidate(candidate);
      $scope.validateVotes();
    };

    $scope.candidateClass = function(candidate){
      var candidatePosition = _.find($scope.election.positions, function(position){
        return _.indexOf(position.candidates, candidate) != -1;
      });
      if(candidatePosition.valid) {
        if(candidate.selected){
          return 'card-inverse card-success';
        } else {
          return '';
        }
      } else {
        return 'card-inverse card-danger';
      }
    };

    function initCandidates(){
      for(var i in positions){
        var candidates = positions[i].candidates;
        for(var j in candidates){
          updateCandidate(candidates[j]);
        }
      }
    }

    initCandidates();
    $scope.validateVotes();  // initial validation

  }]);
