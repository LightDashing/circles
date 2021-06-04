function init(name, username) {
    hide_all()
    console.log("testing-one-two-three")
    $.ajax({
        url: '/_check_friend',
        method: 'POST',
        data: JSON.stringify({'name': name}),
        dataType: 'json',
        contentType: 'application/json',
        success: function (data) {
            console.log(data['friend'], data['request'])
            console.log("u1_lvl")
            if (data['friend'] && data['request'] && data['sent_by'] === username) {
                $("#cancel_request").show();
            } else if (!data['friend']) {
                $("#add_friend").show();
            } else if (data['friend'] && !data['request']) {
                $("#remove_friend").show();
            } else if (data['friend'] && data['request'] && data['sent_by'] !== username) {
                $("#accept_request").show()
                $("#decline_request").show()
            }
        },
        error: function (data) {
        }
    });
}

function add_friend(name) {
    $.ajax({
        url: '/_add_friend',
        method: 'POST',
        data: JSON.stringify({'name': name}),
        dataType: 'json',
        contentType: 'application/json',
        success: function () {
            $("#add_friend").hide()
            $("#cancel_request").show()
        }
    });
}

function accept_request(name) {
    $.ajax({
       url: '/_accept_friend',
       method: 'POST',
       data: JSON.stringify({'name': name}),
       dataType: 'json',
       contentType: 'application/json',
       success: function () {
           hide_all()
           $("#remove_friend").show()
       }
    });
}

function remove_friend(name) {
    $.ajax({
        url: '/_remove_friend',
        method: 'POST',
        data: JSON.stringify({'name': name}),
        dataType: 'json',
        contentType: 'application/json',
        success: function () {
            hide_all()
            $("#add_friend").show()
        }
    });
}

function hide_all() {
    $("#add_friend").hide();
    $("#remove_friend").hide();
    $("#decline_request").hide();
    $("#accept_request").hide();
    $("#cancel_request").hide();
}

function publish_post(post_msg, post_attach, view_level, whereid, fromid){
    console.log(whereid)
    $.ajax({
        url: '/_publish_post',
        method: 'POST',
        data: JSON.stringify({"message": post_msg, "attach": post_attach, 
        "view_lvl": view_level, "whereid": whereid, "fromid": fromid}),
        dataType: 'json',
        contentType: 'application/json',
        success: function(){
            
        },
        error: function(){
        }
    })
}

function update_posts(userid){
    
}