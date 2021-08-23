function send_message(message, user, chat_id) {
    chat_id = parseInt(chat_id)
    $.ajax({
        url: '/api/send_message',
        method: 'POST',
        data: JSON.stringify({"message": message, "chat_id": chat_id, "attachment": null}),
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
            url: '/api/load_messages',
            method: 'POST',
            data: JSON.stringify({"user": username, "msg_time": msg_time, "type": 'update', "chat_id": chat_id}),
            dataType: 'json',
            contentType: 'application/json',
            success: function (data) {
                if (data) {
                    data.forEach(function (el) {
                        let element;
                        if (el["from_user_id"] === username) {
                            element = `<div class="message-box" style="align-self: end; background: #CEC5C3">
                                     <span class="from-user"> ${el["from_user_id"]}: </span> 
                                    <span class="message-text"> ${el["message"]}</span></div>`
                        } else {
                            element = `<div class="message-box"><span class="from-user"> ${el["user"]}: </span> 
                                    <span class="message-text"> ${el["message"]}</span></div>`
                        }
                        $("#incoming_msg").append(element)
                        msg_time = el['message_date']
                    })
                }
            }
        });
    }, 1550);
}