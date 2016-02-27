var sendEmailDialog = (function() {
    var ret = {};
    var init = function(data) {
        $(".want-vote").click(show_email_modal);
    }
    var show_email_modal = function(e) {
        // Show the send-email modal.

        // When click send button, send the email.
        send_email("yaya", false);
    }
    var send_email = function(student_id, forced_send) {
        $.ajax({
            url: '/api/send_voting_email',
            type: 'POST',
            dataType: 'json',
            data: {"student_id": student_id, "forced_send": forced_send},
            success: function(data) {
                console.log(data);
            },
            error: function(data) {
                console.log(data);
            }
        });
    };
    ret.init = init;
    ret.show_email_modal = show_email_modal;
    ret.send_email = send_email;

    return ret;
})();
