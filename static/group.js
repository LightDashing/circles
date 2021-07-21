function join(group_name) {
    $("#leave_b").show()
    $("#join_b").hide()
    $.ajax({
        url: "/_join_group",
        method: 'POST',
        data: JSON.stringify({"group_name": group_name}),
        dataType: 'json',
        contentType: 'application/json'
    })
}

function leave(group_name) {
    $("#join_b").show()
    $("#leave_b").hide()
    $.ajax({
        url: '/_leave_group',
        method: 'POST',
        data: JSON.stringify({"group_name": group_name}),
        dataType: 'json',
        contentType: 'application/json'
    })
}