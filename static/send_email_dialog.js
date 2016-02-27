var sendEmailDialog = (function() {
    var ret = {};
    var init = function(data) {
        $(".want-vote").click(show_email_modal);
        $("#modal-container .close_icon").click(hide_email_modal);
    };
    var show_email_modal = function(e) {
        // Show the send-email modal with student_id request.
        show_student_id_request_msg();
        $("#modal-container .modal").modal({ show: true, backdrop: "static" });

    };
    var hide_email_modal = function(e) {
        // Hide the send-email modal.
        $("#modal-container .modal").modal('hide');
    };
    var send_email = function(student_id, forced_send) {
        $.ajax({
            url: '/api/send_voting_email',
            type: 'POST',
            dataType: 'json',
            data: {"student_id": student_id, "forced_send": forced_send},
            success: function(data) {
                console.log(data);
                if (data.is_sent) {
                    show_success_msg();
                }
                else if (data.voted) {
                    show_voted_msg();
                }
                else if (data.error_message) {
                    show_error_msg();
                }
                else {
                    show_ask_resent_msg(student_id, data.email_count);
                }
            },
            error: function(data) {
                console.log(data);
            }
        });
        show_sending_msg();
    };
    var show_student_id_request_msg = function() {
        // Change modal content
        $("#modal-container .close_icon").show();
        $("#modal-container .msg-content").html(
            '<input id="student-id" type="text" size=30 name="student-id" placeholder="請輸入台大學號"></input>@ntu.edu.tw'
            );
        $("#modal-container .modal-footer").html(
            '<input id="send-email" type="button" class="btn btn-primary" value="寄認證信">'
            );

        // When click send button, send the email.
        $("#send-email").click(function() {
            var student_id = document.getElementById('student-id').value;
            if (student_id.length > 0) {
                send_email(student_id, false);
            }
            else {
                alert("請先輸入學號");
            }
        });
    };
    var show_sending_msg = function(){
        // Should not close modal now.
        $("#modal-container .close_icon").hide();

        // Change modal content
        $("#modal-container .msg-content").html(
            '寄送中'
            );
        $("#modal-container .modal-footer").html(
            ''
            );

    };
    var show_success_msg = function() {
        $("#modal-container .close_icon").show();

        // Change modal content
        $("#modal-container .msg-content").html(
            '已寄出!'
            );
        $("#modal-container .modal-footer").html(
            '<a class="btn btn-primary" href="">前往台大信箱</a>'
            );
    };
    var show_voted_msg = function() {
        $("#modal-container .close_icon").show();

        // Change modal content
        $("#modal-container .msg-content").html(
            '你投過票囉！'
            );
        $("#modal-container .modal-footer").html(
            '<a class="btn btn-primary" href="">看投票結果</a>'
            );
    };
    var show_error_msg = function() {
        $("#modal-container .close_icon").show();

        // Change modal content
        $("#modal-container .msg-content").html(
            '寄送中'
            );
        $("#modal-container .modal-footer").html(
            ''
            );
    };
    var show_ask_resent_msg = function(student_id, email_count) {
        $("#modal-container .close_icon").show();

        // Change modal content
        var enable_resend = email_count < 3;
        var disable_button_css = "";
        if (!enable_resend) {
            disable_button_css = "disabled";
        }
        $("#modal-container .msg-content").html(
            '你已經寄過認證信了！'
            );
        $("#modal-container .modal-footer").html(
            '<div>' +
            '<a class="btn btn-primary" href="">前往台大信箱</a>' +
            '<a class="btn btn-primary ' + disable_button_css + '" onclick="sendEmailDialog.send_email(\'' + student_id + '\',true);">再寄一次</a>' +
            '</div>' +
            '<span class="button-message">你剩' + (3 - email_count) + '次寄送機會</span>'
            );
    };
    ret.init = init;
    ret.show_email_modal = show_email_modal;
    ret.send_email = send_email;

    return ret;
})();
