function send_message(message, username, chat_id) {
    chat_id = parseInt(chat_id)
    $.ajax({
        url: '/_send_message',
        method: 'POST',
        data: JSON.stringify({"user": username, "message": message, "chat_id": chat_id, "attachment": null}),
        dataType: 'json',
        contentType: 'application/json',
        success: function (){
            $("#inp_msg").val('')
        }
    });
}

//TODO: исправить баг, при котором когда у пользователя 0 сообщений, они не загржаются после отправки
function update_messages(username, chat_id) {
    chat_id = parseInt(chat_id)
    let last_msg_time = null;
    $.ajax({
        url: '/_load_messages',
        method: 'POST',
        data: JSON.stringify({"user": username, "type": 'load', "chat_id": chat_id}),
        dataType: 'json',
        contentType: 'application/json',
        success: function (data) {
            if (data) {
                try{
                data[1].forEach(function (el, index) {
                    $("#incoming_msg").append("<a>" + el['user'] + ": " + el['message'] + "</a><br>")
                })} catch (TypeError){
                    
                }
                last_msg_time = data[0]
            }
        }
    });
    console.log(last_msg_time)
    window.setInterval(function () {
        $.ajax({
            url: '/_load_messages',
            method: 'POST',
            data: JSON.stringify({"user": username, "msg_time": last_msg_time, "type": 'update', "chat_id": chat_id}),
            dataType: 'json',
            contentType: 'application/json',
            success: function (data) {
                if (data) {
                    try{
                    data[1].forEach(function (el, index) {
                        $("#incoming_msg").append("<a>" + el['user'] + ": " + el['message'] + "</a><br>")
                    })} catch (TypeError) {
                        
                    }
                    last_msg_time = data[0]
                }
            }
        });
    }, 1000);
}