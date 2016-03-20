/* global _ */
// vote.js
(function(angular){
  var app = angular.module('voteApp', []);
  app.controller('VoteController',
    ['$scope', '$window', '$http', function($scope, $window, $http){
      $scope.init = function(){
        $scope.election = $window.userdata.election;
        $scope.token = $window.userdata.token;
      };

      function aggrecateVotes(){
        var allVotes = [];
        var positions = $scope.election.positions;
        for(var i in positions){
          var position = positions[i];
          var votesPerPerson = position.votes_per_person;
          var positionVotes = _.filter(position.candidates, function(candidate){
            return candidate.selected;
          });
          if(positionVotes.length > votesPerPerson){
            return undefined;  // :( invalid vote
          }
          allVotes = allVotes.concat(positionVotes);
        }
        return allVotes;
      }

      $scope.submitVotes = function(){
        var allVotes = aggrecateVotes();
        if(allVotes){
          // submit vote request
          var config = {timeout: 10000};
          var ids = _.map(allVotes, function(candidate){
            return candidate.id;
          });
          var param = {candidate_ids: ids};
          var apiPath = '/api/vote/' + $scope.token + '/';
          $http.post(apiPath, param, config).then(function(){
            window.location.href = '/results/'+$scope.election.websafe_key;
          }, function(err){
            console.log(err);
            window.location.href = '/error/';
          });
        }
      };
    }]);
  app.directive('voteCard', function(){
    return {
      restrict: 'E',
      templateUrl: '/tpl/votecard.html',
      scope: {
        candidate: '=',
        full: '<', // no more votes
        voteStatus: '<'
      },
      controller: ['$scope', function($scope){
        $scope.candidate.selected = false;
        $scope.$watch('candidate.selected', function(selected){
          if(selected){
            $scope.btnTitle = '收回選票';
          } else {
            $scope.btnTitle = '投他一票';
          }
        });
        $scope.cardClass = function(){
          if($scope.candidate.selected){
            return 'candidate-card-selected';
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
          var votesPerPerson = $scope.position.votes_per_person;
          var totalVotes = _.filter(candidates, function(candidate){
            return candidate.selected;
          });
          $scope.full = (totalVotes.length >= votesPerPerson);
          if($scope.full){
            $scope.voteStatus = $scope.position.title+'已投好投滿';
          }else{
            $scope.voteStatus = $scope.position.title+'已投'+totalVotes.length+'/'+votesPerPerson;
          }

        }, true);  // watch deep
      }]
    };
  });
}(angular));
