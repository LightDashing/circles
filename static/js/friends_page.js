$(function () {
    window.addEventListener('beforeunload', function (e) {
        navigator.sendBeacon('/api/test', `text=kek`)
    })
    let friends_selectors = Array.from($(".friend-selector"))
    friends_selectors.forEach(function (element) {
        element = $(element)
        element.selectize({
            plugins: ["remove_button"],
            preload: true,
            valueField: "role_name",
            labelField: "role_name",
            searchField: ["role_name"],
            load: function (query, callback) {
                $.ajax({
                    url: '/api/get_friend_roles', data: `f=${element.attr("id").replace("f", "")}`,
                    success: function (data) {
                        console.log(data)
                        callback(data)
                        element[0].selectize.setValue(data.reduce(function filterRoles(result, role) {
                            if (role["is_active"]) {
                                result.push(role["role_name"])
                            }
                            return result
                        }, []))
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
            }
        });
    })
    let friends_buttons = Array.from($(".save-friend-role"))
    friends_buttons.forEach(function (element) {
        element.onclick = function () {
            let friend_id = this.id.split("fs")[1]
            let selector = $(`#f${friend_id}`)[0].selectize
            let roles = $(`#f${friend_id}`)[0].selectize.getValue()
            let choosen_arr = []
            roles.forEach(function (elem) {
                choosen_arr.push(selector.options[elem])
            })
            $.ajax({
                url: "/api/change_friend_roles",
                method: "POST",
                data: JSON.stringify({friend_id: friend_id, roles: choosen_arr}),
                dataType: 'json',
                contentType: 'application/json',
                success: function (data) {
                }
            })
        }
    })
})