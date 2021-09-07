let is_post_private = true
let roles_list

function init(name, username) {
    //TODO: потом переделать, выглядит некрасиво
    hide_all()

    let create_post = $("#create_post")
    create_post.hide()

    let role_label = $("#roles_label")
    let roles_selector = $("#add_roles")
    let private_selector = $("#private_post")
    let roles_container = $(".new-post-sub-tags-roles")
    let modal_window = $(".tag-modal-window")
    let modal_window_content = $(".tag-modal-window-content")
    let html = jQuery('html')

    private_selector.click(function () {
        if (is_post_private) {
            is_post_private = false
            role_label.fadeOut(250)
            roles_selector.fadeOut(250)
            roles_container.fadeOut(250)
            private_selector.html("public")
        } else {
            is_post_private = true
            role_label.fadeIn(250)
            roles_selector.fadeIn(250)
            roles_container.fadeIn(250)
            private_selector.html("private")
        }
    })

    roles_selector.click(function addRoles() {
        modal_window.show()
        modal_window_content.addClass("showModal")
        html.css("overflow", "hidden")
    })

    window.onclick = function (event) {
        if (event.target === modal_window[0]) {
            html.css("overflow", "auto")
            modal_window_content.removeClass("showModal")
            modal_window_content.addClass("hideModal")
            setTimeout(() => modal_window.hide(), 250)
        }
    }

    autosize($("#post-input"))
    $("#roles_selector").select2()

    $.ajax({
        url: '/api/check_friend',
        method: 'POST',
        data: JSON.stringify({'name': name}),
        dataType: 'json',
        contentType: 'application/json',
        success: function (data) {
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
        url: '/api/add_friend',
        method: 'POST',
        data: JSON.stringify({'name': name}),
        dataType: 'json',
        contentType: 'application/json',
        success: function (data) {
            console.log(data)
            $("#add_friend").hide()
            $("#cancel_request").show()
        }
    });
}

function accept_request(name) {
    $.ajax({
        url: '/api/accept_friend',
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
        url: '/api/remove_friend',
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

function publish_post(post_msg, post_attach, where_id, is_private) {
    $.ajax({
        url: '/api/publish_post',
        method: 'POST',
        data: JSON.stringify({
            "message": post_msg, "attach": post_attach, "where_id": where_id, "is_private": is_private
        }),
        dataType: 'json',
        contentType: 'application/json',
        success: function (data) {
        },
        error: function () {
        }
    })
}