let message_updater;
let chat_list = []
let max_image_height = 0
let messages_loaded = true
let html = jQuery("html")

$(function onReady() {
    $("#all_messages_button").click(function () {
        changeLayout();
    })
    window.scrollTo(0, document.querySelector(".main-row").scrollHeight);
    $(window).scroll(function getScrolling() {
        if ($(window).scrollTop() < 400 && messages_loaded && $("#all_messages").is(":hidden")) {
            messages_loaded = false
            addMoreContent(messages_loaded);
        }
    })
    document.addEventListener("mousedown", function (e) {
        if (!e.target.classList.contains("message-settings-context") && !$(e.target).parent()[0].classList.contains("message-settings-context")) {
            let context_menu = document.getElementsByClassName("message-settings-context-displayed")
            if (context_menu.length !== 0) {
                toggleMenu(context_menu[0].id.split("_")[2])
            }
        }
    })
    let image_modal_content = $("#image_modal_content")
    let image_modal = $("#image_modal")
    window.onclick = function (event) {
        if (event.target === image_modal[0]) {
            hideModalImage(image_modal, image_modal_content)
        }
    }

    let textarea = $("textarea")
    textarea.each(function () {
        autosize(this)
    }).on('autosize:resized', function () {
        let input_height = parseInt(textarea.css("height"))
        if ($(".message-input-pinned > img") !== 0) {
            $(".message-input").css("height", `${input_height + max_image_height}px`)
        } else {
            $(".message-input").css("height", `${input_height}px`)
        }
    })
    pinToObject({
        obj: textarea,
        image_container: '#pinned-container',
        image_class: 'message-input-pinned',
        image_desc_class: 'pinned-image-description',
        add_element_callback: addImageContainer,
        delete_element_callback: deleteImageContainer
    })


})

function enableEditing(message_id, chat_id) {
    let text_editor = $(`#message_${chat_id}`)
    let edit_button = $(`#edit_message`)
    let send_button = $(`#send_message_${chat_id}`)
    if (send_button.css("display") === "none") {
        return
    }
    send_button.css("display", "none")
    edit_button.css("display", "inline")
    edit_button.click(function () {
        editMessage(message_id, chat_id, text_editor.val())
        text_editor.val("")
        edit_button.css("display", "none")
        send_button.css("display", "inline")
    })
}

function addMoreContent(old_msg_loader) {
    $.ajax({
        url: '/api/load_old',
        method: 'GET',
        data: {'c': chat_id, 'f_msg': first_msg_time},
        success: function (data) {
            if (data.length !== 0) {
                first_msg_time = data["messages"][0]["message_date"]
                data["messages"].reverse().forEach(function (el) {
                    $(".incoming_msg").prepend(renderChatMessage(current_username, el))
                })
                if (data["older"] === true) {
                    old_msg_loader = true
                }
                console.log(old_msg_loader)
            }
        }
    })
}

function addImageContainer(element) {
    element = $(element)
    if (element.height() > max_image_height) {
        let msg_input = $(".message-input")
        let height = msg_input.height() - max_image_height
        msg_input.css("height", `${height}px`)
        max_image_height = element.height() + 5
        msg_input.css("height", `${height + max_image_height}px`)
    }
}

// TODO: Возможно можно написать получше
function deleteImageContainer(element) {
    let pinned_images = $(".message-input-pinned > img")
    let msg_input = $(".message-input")
    let initial_height = msg_input.height()
    if (pinned_images.length === 1) {
        msg_input.css("height", `${initial_height - max_image_height}px`)
        max_image_height = 0
    } else {
        element = $(element)
        if (max_image_height === element.height() + 5) {
            let new_height = 0
            Array.from(pinned_images).forEach(function (el) {
                el = $(el)
                if (el.height() > new_height && new_height !== max_image_height) {
                    new_height = el.height()
                }
            })
            console.log(new_height, max_image_height)
            msg_input.css("height", `${initial_height - max_image_height}px`)
            initial_height = msg_input.height()
            msg_input.css("height", `${initial_height + new_height + 5}px`)
            max_image_height = new_height
        }
    }
}

function send_message(message, user, chat_id) {
    chat_id = parseInt(chat_id);
    let pinned_images = Array.from($(".message-input-pinned > img"));
    for (let i = 0; i < pinned_images.length; i++) {
        pinned_images[i] = pinned_images[i].src;
    }
    $.ajax({
        url: '/api/send_message',
        method: 'POST',
        data: JSON.stringify({
            "message": message,
            "chat_id": chat_id,
            "attachment": null,
            pinned_images: pinned_images
        }),
        dataType: 'json',
        contentType: 'application/json',
        success: function () {
            $(`#message_area_${chat_id}`).val('');
            $(`#pinned-container`).val(``);
        }
    })
}

// TODO: Переделать, так чтобы эта функция проверяла ВСЕ сообщения, которые могут приходить
function update_messages(username, chat_id, last_msg_time, type) {
    // Эта функция обновляет сообщения каждые 1.5 секунды, либо один раз загружает их
    // В зависимости от того чата, который загружен, будет заполнено #incoming_msg для необходимого чата
    let msg_time = last_msg_time;
    chat_id = parseInt(chat_id)
    $.ajax({
        url: '/api/update_all',
        method: 'GET',
        success: function (data) {
            data["chats"].forEach(function (elem) {
                if (elem["chat_id"] === chat_id) {
                    Cookies.set("new_messages", parseInt(Cookies.get("new_messages")) - 1)
                    setMessages(parseInt(Cookies.get("new_messages")))
                }
            })
        }
    })
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
                        let element = renderChatMessage(current_username, el)
                        $(`#incoming_msg_${chat_id}`).append(element);
                        msg_time = el['message_date']
                    })
                    messages_loaded = true
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

function changeChat(l_chat_id, chat_name) {
    let all_messages = $("#all_messages");
    let chat_container = $(".chat-container");
    if (!all_messages.is(":hidden")) {
        all_messages.hide();
    } else {
        chat_container.empty();
    }
    chat_container.load('/api/load_chat_template', `id=${l_chat_id}`,
        function changeChatEvents() {
            // window.scrollTo(0, document.querySelector(".main-row").scrollHeight);
            chat_id = l_chat_id
            let textarea = $('textarea')
            textarea.each(function () {
                autosize(this)
            }).on('autosize:resized', function () {
                let input_height = parseInt(textarea.css("height"))
                $(".message-input").css("height", `${input_height}px`)
            })
            $(`#send_message_${l_chat_id}`).click(function () {
                send_message($(`#message_area_${l_chat_id}`).val(), current_username, l_chat_id);
                update_messages(current_username, l_chat_id, last_msg_time, "update");
            })
            if (!chat_list.includes(chat_name)) {
                let new_chat_button = `<button class="new-button" id="chat_${l_chat_id}" 
                                    onclick="changeChat(${l_chat_id}, '${chat_name}')">${chat_name}</button>`
                chat_list.push(chat_name)
                $(".chat-messages-buttons").append(new_chat_button)
            }
            messages_loaded = true
            window.scrollTo(0, document.querySelector(".main-row").scrollHeight);
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