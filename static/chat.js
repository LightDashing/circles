function send_message(message, user, chat_id) {
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
                    try {
                        data[1].forEach(function (el, index) {
                            let element;
                            if (el["user"] === username){
                                element = `<div class="message-box" style="align-self: end; background: #CEC5C3">
                                     <span class="from-user"> ${el["user"]}: </span> 
                                    <span class="message-text"> ${el["message"]}</span></div>`
                            } else {
                                element = `<div class="message-box"><span class="from-user"> ${el["user"]}: </span> 
                                    <span class="message-text"> ${el["message"]}</span></div>`
                            }
                            // let div = document.createElement("div")
                            // let author = document.createElement("span")
                            // author.innerHTML = el['user'] + ": "
                            // let message = document.createElement("span")
                            // message.innerHTML = el['message'] + "<br>"
                            // $("#incoming_msg").append(author, message)
                            $("#incoming_msg").append(element)
                        })
                    } catch (TypeError) {

                    }
                    msg_time = data[0]
                }
            }
        });
    }, 1250);
}