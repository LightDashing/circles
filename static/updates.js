// import Cookies from '/static/node_modules/js-cookie/dist/js.cookie.min'
let notification_sound
$(function onReady() {
    notification_sound = new Audio('/static/audio/notification.mp3')
    StartTimers()
    const message_b = $('#messages')
    const friends_b = $("#friends")
    if (Cookies.get("new_messages") && Cookies.get("new_messages") !== "0") {
        message_b.html(`<i class="material-icons">mail</i> Messages +${Cookies.get("new_messages")}`)
    } else {
        message_b.html(`<i class="material-icons">mail</i> Messages`)
    }
    if (Cookies.get("new_friends") && Cookies.get("new_friends") !== "0") {
        friends_b.html(`<i class="material-icons">people</i> Friends +${Cookies.get("new_friends")}`)
    } else {
        friends_b.html(`<i class="material-icons">people</i> Friends`)
    }
})

function StartTimers() {
    setInterval(() => checkAllUpdates(), 5000)
    stillAlive()
    setInterval(() => stillAlive(), 600000)
}

function checkAllUpdates() {
    $.ajax({
        url: '/api/update_all',
        method: 'GET',
        success: function updateAll(data) {
            let playNotification = false
            if (data["chats"].length > 0 || data["friends"] !== 0) {
                data["chats"].forEach(function (elem) {
                    if (!elem["is_notified"]) {
                        playNotification = true
                    }
                })
                if (data["new_friends"]) {
                    playNotification = true
                }
                if (data["chats"].length > 0) {
                    const messages_button = $("#messages")
                    messages_button.html(`
                     <i class="material-icons">mail</i> Messages +${data["chats"].length}`)
                    Cookies.set("new_messages", data["chats"].length)
                }
                if (data["friends"] !== 0) {
                    const friends_button = $("#friends")
                    friends_button.html(`
                     <i class="material-icons">people</i> Friends +${data["friends"]}`)
                    Cookies.set("new_friends", 0)
                }

            } else {
                Cookies.set("new_messages", 0)
                $("#messages").html(`<i class="material-icons">mail</i> Messages`)
                $("#friends").html(`<i class="material-icons">people</i> Friends`)
                Cookies.set("new_friends", 0)
            }
            if (playNotification) {
                notification_sound.play().then(r => function () {
                    console.log('error')
                }, reason => function () {
                    //TODO: придумать что-нибудь с автовоспроизведением
                })
            }
        }
    })
}

function setMessages(value) {
    if (value > 0) {
        $("#messages").html(`<i class="material-icons">mail</i> Messages +${value}`)
    } else {
        $("#messages").html(`<i class="material-icons">mail</i> Messages`)
    }
}

function setFriends(value) {
    if (value > 0) {
        $("#friends").html(`<i class="material-icons">people</i> Friends +${value}`)
    } else {
        $("#friends").html(`<i class="material-icons">people</i> Friends`)
    }
}

function stillAlive() {
    $.get('/api/online')
}