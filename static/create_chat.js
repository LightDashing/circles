let usernames = [current_username]
let admin = null
let moderators = []
let chat_name = null
let chat_avatar = null

function init(friends_count) {
    admin = current_username
    friends_count = $(".create-chat-friend").length
    for (let i = 0; i < friends_count; i++) {
        bind_button(i)
        bind_checkbox(i)
    }
    $("#create_chat").click(function () {
        create_chat()
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

    const modal_avatar = document.getElementById("set_avatar")
    const modal_avatar_content = $("#avatar-modal")
    $("#set_chat_avatar").click(function () {
        modal_avatar.style.display = "block";
        $("#avatar-modal").addClass("showModal")
    })

    const fileInput = document.getElementById("picture")
    fileInput.addEventListener('change', function () {
        addImage("avatar-modal", "crop-image","new_image", this.files, get_avatar)
    }, false)

}

function add_friend(friend_name) {
    usernames.push(friend_name)
}

function get_avatar(data){
    chat_avatar =  data.toDataURL()
    const modal_avatar_content = $("#avatar-modal")
    modal_avatar_content.removeClass("showModal")
    modal_avatar_content.addClass("hideModal")
    setTimeout(() => document.getElementById("set_avatar").style.display = "none", 250)

}

function remove_friend(friend_name) {
    for (let i = 0; i < usernames.length; i++) {
        if (usernames[i] === friend_name) {
            usernames.splice(i, 1)
        }
    }
}

function add_moderator(friend_name) {
    moderators.push(friend_name)
}

function remove_moderator(friend_name) {
    for (let i = 0; i < moderators.length; i++) {
        if (moderators[i] === friend_name) {
            moderators.splice(i, 1)
        }
    }
}

function bind_button(number){
    let add_friend_b = $("#add_friend_"+number)
    let remove_friend_b =  $("#remove_friend_"+number)
    let is_moderator_c = $("#is_moderator_"+number)
    let friend = $("#friend_"+number).html()
    add_friend_b.click(function (){
        add_friend(friend)
        remove_friend_b.show()
        add_friend_b.hide()
        is_moderator_c.show()
    })
    remove_friend_b.hide()
    is_moderator_c.hide()
    remove_friend_b.click(function(){
        remove_friend(friend)
        remove_moderator(friend)
        remove_friend_b.hide()
        add_friend_b.show()
        is_moderator_c.hide()
        is_moderator_c.prop("checked", false)
    })
}

function bind_checkbox(number){
    $("#is_moderator_"+number).change(function (){
        if(this.checked){
            add_moderator($("#friend_"+number).html())
        } else {
            remove_moderator($("#friend_"+number).html())
        }
    })
}

function create_chat(){
    chat_name = $("#chat_name").val()
    if (chat_name === ''){
        alert("Enter chat name!")
    } else if (usernames.length < 2){
        // TODO: здесь нужно поменять на кнопку "перейти в диалог"
        alert("Add more friends to chat!")
    } else {
        console.log(chat_name)
        $.ajax({
            url: '/api/create_chat',
            method: 'POST',
            data: JSON.stringify({
                "users": usernames,
                "admin": admin,
                "moderators": moderators,
                "chat_name": chat_name,
                "avatar": chat_avatar
            }),
            dataType: 'json',
            contentType: 'application/json',
            success: function (data) {
                location.href = `${window.location.origin}/chat/${data}`
            }
        })
    }
}