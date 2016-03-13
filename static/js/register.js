// register page controller
angular.module('registerApp', [])
  .controller('RegisterFormController', ['$scope', '$http', '$window',
    function($scope, $http, $window) {
      $scope.studentId = '';
      $scope.websafe_election_key = $window.election_key;
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
          election_key: $scope.websafe_election_key
        };
        var voted_url = '/voted/'+$scope.websafe_election_key+'/';
        var config = {timeout: 10000};
        $http.post(apiPath, param, config).then(function(response){
          if(response.data == 'send fail'){
            window.location.href = '/sent_failed/';
          }else if(response.data == 'already voted'){
            window.location.href = voted_url;
          }else {
            window.location.href = '/mail_sent/';
          }
        }, function(err){
          console.log('Err:', err);
          window.location.href = '/sent_failed/';
        });
      };

    }]);
