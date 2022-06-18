let success_msg = _("Deletion was successful!")

function delete_user_post(post_id) {
    if (post_id !== ""){
        post_id = parseInt(post_id)
        $.ajax({
            url: '/api/admin/delete_user_post',
            method: 'DELETE',
            dataType: 'json',
            contentType: 'application/json',
            data: JSON.stringify({post_id: post_id}),
            success: function () {
                alert(success_msg)
            }
        });
    } else {
        alert(_("You need to input post id!"))
    }
}

function delete_group_post(post_id) {
    if (post_id !== ""){
        post_id = parseInt(post_id)
        $.ajax({
            url: '/api/admin/delete_group_post',
            method: 'DELETE',
            dataType: 'json',
            contentType: 'application/json',
            data: JSON.stringify({post_id: post_id}),
            success: function () {
                alert(success_msg)
            }
        });
    } else {
        alert(_("You need to input post id!"))
    }
}

function delete_user(user_id) {
    if (user_id !== ""){
        user_id = parseInt(user_id)
        $.ajax({
            url: '/api/admin/delete_user',
            method: 'DELETE',
            dataType: 'json',
            contentType: 'application/json',
            data: JSON.stringify({user_id: user_id}),
            success: function () {
                alert(success_msg)
            }
        });
    } else {
        alert(_("You need to input user id!"))
    }
}

function delete_group(group_id) {
    if (group_id !== ""){
        group_id = parseInt(group_id)
        $.ajax({
            url: '/api/admin/delete_group',
            method: 'DELETE',
            dataType: 'json',
            contentType: 'application/json',
            data: JSON.stringify({group_id: group_id}),
            success: function () {
                alert(success_msg)
            }
        });
    } else {
        alert(_("You need to input group id!"))
    }
}