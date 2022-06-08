function toggleMenu(message_id) {
    document.getElementById(`settings_context_${message_id}`).classList.toggle("message-settings-context-displayed")
}

function deleteMessage(message_id, chat_id) {
    let message = $(`#message_${message_id}`)
    $.ajax({
        url: '/api/delete_message',
        method: 'DELETE',
        data: JSON.stringify({
            chat_id: chat_id,
            message_id: message_id
        }),
        dataType: 'json',
        contentType: 'application/json',
        success: function (data) {
            if (data) {
                message.remove()
            }
        }
    })
}

function editMessage(message_id, chat_id, new_text) {
    let message = $(`#message_${message_id}`)
    console.log(new_text)
    $.ajax({
        url: '/api/edit_message',
        method: 'PATCH',
        data: JSON.stringify({
            chat_id: chat_id,
            message_id: message_id,
            new_text: new_text
        }),
        dataType: 'json',
        contentType: 'application/json',
        success: function (data) {
            if (data) {
                message.children()[0].children[1].children[1].innerHTML = new_text
            }
        }
    })
}