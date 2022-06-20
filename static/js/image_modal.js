function showModalImage(modal_window, modal_window_content, image_src, div_id, image_date, username, user_avatar) {
    modal_window = $(`#${modal_window}`)
    modal_window_content = $(`#${modal_window_content}`)

    renderModalImage(image_src, div_id, image_date, username, user_avatar)
    html.css("overflow", "hidden")
    modal_window.show()
    modal_window_content.addClass("showModal")
}

function hideModalImage(modal_window, modal_window_content) {
    html.css("overflow", "auto")
    modal_window_content.removeClass("showModal")
    modal_window_content.addClass("hideModal")
    setTimeout(() => modal_window.hide(), 250)
}

function renderModalImage(image_src, div_id, image_date, username, user_avatar) {
    console.log(div_id)
    let parent_div = $(`#${div_id}`)
    parent_div.html("")
    image_date = image_date.toString()
    image_date = image_date.substring(0, image_date.lastIndexOf(":"))
    let element = `<div class="modal-content">
    <div class="modal-content-image">
        <img src="${image_src}" alt="image big">
    </div>
    <div class="modal-content-info">
        <img src="${user_avatar}" alt="user_avatar">
        <div class="modal-content-text">
            <span>${username}</span>
            <span>${image_date}</span>
        </div>
<!--        TOOD: Add like button-->
    </div>
                </div>`
//     let element = `<img src="${image_src}" alt="image big">`
    parent_div.append(element)
}