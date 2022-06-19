let is_post_private = true
let pinned_num = 0
let username

function init(name) {
    //TODO: потом переделать, выглядит некрасиво
    hideFriendsButtons()
    let create_post = $("#create_post")
    create_post.hide()
    username = name

    let roles_selector = $("#role_selector")
    let private_selector = $("#private_post")

    let add_role_modal = $("#add_role_modal")
    let add_role_modal_content = $("#add_role_modal_content")

    let edit_role_modal = $("#modal_edit_role")
    let edit_role_modal_content = $("#modal_edit_role_content")

    document.querySelector("#edit_role_color").disabled = true;
    $("#edit_role_name").prop('disabled', true)


    let tags_flexbox = $('.new-post-sub-tags')
    let html = jQuery("html")
    let post_input = $("#post-input")

    pinToObject({
        obj: post_input,
        image_container: '#pinned_container',
        image_class: 'pinned-image',
        image_desc_class: 'pinned-image-description',
    })

    function showModalEditRoles() {
        edit_role_modal.show()
        edit_role_modal_content.addClass("showModal")
        html.css("overflow", "hidden")
    }

    function hideModalEditRoles() {
        html.css("overflow", "auto")
        edit_role_modal_content.removeClass("showModal")
        edit_role_modal_content.addClass("hideModal")
        setTimeout(() => edit_role_modal.hide(), 250)
    }

    function showModalAddRoles() {
        add_role_modal.show()
        add_role_modal_content.addClass("showModal")
        html.css("overflow", "hidden")
    }

    function hideModalAddRoles() {
        html.css("overflow", "auto")
        add_role_modal_content.removeClass("showModal")
        add_role_modal_content.addClass("hideModal")
        setTimeout(() => add_role_modal.hide(), 250)
    }

    $("#edit_roles").click(function () {
        showModalEditRoles()
    })

    function renderOptions(item, escape) {
        return `<div style="font-size: 1.1em; padding: 10px">${item["role_name"]}</div>`
    }

    function renderItem(item, escape) {
        return `<div class="item-selected" 
                        style="background: ${item["role_color"]}95; border: none; border-radius: 15px;
                        text-shadow: 0 1px 0 rgba(0, 51, 83, 0.3); color: ${item["font_color"]}"
                            id="edit_${item["id"]}">${item["role_name"]}</div>`
    }

    $("#edit_roles_selector").selectize({
        valueField: 'role_name',
        labelField: 'role_name',
        searchField: ['role_name'],
        preload: true,
        load: function (query, callback) {
            $.ajax({
                url: '/api/get_user_roles', method: 'GET',
                success: function (data) {
                    callback(data)
                }
            })
        },
        render: {
            option: function (item, escape) {
                return renderOptions(item, escape)
            },
            item: function (item, escape) {
                return renderItem(item, escape)
            }
        },
        onChange: function (value) {
            let edit_role_color_picker = document.querySelector("#edit_role_color")
            edit_role_color_picker.disabled = false;
            let edit_role_name = $("#edit_role_name")
            edit_role_name.prop('disabled', false)
            $("#edit_role_button").prop("disabled", false)
            $("#delete_role_button").prop("disabled", false)
            changeRoleHandler(edit_role_color_picker, edit_role_name, $("#can_post"), $("#roles_selector"), value)
        }

    })

    let delete_role_button = $("#delete_role_button")
    delete_role_button.prop("disabled", true)

    delete_role_button.click(function deleteRole() {
        let selector = $("#edit_roles_selector")
        deleteRoleHandler(selector, hideModalEditRoles)
    })

    $("#make_post").click(function () {
        let role_selector = $("#roles_selector")
        let roles = null
        if (role_selector.length !== 0) {
            roles = role_selector[0].selectize.getValue();
        }
        let pinned_images = Array.from($(".pinned-image"));
        for (let i = 0; i < pinned_images.length; i++) {
            pinned_images[i] = pinned_images[i].src;
        }
        if (post_input.val() !== '' || pinned_images.length > 0) {
            publish_post(post_input.val(), where_id, is_post_private, roles, pinned_images);
            post_input.val("")
            $(".pinned-image").remove()
        }
    })

    let edit_role_button = $("#edit_role_button")
    edit_role_button.prop("disabled", true)

    edit_role_button.click(function () {
        let selector = $("#edit_roles_selector")
        let old_role_name = selector[0].selectize.getValue()
        let role_name = $("#edit_role_name")
        let can_post = document.getElementById("can_post").checked
        let color_picker = $("#edit_role_color")[0].jscolor
        saveRoleHandler(selector, role_name, color_picker, can_post, function updateSelector(data) {
            $("#roles_selector")[0].selectize.updateOption(old_role_name, {
                role_name: data["role_name"],
                role_color: data["role_color"],
                font_color: data["font_color"],
                id: data["id"],
                creator: data["creator"]
            })
        })
    })

    private_selector.click(function () {
        if (is_post_private) {
            is_post_private = false
            roles_selector.fadeOut(250)
            setTimeout(() => tags_flexbox.css("display", "inline"), 240)
            private_selector.html(_("public"))

        } else {
            is_post_private = true
            tags_flexbox.css("display", "flex")
            roles_selector.fadeIn(250)
            private_selector.html(_("private"))
        }
    })

    window.onclick = function (event) {
        if (event.target === add_role_modal[0]) {
            hideModalAddRoles()
        } else if (event.target === edit_role_modal[0]) {
            hideModalEditRoles()
        }
    }

    function autoCloseAddModal(callback){
        /* This function is waiting for add_role_modal window to close and then calls callback
        * It was designed for role selector, if user closes modal window without creating role */
        if (add_role_modal.css("display") === "none"){
            callback()
        }
    }

    autosize(post_input)
    $('#roles_selector').selectize({
        plugins: ['remove_button'],
        valueField: "role_name",
        labelField: "role_name",
        placeholder: _('Start typing something...'),
        searchField: ["role_name"],
        maxItems: 6,
        preload: true,
        render: {
            option: function (item, escape) {
                return renderOptions(item, escape)
            },
            item: function renderItem(item, escape) {
                return `<div class="item-selected" 
                        style="background: ${item["role_color"]}; border: none; border-radius: 15px;
                        text-shadow: 0 1px 0 rgba(0, 51, 83, 0.3); color: ${item["font_color"]}">
                        ${item["role_name"]}</div>`
            }
        },
        create: function createElement(input, callback) {
            /* This function shows modal window for user to create new role and then sends it to server */
            showModalAddRoles()
            $("#role_name").val(input)
            let role_name, role_color, font_color
            setInterval(() => autoCloseAddModal(callback), 300)
            $("#pin_roles").click(function () {
                let color_picker = document.querySelector("#role_color").jscolor
                role_name = $("#role_name").val()
                role_color = color_picker.toHEXString()
                font_color = fColorByBackground(color_picker.toRGBString())
                hideModalAddRoles()
                $.ajax({
                    url: '/api/create_role',
                    method: 'POST',
                    data: JSON.stringify({role_name: role_name, role_color: role_color, font_color: font_color}),
                    dataType: 'json',
                    contentType: 'application/json',
                    success: function (data) {
                        if (data) {
                            $("#edit_roles_selector")[0].selectize.addOption(data)
                            callback(data)
                        } else {
                            let alert_message = _("You already have 6 tags created!'")
                            alert(alert_message)
                        }
                    }
                })
            })
        },
        load: function (query, callback) {
            $.ajax({
                url: '/api/get_user_roles', method: 'GET',
                success: function (data) {
                    callback(data)
                }
            })
        }
    })

    $.ajax({
        /* Setting friend buttons, if user is friend or not */
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
    /* This function sends request to add user to friends*/
    $.ajax({
        url: '/api/add_friend',
        method: 'POST',
        data: JSON.stringify({'name': name}),
        dataType: 'json',
        contentType: 'application/json',
        success: function (data) {
            $("#add_friend").hide()
            $("#cancel_request").show()
        }
    });
}

function accept_request(name) {
    /* This function sends request to accept friendship request */
    $.ajax({
        url: '/api/accept_friend',
        method: 'POST',
        data: JSON.stringify({'name': name}),
        dataType: 'json',
        contentType: 'application/json',
        success: function () {
            hideFriendsButtons()
            $("#remove_friend").show()
        }
    });
}

function remove_friend(name) {
    /* This function sends request to delete friend */
    $.ajax({
        url: '/api/remove_friend',
        method: 'DELETE',
        data: JSON.stringify({'name': name}),
        dataType: 'json',
        contentType: 'application/json',
        success: function () {
            hideFriendsButtons()
            $("#add_friend").show()
        }
    });
}

function hideFriendsButtons() {
    /* This function hides all buttons affiliated with friends system */
    $("#add_friend").hide();
    $("#remove_friend").hide();
    $("#decline_request").hide();
    $("#accept_request").hide();
    $("#cancel_request").hide();
}

function publish_post(post_msg, where_id, is_private, roles, pinned_images) {
    /* This function creates new post on user pge */
    $.ajax({
        url: '/api/publish_post',
        method: 'POST',
        data: JSON.stringify({
            "message": post_msg, "where_id": where_id, "is_private": is_private, "roles": roles,
            pinned_images: pinned_images
        }),
        dataType: 'json',
        contentType: 'application/json',
        success: function (data) {
            $.ajax({
                url: '/api/get_your_post', data: `p_id=${data["id"]}&u_name=${username}`,
                success: function (data) {
                    $(".posts").prepend(data)
                }
            })
        },
        error: function () {
        }
    })
}