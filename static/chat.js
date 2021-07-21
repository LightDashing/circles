function send_message(message, user, chat_id){
    chat_id = parseInt(chat_id)
    $.ajax({
        url: '/chat/send_message',
        method: 'POST',
        data: JSON.stringify({"user": user, "message": message, "chat_id": chat_id, "attachment": null}),
        dataType: 'json',
        contentType: 'application/json',
        success: function () {
            $("#message").val('')
        }
    })
}

function update_messages(username, chat_id, last_msg_time) {
    let msg_time = last_msg_time
    chat_id = parseInt(chat_id)
    window.setInterval(function () {
        $.ajax({
            url: '/chat/load_messages',
            method: 'POST',
            data: JSON.stringify({"user": username, "msg_time": msg_time, "type": 'update', "chat_id": chat_id}),
            dataType: 'json',
            contentType: 'application/json',
            success: function (data) {
                if (data) {
                    try{
                    data[1].forEach(function (el, index) {
                        let author = document.createElement("span")
                        author.innerHTML = el['user'] + ": "
                        let message = document.createElement("span")
                        message.innerHTML = el['message'] + "<br>"
                        $("#incoming_msg").append(author, message)
                    })} catch (TypeError) {

                    }
                    msg_time = data[0]
                }
            }
        });
    }, 1000);
}