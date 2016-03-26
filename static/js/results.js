/* global google, election */
/* results.js */

(function(angular){
  var app = angular.module('resultsApp', []);
  app.controller('ElectionResultsController', ['$scope', '$window', function($scope, $window){
    $scope.init = function(){
      $scope.election = $window.election;
    };
  }]);

}(angular));

google.charts.load('current', {packages: ['corechart']});
google.charts.setOnLoadCallback(drawChart);
function drawChart(){
  for(var i in election.positions){
    var position = election.positions[i];
    var element_id = position.name;
    var candidates = position.candidates;

    var chartData = [['Name', 'Votes']];
    for(var j in candidates){
      var candidate = candidates[j];
      chartData.push([candidate.name, candidate.num_votes]);
    }
    var data = google.visualization.arrayToDataTable(chartData);
    var view = new google.visualization.DataView(data);
    var chart = new google.visualization.BarChart(document.getElementById(element_id));
    var options = {
      title: '前'+ position.num_elected + '名候選人當選',
      height: candidates.length*38,
      bar: {groupWidth: '95%'},
      legend: { position: 'none'}
    };

    chart.draw(view, options);
  }
}
