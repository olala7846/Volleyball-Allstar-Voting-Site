// vote.js
angular.module('voteApp', [])
  .controller('VoteController', ['$scope', '$window', function($scope, $window){
    $scope.election = $window.data;

    $scope.validateVotes = function(){
      for(var i in $scope.election.positions){
        var position = $scope.election.positions[i];
        var votesPerPerson = position.votes_per_person;
        var numSelected = 0;
        for(var j in position.candidates){
          var candidate = position.candidates[j];
          if(candidate.selected){
            numSelected++;
          }
        }
        position.valid = numSelected <= votesPerPerson;
      }
    };

    $scope.toggleCandidate = function(candidate) {
      if(!candidate.selected){
        candidate.selected = true;
      } else {
        candidate.selected = false;
      }
      $scope.validateVotes();
    };

    $scope.validateVotes();  // initial validation

  }]);
