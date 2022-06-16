$(function onReady() {
    const modal_avatar = document.getElementById("change_avatar")
    const modal_avatar_content = $("#avatar-modal")
    const modal_roles = document.getElementById("roles_changer")
    const modal_roles_content = $("#roles_modal")
    $("#avatar_changer").click(function () {
        modal_avatar.style.display = "block";
        $("#avatar-modal").addClass("showModal")
    })
    $("#roles_menu").click(function () {
        modal_roles.style.display = "block";
        modal_roles_content.addClass("showModal")
    })
    window.onclick = function (event) {
        if (event.target === modal_avatar) {
            modal_avatar_content.removeClass("showModal")
            modal_avatar_content.addClass("hideModal")
            setTimeout(() => modal_avatar.style.display = "none", 250)
        } else if (event.target === modal_roles) {
            modal_roles_content.removeClass("showModal")
            modal_roles_content.addClass("hideModal")
            setTimeout(() => modal_roles.style.display = "none", 250)
        }
    }
    $("#close_button").click(function () {
        modal_avatar_content.removeClass("showModal")
        $("#avatar-modal").addClass("hideModal")
        setTimeout(() => modal_avatar.style.display = "none", 250)
    })
    $("#close_roles_button").click(function () {
        modal_roles_content.removeClass("showModal")
        modal_roles_content.addClass("hideModal")
        setTimeout(() => modal_roles.style.display = "none", 250)
    })
    const mainForm = document.getElementById("main_form")
    mainForm.onsubmit = function (event) {
        let settingsForm = new FormData(mainForm)
        send_settings(settingsForm)
        event.preventDefault()
    }
    const fileInput = document.getElementById("picture")
    fileInput.addEventListener('change', function () {
        addImage("avatar-modal", "crop-image","new_image", this.files, send_avatar)
    }, false)

    $("#roles_selector").selectize({
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
                return `<div style="font-size: 1.1em; padding: 10px">${item["role_name"]}</div>`
            },
            item: function (item, escape) {
                return `<div class="item-selected" 
                        style="background: ${item["role_color"]}; border: none; border-radius: 15px;
                        text-shadow: 0 1px 0 rgba(0, 51, 83, 0.3); color: ${item["font_color"]}"
                            id="edit_${item["id"]}">${item["role_name"]}</div>`
            }
        },
        onChange: function (value) {
            let edit_role_color_picker = document.querySelector("#edit_role_color")
            edit_role_color_picker.disabled = false;
            let edit_role_name = $("#edit_role_name")
            edit_role_name.prop("disabled", false)
            $("#edit_role_button").prop("disabled", false)
            $("#delete_role_button").prop("disabled", false)
            changeRoleHandler(edit_role_color_picker, edit_role_name, $("#can_post"), $("#roles_selector"), value)
        }
    })
    $('textarea').each(function () {
        autosize(this)
    })

    $("#edit_role_button").click(function () {
        let selector = $("#roles_selector")
        let role_name = $("#edit_role_name")
        let color_picker = $("#edit_role_color")[0].jscolor
        let can_post = document.getElementById("can_post").checked
        saveRoleHandler(selector, role_name, color_picker, can_post)
    })

    $("#delete_role_button").click(function () {
        deleteRoleHandler($("#roles_selector"))
    })

    $("#create_role_b").click(function () {
        let name = $("#create_role_name").val()
        let color = $("#create_role_color")[0].jscolor
        let font_color = fColorByBackground(color.toRGBString())
        console.log(name)
        if (name === "") {
            alert("Input role name!")
        } else {
            $.ajax({
                url: "/api/create_role",
                method: "POST",
                data: JSON.stringify({role_name: name, role_color: color.toHEXString(), font_color: font_color}),
                dataType: 'json',
                contentType: 'application/json',
                success: function (data) {
                    if (data) {
                        $("#roles_selector")[0].selectize.addOption(data)
                    } else {
                        alert(_('You already have 6 tags created!'))
                    }
                }
            })
        }
    })
})


function send_avatar(data) {
    let base64img = data.toDataURL()
    $.ajax({
        url: '/api/upload_settings',
        method: 'POST',
        dataType: 'json',
        contentType: 'application/json',
        data: JSON.stringify({"image": base64img}),
        success: function updateModal(data) {
            console.log(data)
            if (data === 2) {
                alert(_('This file is too large!'))
            } else if (data === 1) {
                // alert('You little cheater')
            }
        }
    });
}

function send_settings(form) {
    $.ajax({
        url: '/api/upload_settings',
        method: 'POST',
        processData: false,
        contentType: false,
        data: form,
        success: function displayErrors(data) {
            let msg = document.createElement('span');
            if (data['unknown_error']) {
                msg.innerText = _("Some unknown error occurred!");
                msg.classList.add('error-message');
                $(".unknown-error").append(msg);
            }
            if (data['u_name_r'] === 1) {
                msg.innerText = _("User with that username already exist!");
                msg.classList.add('error-message');
                $(".username-error").append(msg);
            } else if (data['u_name_r'] === 2) {
                msg.innerText = _("Username length is incorrect!");
                msg.classList.add('error-message');
                $(".username-error").append(msg);
            }
            if (data['u_email_r'] === 1) {
                msg.innerText = _("Email isn't valid!");
                msg.classList.add('error-message');
                $(".email-error").append(msg)
            } else if (data['u_email_r'] === 2) {
                msg.innerText = _("That email already belongs to someone!")
                msg.classList.add('error-message');
                $(".email-error").append(msg)
            }
        }
    })
}

