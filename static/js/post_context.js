function toggleMenu(post_id) {
    document.getElementById(`post_context_${post_id}`).classList.toggle("post-settings-context-displayed")
}

function deleteUserPost(post_id) {
    let message = $(`#post_${post_id}`)
    $.ajax({
        url: '/api/delete_user_post',
        method: 'DELETE',
        data: JSON.stringify({
            post_id: post_id
        }),
        dataType: 'json',
        contentType: 'application/json',
        success: function (data) {
            if (data["result"] === true) {
                message.remove()
            }
        }
    })
}