function changeRoleHandler(color_picker, name_picker, can_post_checkbox, role_selector, value) {
    let options = role_selector[0].selectize.options
    try {
        name_picker.val(options[value]["role_name"])
    } catch (TypeError) {
        role_selector[0].selectize.refreshOptions()
        return
    }
    color_picker.jscolor.fromString(options[value]["role_color"])
    can_post_checkbox.prop("checked", options[value]["can_post"])
    color_picker.jscolor.onInput = function () {
        let edit = $(`#edit_${options[value]["id"]}`)
        edit.css("background", `${color_picker.jscolor.toHEXString()}`)
        edit.css("color", fColorByBackground(color_picker.jscolor.toRGBString()))
    }
    name_picker.keyup(function () {
        $(`#edit_${options[value]["id"]}`).html(name_picker.val())
    })
}

function deleteRoleHandler(selector, callback) {
    let options = selector[0].selectize.options
    let value = selector[0].selectize.getValue()
    let role_id = options[value]["id"]
    selector[0].selectize.removeOption(value)
    $("#roles_selector")[0].selectize.removeOption(value)
    $.ajax({
        url: '/api/delete_role',
        method: 'POST',
        data: JSON.stringify({role_id: role_id}),
        dataType: 'json',
        contentType: 'application/json',
        success: function (data) {
            if (callback) {
                callback(data)
            }

        }
    })
    return value
}

function saveRoleHandler(selector, role_name, color_picker, can_post, callback) {
    let role_id = selector[0].selectize.options[selector[0].selectize.getValue()]["id"]
    let old_role_name = selector[0].selectize.getValue()
    let role_color = color_picker.toHEXString()
    let font_color = fColorByBackground(color_picker.toRGBString())
    if (role_name.val() !== '' || role_color !== '#FFFFFF') {
        $.ajax({
            url: '/api/change_user_role',
            method: 'POST',
            data: JSON.stringify({
                role_name: role_name.val(),
                role_color: role_color,
                font_color: font_color,
                role_id: role_id,
                can_post: can_post
            }),
            dataType: 'json',
            contentType: 'application/json',
            success: function (data) {
                selector[0].selectize.updateOption(old_role_name, {
                    role_name: data["role_name"],
                    role_color: data["role_color"],
                    font_color: data["font_color"],
                    id: data["id"],
                    creator: data["creator"]
                })
                $("#roles_selector")[0].selectize.updateOption(old_role_name, {
                    role_name: data["role_name"],
                    role_color: data["role_color"],
                    font_color: data["font_color"],
                    id: data["id"],
                    creator: data["creator"]
                })
                for (const [key, value] of Object.entries(selector[0].selectize.options)) {
                    let element = $(`.role-display-${value["id"]}`)
                    element.css("background", `${value["role_color"]}`)
                    element.css("color", `${value["font_color"]}`)
                }
                if (callback) {
                    callback(data)
                }
            }
        })
    }
}

function fColorByBackground(color) {
    let c_splitted = Array.from(color.split("(")[1].split(")")[0].split(","), x => parseInt(x))
    const brightness = Math.round(((c_splitted[0] * 299) +
        (c_splitted[1] * 587) +
        (c_splitted[2] * 114)) / 1000);
    return (brightness > 125) ? '#000000' : '#FFFFFF';
}