function send_message(message, username) {
    $.ajax({
        url: '/_send_message',
        method: 'POST',
        data: JSON.stringify({"user": username, "message": message}),
        dataType: 'json',
        contentType: 'application/json',
        success: function (){
            $("#inp_msg").val('')
        }
    });
}

//TODO: исправить баг, при котором когда у пользователя 0 сообщений, они не загржаются после отправки
function update_messages(username) {
    let last_msg_time = null;
    $.ajax({
        url: '/_load_messages',
        method: 'POST',
        data: JSON.stringify({"user": username, "type": 'load'}),
        dataType: 'json',
        contentType: 'application/json',
        success: function (data) {
            if (data) {
                data[1].forEach(function (el, index) {
                    $("#incoming_msg").append("<a>" + el[0] + ": " + el[1] + "</a><br>")
                })
                last_msg_time = data[0]
                console.log(last_msg_time)
            }
        }
    });
    console.log(last_msg_time)
    window.setInterval(function () {
        $.ajax({
            url: '/_load_messages',
            method: 'POST',
            data: JSON.stringify({"user": username, "msg_time": last_msg_time, "type": 'update'}),
            dataType: 'json',
            contentType: 'application/json',
            success: function (data) {
                if (data) {
                    data[1].forEach(function (el, index) {
                        $("#incoming_msg").append("<a>" + el[0] + ": " + el[1] + "</a><br>")
                    })
                    last_msg_time = data[0]
                    console.log(last_msg_time)
                }
            }
        });
    }, 1000);
}