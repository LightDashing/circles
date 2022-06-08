function like(post_id, post_type) {
    const like_b = $(`#likes_${post_type}_${post_id}`)
    const likes = $(`#likes_amount_${post_type}_${post_id}`)
    if (like_b.hasClass('liked')) {
        like_b.removeClass('liked')
        like_b.fadeOut('fast', function () {
            like_b.attr('src', '/static/img/like_fill.svg');
            like_b.fadeIn('fast');
        })
        likes.html(parseInt(likes.html()) - 1)
    } else {
        like_b.addClass('liked')
        like_b.fadeOut('fast', function () {
            like_b.attr('src', '/static/img/like_fill_red.svg');
            like_b.fadeIn('fast');
        })
        likes.html(parseInt(likes.html()) + 1)
    }
    $.ajax({
        url: '/api/like',
        method: 'PATCH',
        dataType: 'json',
        contentType: 'application/json',
        data: JSON.stringify({"post_type": post_type, "post_id": parseInt(post_id)}),
        success: function () {
        }
    })
}