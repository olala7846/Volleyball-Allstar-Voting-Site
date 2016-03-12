// register page controller
angular.module('registerApp', [])
  .controller('RegisterFormController', ['$scope', '$http', '$window',
    function($scope, $http, $window) {
      $scope.studentId = '';
      $scope.electionKey = $window.election_key;
      $scope.valid = false;
      $scope.inputGroupClass = 'has-warning';
      $scope.validate = function() {
        var studentId = $scope.studentId;
        var validPattern = new RegExp('[a-zA-z][0-9]{8}$');
        var match = studentId.match(validPattern);
        $scope.valid = false;
        $scope.inputGroupClass = 'has-danger';
        if(match != null && match[0] == studentId) {
          $scope.valid = true;
          $scope.inputGroupClass = 'has-success';
        } else if ($scope.studentId === '') {
          $scope.inputGroupClass = 'has-warning';
        }

      };

      $scope.requestEmail = function(){
        var apiPath = '/api/send_voting_email';
        var param = {
          student_id: $scope.studentId,
          election_key: $scope.electionKey
        };
        $http.post(apiPath, param).then(function(){
          window.location.href = '/mail_sent/';
        }, function(){
          window.location.href = '/sent_fail/';
        });
      };

    }]);
