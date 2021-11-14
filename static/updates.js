// TODO: Важно! Проверять все обновления в режиме реального времени, в том числе посты на странице пользователя, сообщения
//  и заявки в друзья
let notification_sound
$(function onReady() {
    notification_sound = new Audio('/static/audio/notification.mp3')
    setInterval(() => checkAllUpdates(), 5000)
    stillAlive()
    setInterval(() => stillAlive(), 600000)
})

function checkAllUpdates() {
    $.ajax({
        url: '/api/update_all',
        method: 'GET',
        success: function updateAll(data) {
            if (data['messages'] !== 0 || data['friends'] !== 0) {
                $("#settings").val()
                notification_sound.play().then(r => function () {
                    console.log('error')
                }, reason => function () {
                    console.log("fwfa")
                    //TODO: придумать что-нибудь с автовоспроизведением
                })
            }
        }
    })
}

function stillAlive() {
    $.get('/api/online')
}