function renderChatMessage(username, message) {
    let message_style
    if (message["from_user_id"] === username) {
        message_style = "align-self: end; background: #e3e4f8"
    } else {
        message_style = ""
    }
    let element = `<div class="message-box" style="${message_style}">
            <img class="message-box-avatar" src="${message["user_avatar"]}" alt="user avatar">
            <div class="message-box-text">
            <span class="from-user">${message["from_user_id"]}</span>
            <span class="message-text">${message["message"]}</span>
            </div>`
    if (message["attachment"]) {
        element = appendAttachments(element, message)
    } else {
        element += `</div>`
    }
    return element
}

function renderDialogMessage(username, message) {
    let message_style
    if (message["from_user_id"] === username) {
        message_style = "align-self: end; background: #e3e4f8"
    } else {
        message_style = ""
    }
    let element = `<div class="message-box" style="${message_style}">
            <div class="message-box-text">
            <span class="message-text">${message["message"]}</span>
            </div>`
    if (message["attachment"]) {
        element = appendAttachments(element, message)
    } else {
        element += `</div>`
    }
    return element
}

function appendAttachments(element, message) {
    element += `
            <span class="flex-break"></span>
            <div class="message-pinned-images">`
    message["attachment"].forEach(function (attach) {
        attach["links_array"].forEach(function (image) {
            if (image) {
                element += `<img class="post-pinned-images" alt="attached image" src="${image}" onclick="showModalImage('image_modal', 'image_modal_content',
                                                 '${image}', 'image_modal_content',
                                                 '${message["attachment"][0]["date_added"]}', '${message["from_user_id"]}',
                                                 '${message["user_avatar"]}')">`
            }
        })
    })
    element += '</div></div>'
    return element
}