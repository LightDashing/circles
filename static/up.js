function init(name, username) {
    hide_all()
    let create_post = $("#create_post")
    create_post.hide()
    let add_post = $("#add_post")
    add_post.click(function () {
        if (create_post.is(':visible')) {
            create_post.hide("slow")
        } else {
            create_post.show("slow")
            //add_post.hide()
        }
    })
    $.ajax({
        url: '/_check_friend',
        method: 'POST',
        data: JSON.stringify({'name': name}),
        dataType: 'json',
        contentType: 'application/json',
        success: function (data) {
            console.log(data)
            if (data['first_user_id'] === current_userid && data['is_request']) {
                $("#cancel_request").show()
            } else if (data['second_user_id'] === current_userid && data['is_request']) {
                $("#decline_request").show()
                $("#accept_request").show()
            } else if (!data['is_request'] && data) {
                $("#remove_friend").show()
            } else if (data === false) {
                $("#add_friend").show();
            }
        },
        error: function (data) {
        }
    });
}

function add_friend(name) {
    $.ajax({
        url: '/_add_friend',
        method: 'POST',
        data: JSON.stringify({'name': name}),
        dataType: 'json',
        contentType: 'application/json',
        success: function () {
            $("#add_friend").hide()
            $("#cancel_request").show()
        }
    });
}

function accept_request(name) {
    $.ajax({
        url: '/_accept_friend',
        method: 'POST',
        data: JSON.stringify({'name': name}),
        dataType: 'json',
        contentType: 'application/json',
        success: function () {
            hide_all()
            $("#remove_friend").show()
        }
    });
}

function remove_friend(name) {
    $.ajax({
        url: '/_remove_friend',
        method: 'POST',
        data: JSON.stringify({'name': name}),
        dataType: 'json',
        contentType: 'application/json',
        success: function () {
            hide_all()
            $("#add_friend").show()
        }
    });
}

function hide_all() {
    $("#add_friend").hide();
    $("#remove_friend").hide();
    $("#decline_request").hide();
    $("#accept_request").hide();
    $("#cancel_request").hide();
}

function publish_post(post_msg, post_attach, view_level, whereid, fromid) {
    $.ajax({
        url: '/_publish_post',
        method: 'POST',
        data: JSON.stringify({
            "message": post_msg, "attach": post_attach,
            "view_lvl": view_level, "whereid": whereid, "fromid": fromid
        }),
        dataType: 'json',
        contentType: 'application/json',
        success: function (data) {
            console.log(data)
        },
        error: function () {
            console.log('Failure')
        }
    })
}