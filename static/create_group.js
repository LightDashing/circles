function create_group(group_name, group_description, group_rules, group_tags) {
    console.log(group_name, group_description, group_rules)
    $.ajax({
        url: '/create/group',
        method: 'POST',
        data: JSON.stringify({"group_name": group_name, "group_description": group_description,
            "group_rules": group_rules, "group_tags": null}),
        dataType: 'json',
        contentType: 'application/json'
    })
}

