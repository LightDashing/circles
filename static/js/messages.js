function leave_chat(chat_id) {
    chat_id = parseInt(chat_id)
     $.ajax({
            url: '/api/leave_chat',
            method: 'DELETE',
            data: JSON.stringify({
                "chat_id": chat_id
            }),
            dataType: 'json',
            contentType: 'application/json',
            success: function (data) {
                $(`#chat_box_${chat_id}`).remove()
            }
        })
}