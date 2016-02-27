// register page controller
angular.module('registerApp', [])
  .controller('RegisterFormController', ['$scope', function($scope) {
    $scope.ntuldap = '';
    $scope.valid = false;
    $scope.inputGroupClass = 'has-warning';
    $scope.validate = function() {
      var ldap = $scope.ntuldap;
      var validPattern = new RegExp('[a-zA-z][0-9]{8}$');
      var match = ldap.match(validPattern);
      $scope.valid = false;
      $scope.inputGroupClass = 'has-danger';
      if(match != null && match[0] == ldap) {
        $scope.valid = true;
        $scope.inputGroupClass = 'has-success';
      } else if ($scope.ntuldap === '') {
        $scope.inputGroupClass = 'has-warning';
      }

    };


  }]);
