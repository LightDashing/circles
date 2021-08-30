let message_updater;
let chat_list = []

$(function onReady() {
    $("#all_messages_button").click(function () {
        changeLayout();
    })
})

function send_message(message, user, chat_id) {
    chat_id = parseInt(chat_id)
    $.ajax({
        url: '/api/send_message',
        method: 'POST',
        data: JSON.stringify({"message": message, "chat_id": chat_id, "attachment": null}),
        dataType: 'json',
        contentType: 'application/json',
        success: function () {
            $(`#message_${chat_id}`).val('');
        }
    })
}

// TODO: Переделать, так чтобы эта функция проверяла ВСЕ сообщения, которые могут приходить
function update_messages(username, chat_id, last_msg_time, type) {
    // Эта функция обновляет сообщения каждые 1.5 секунды, либо один раз загружает их
    // В зависимости от того чата, который загружен, будет заполнено #incoming_msg для необходимого чата
    let msg_time = last_msg_time;
    chat_id = parseInt(chat_id)
    message_updater = window.setInterval(function () {
        $.ajax({
            url: '/api/load_messages',
            method: 'POST',
            data: JSON.stringify({"msg_time": msg_time, "type": type, "chat_id": chat_id}),
            dataType: 'json',
            contentType: 'application/json',
            success: function (data) {
                if (data) {
                    data.forEach(function (el) {
                        let element;
                        if (el["from_user_id"] === username) {
                            element = `<div class="message-box" style="align-self: end; background: #CEC5C3">
                                     <span class="from-user"> ${el["from_user_id"]}: </span> 
                                    <span class="message-text"> ${el["message"]}</span></div>`;
                        } else {
                            element = `<div class="message-box"><span class="from-user"> ${el["from_user_id"]}: </span> 
                                    <span class="message-text"> ${el["message"]}</span></div>`;
                        }
                        $(`#incoming_msg_${chat_id}`).append(element);
                        msg_time = el['message_date']
                    })
                }
            }
        });
    }, 1550);
    // На случай если функция вызывается один раз просто чтобы загрузить все сообщения
    if (type === "load") {
        window.clearInterval(message_updater);
    }
}

function getUserChats() {
    let chats = $(".all-chats")
    chats.empty()
    $.ajax({
        url: '/api/load_chats',
        method: 'POST',
        success: function (data) {
            data.forEach(function (element) {
                let el = `<div class="new-button" onclick="changeChat(${element['id']}, '${element['chatname']}')"
                    <a>${element['chatname']}</a><br>
                </div>`;
                chats.append(el);
            })
        }
    })
}

function changeChat(chat_id, chat_name) {
    let all_messages = $("#all_messages");
    let chat_container = $(".chat-container");
    if (!all_messages.is(":hidden")) {
        all_messages.hide();
    } else {
        chat_container.empty();
    }
    chat_container.load('/api/load_chat_template', `id=${chat_id}`,
        function resetSendButton() {
            $(`#send_message_${chat_id}`).click(function () {
                send_message($(`#message_${chat_id}`).val(), current_username, chat_id);
                $(`message_${chat_id}`).val("");
                update_messages(current_username, chat_id, last_msg_time, "update");
            })
            if (!chat_list.includes(chat_name)) {
                let new_chat_button = `<button class="new-button" id="chat_${chat_id}" 
                                    onclick="changeChat(${chat_id}, '${chat_name}')">${chat_name}</button>`
                chat_list.push(chat_name)
                $(".chat-messages-buttons").append(new_chat_button)
            }
        }
    )

}

function changeLayout() {
    let user_messages = $(".chat-content");
    let all_messages = $("#all_messages");
    if (!user_messages.is(":hidden")) {
        user_messages.hide();
        all_messages.show();
        clearInterval(message_updater);
        getUserChats();
    }
}