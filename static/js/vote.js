/* global _ */
// vote.js
(function(angular){
  var app = angular.module('voteApp', []);
  app.controller('VoteController', ['$scope', '$window', function($scope, $window){
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
  app.directive('voteCard', function(){
    return {
      restrict: 'E',
      templateUrl: '/tpl/votecard.html',
      scope: {
        candidate: '=',
        full: '=', // no more votes
        positionName: '<',
      },
      controller: ['$scope', function($scope){
        $scope.candidate.selected = false;
        $scope.$watch('candidate.selected', function(selected){
          if(selected){
            $scope.btnTitle = '收回選票';
          } else {
            $scope.btnTitle = '投他一票';
          }
          console.log($scope.full);

        });
        $scope.cardClass = function(){
          if($scope.candidate.selected){
            return 'card-inverse card-success';
          }
          return '';
        };
        $scope.btnClass = function(){
          if($scope.candidate.selected){
            return 'btn btn-danger';
          }
          return 'btn btn-primary';
        };
        $scope.canToggle = function(){
          return $scope.candidate.selected || !$scope.full;
        };
        $scope.toggleCandidate = function(){
          $scope.candidate.selected = !$scope.candidate.selected;
        };

      }]
    };
  });
  app.directive('positionCards', function(){
    return {
      restrict: 'E',
      templateUrl: '/tpl/positioncards.html',
      scope: {
        position: '='
      },
      controller: ['$scope', function($scope){
        $scope.full = false;
        $scope.$watch('position.candidates', function(candidates){
          var totalVotes = _.reduce(candidates, function(voted, candidate){
            return voted + (candidate.selected? 1:0);
          }, 0);
          $scope.full = (totalVotes >= $scope.position.votes_per_person);

        }, true);  // watch deep
      }]
    };
  });
}(angular));
