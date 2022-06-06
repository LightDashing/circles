let is_anonymous = true;

$(function onReady() {
    const textarea = $("#post-input")
    const anonimity_b = $("#is_anonymous")
    autosize(textarea)

    pinToObject({
        obj: textarea,
        image_container: '#pinned_container',
        image_class: 'pinned-image',
        image_desc_class: 'pinned-image-description'})

    anonimity_b.click(function () {
        if (is_anonymous){
            is_anonymous = false
            anonimity_b.html("public")
        } else{
            is_anonymous = true
            anonimity_b.html("anonymous")
        }
    })

    $("#make_post").click(function () {
        let pinned_images = Array.from($(".pinned-image"));
        for (let i = 0; i < pinned_images.length; i++) {
            pinned_images[i] = pinned_images[i].src;
        }
        if (textarea.val() !== '') {
            publish_post(textarea.val(), parseInt(group_id), is_anonymous, pinned_images);
        }
    })
})

function publish_post(post_msg, group_id, is_anonymous, pinned_images) {
    /* This function creates new post on user pge */
    $.ajax({
        url: '/api/publish_group_post',
        method: 'POST',
        data: JSON.stringify({
            "message": post_msg, "group_id": group_id,
            "is_anonymous": is_anonymous,
            "pinned_images": pinned_images
        }),
        dataType: 'json',
        contentType: 'application/json',
        success: function (data) {
            $.ajax({
                url: '/api/get_group_post', data: `p_id=${data["id"]}`,
                success: function (data) {
                    $(".posts").prepend(data)
                }
            })
        },
        error: function () {
        }
    })
}

function join(group_name) {
    $("#leave_b").show()
    $("#join_b").hide()
    $.ajax({
        url: "/api/join_group",
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
        url: '/api/leave_group',
        method: 'DELETE',
        data: JSON.stringify({"group_name": group_name}),
        dataType: 'json',
        contentType: 'application/json'
    })
}