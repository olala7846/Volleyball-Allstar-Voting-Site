// register page controller
angular.module('registerApp', [])
  .controller('RegisterFormController', ['$scope', '$http', '$window',
    function($scope, $http, $window) {
      $scope.schoolId = '';
      $scope.electionKey = $window.election_key;
      $scope.valid = false;
      $scope.inputGroupClass = 'has-warning';
      $scope.validate = function() {
        var schoolId = $scope.schoolId;
        var validPattern = new RegExp('[a-zA-z][0-9]{8}$');
        var match = schoolId.match(validPattern);
        $scope.valid = false;
        $scope.inputGroupClass = 'has-danger';
        if(match != null && match[0] == schoolId) {
          $scope.valid = true;
          $scope.inputGroupClass = 'has-success';
        } else if ($scope.schoolId === '') {
          $scope.inputGroupClass = 'has-warning';
        }

      };

      $scope.requestEmail = function(){
        var apiPath = '/api/send_voting_email';
        var param = {
          student_id: $scope.schoolId,
          election_key: $scope.electionKey
        };
        $http.post(apiPath, param).then(function(response){
          console.log(response);
        }, function(err){
          console.log(err);
        });
      };

    }]);
