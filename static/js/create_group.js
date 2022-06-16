let image_avatar;

$(function onReady() {
    $('textarea').each(function () {
        autosize(this)
    })

    const modal_avatar = document.getElementById("set_avatar")
    const modal_avatar_content = $("#avatar-modal")
    const create_button = $("#create_group")
    $("#avatar_setter").click(function () {
        modal_avatar.style.display = "block";
        $("#avatar-modal").addClass("showModal")
    })
     window.onclick = function (event) {
        if (event.target === modal_avatar) {
            modal_avatar_content.removeClass("showModal")
            modal_avatar_content.addClass("hideModal")
            setTimeout(() => modal_avatar.style.display = "none", 250)
        }}
    $("#close_button").click(function () {
        modal_avatar_content.removeClass("showModal")
        $("#avatar-modal").addClass("hideModal")
        setTimeout(() => modal_avatar.style.display = "none", 250)
    })

    const fileInput = document.getElementById("picture")
    fileInput.addEventListener('change', function () {
        addImage("avatar-modal", "crop-image","new_image", this.files, get_avatar)
    }, false)
    
    create_button.click(function () {
        create_group()
    })
})

function get_avatar(data){
    image_avatar =  data.toDataURL()
    const modal_avatar_content = $("#avatar-modal")
    modal_avatar_content.removeClass("showModal")
    modal_avatar_content.addClass("hideModal")
    setTimeout(() => document.getElementById("set_avatar").style.display = "none", 250)

}

function create_group() {
    let group_name = $("#group_name").val()
    let group_summary = $("#group_summary").val()
    let group_rules = $("#group_rules").val()
    let group_description = $("#group_description").val()
    if (group_summary.length > 128){
        alert(_("Group summary must be less than 128!"))
        return
    }
    if (group_name === "" || group_summary === "" || group_rules === "" || group_description === "") {
        alert(_("One of the fields are empty!"))
    } else {
        $.ajax({
            url: '/create_group',
            method: 'POST',
            dataType: 'json',
            contentType: 'application/json',
            data: JSON.stringify({
                "group_avatar": image_avatar,
                "group_name": group_name,
                "group_rules": group_rules,
                "group_description": group_description,
                "group_summary": group_summary
            }),
            success: function updateModal(data) {
                console.log(data)
                if (data === 2) {
                    alert('This file is too large!')
                }
            }
        });
    }
}