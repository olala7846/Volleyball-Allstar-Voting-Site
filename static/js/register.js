// register page controller
angular.module('registerApp', [])
  .controller('RegisterFormController', ['$scope', '$window',
    function($scope, $window) {
      $scope.studentId = '';
      $scope.websafe_election_key = $window.election_key;
      $scope.valid = false;
      $scope.inputGroupClass = 'has-warning';

      $scope.validate = function() {
        var studentId = $scope.studentId;
        var validPattern = new RegExp('[a-zA-Z][0-9]{2}[a-zA-Z0-9][0-9]{5}$');
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

    }]);
