// register page controller
angular.module('registerApp', [])
  .controller('RegisterFormController', ['$scope', '$http',
    function($scope, $http) {
      $scope.schoolId = '';
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
          student_id: $scope.schoolId
        };
        $http.post(apiPath, param).then(function(response){
          console.log(response);
        }, function(err){
          console.log(err);
        });
      };

    }]);
