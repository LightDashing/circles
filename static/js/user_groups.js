function leave_group(group_name, group_id) {
    $.ajax({
            url: '/api/leave_group',
            method: 'DELETE',
            dataType: 'json',
            contentType: 'application/json',
            data: JSON.stringify({
                "group_name": group_name,
            }),
            success: function updateModal(data) {
                $(`#group_${group_id}`).remove()
            }
        });
}