let usernames = []
let admin = null
let moderators = []
let chat_name = null

function init(friends_count) {
    admin = current_username
    for (let i = 0; i < friends_count; i++) {
        bind_button(i)
        bind_checkbox(i)
    }
    $("#create_chat").click(function () {
        create_chat()
    })
}

function add_friend(friend_name) {
    usernames.push(friend_name)
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
        alert("Add friends to chat!")
    } else {
        console.log(chat_name)
        $.ajax({
            url: '/user/create_chat',
            method: 'POST',
            data: JSON.stringify({"users":usernames, "admin":admin, "moderators":moderators, "chat_name": chat_name}),
            dataType: 'json',
            contentType: 'application/json',
            success: function(){
                
            }
        })
    }
}