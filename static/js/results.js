/* global _ */
// results.js
(function(angular){
  console.log('loading results.js');
  var app = angular.module('resultsApp', []);
  app.controller('ElectionResultsController', ['$scope', '$window', function($scope, $window){
    $scope.init = function(){
      $scope.election = $window.election;
      console.log('init controller');
    };
  }]);

}(angular));
