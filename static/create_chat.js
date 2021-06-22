var usernames = []
var admin = null
var moderators = []
var chatname = null

function init(username, friendscount){
    usernames.push(username)
    admin = username
    console.log(friendscount)
    for (i = 1; i < friendscount + 1; i++){
        bind_button(i)
        bind_checkbox(i)
    }
    $("#create_chat").click(function (){
        create_chat()
    })
}

function add_friend(friendname){
    usernames.push(friendname)
}


function remove_friend(friendname){
    for (i = 0; i < usernames.length; i++){
        if (usernames[i] == friendname){
            usernames.splice(i, 1)
        }
    }
}

function add_moderator(friendname){
    moderators.push(friendname)
}

function remove_moderator(friendname){
    for (i = 0; i < moderators.length; i++){
        if (moderators[i] == friendname){
            moderators.splice(i, 1)
        }
    }
}

function bind_button(number){
    $("#add_friend_"+number).click(function (){
        add_friend($("#friend_"+number).html())
        $("#remove_friend_"+number).show()
        $("#add_friend_"+number).hide()
        $("#is_moderator_"+number).show()
    })
    $("#remove_friend_"+number).hide()
    $("#is_moderator_"+number).hide()
    $("#remove_friend_"+number).click(function(){
        remove_friend($("#friend_"+number).html())
        $("#remove_friend_"+number).hide()
        $("#add_friend_"+number).show()
        $("#is_moderator_"+number).hide()
        $("#is_moderator_"+number).prop("checked", false)
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
    chatname = $("#chat_name").val()
    if (chatname == ''){
        alert("Enter chat name!")
    } else {
        console.log(chatname)
        $.ajax({
            url: '/user/create_chat',
            method: 'POST',
            data: JSON.stringify({"users":usernames, "admin":admin, "moderators":moderators, "chatname": chatname}),
            dataType: 'json',
            contentType: 'application/json',
            success: function(){
                
            }
        })
    }
}