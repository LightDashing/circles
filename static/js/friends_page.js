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
                        style="background: ${item["role_color"]}80; border: none; border-radius: 15px;
                        text-shadow: 0 1px 0 rgba(0, 51, 83, 0.3); color: ${item["font_color"]}"
                            id="edit_${item["id"]}">${item["role_name"]}</div>`
                }
            }
        });
    })
})