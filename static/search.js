let search_list = {};
let dropdown;

$(function initSearch() {
    const $search_input = $("#search_users");
    dropdown = document.getElementById("dropdown-search")
    setTimeout(() => searchInit(), 250)

    $search_input.on('keyup', function (event) {
        if ($search_input.val() !== '') {
            let query = $search_input.val()
            findDropdown(query)
            searchUsers(query)
        }
    })

    $search_input.on('focus', function () {
        dropdown.style.display = "block";
    })

    $search_input.on('focusout', function () {
        setTimeout(() => {
            dropdown.style.display = "none";
        }, 250)
    })
})

function searchUsers(query) {
    $.ajax({
        url: '/api/search',
        method: 'POST',
        dataType: 'json',
        contentType: 'application/json',
        data: JSON.stringify({"search_input": query}),
        success: function (data) {
            data.forEach(function appendDropdown(element) {
                if (element['group_name'] !== undefined) {
                     if (!(`group_${element['id']}` in search_list)) {
                        search_list[`group_${element['id']}`] = element;
                        let drop_element = createDropdownElement(element);
                        dropdown.append(drop_element);
                    }
                } else {
                    if (!(`user_${element['id']}` in search_list)) {
                        search_list[`user_${element['id']}`] = element;
                        let drop_element = createDropdownElement(element);
                        dropdown.append(drop_element);
                    }
                }
            })
        }
    })
}

function searchInit() {
    $.ajax({
        url: '/api/get_user_friends',
        success: function (data) {
            data.forEach(function createDropdown(element) {
                search_list[`user_${element['id']}`] = element;
                let drop_element = createDropdownElement(element)
                dropdown.append(drop_element)
            })
        }
    })
}

function findDropdown(text) {
    for (const [key, value] of Object.entries(search_list)) {
        if (value["group_name"] !== undefined){
            if (value['group_name'].toUpperCase().indexOf(text.toUpperCase()) > -1){

            } else{
                $(`#drop_group_${value['id']}`).remove()
                delete search_list[key]
            }
        } else if (value['username'].toUpperCase().indexOf(text.toUpperCase()) > -1) {

        } else {
            $(`#drop_user_${value['id']}`).remove()
            delete search_list[key]
        }
    }
}

function createDropdownElement(element) {
    let drop_element = document.createElement("div");
    drop_element.classList.add("dropdown-profile")
    if (element["group_name"] !== undefined){
        drop_element.onclick = function () {
            location.href = `/groups/${element['group_name']}`
        }
        drop_element.id = `drop_group_${element['id']}`
        drop_element.innerHTML = ` <img src="${element['avatar']}" alt="user_avatar" class="dropdown-profile-avatar">
                                        <div class="dropdown-profile-description">
                                            <span>${element['group_name']}</span>
                                            <span class="dropdown-profile-description-status">${_('Subscribers:')} ${element["users_amount"]}</span>
                                            <span class="dropdown-profile-description-type">${_("Group")}</span>
                                        </div>`
    } else {
        drop_element.onclick = function () {
            location.href = `/users/${element['username']}`
        }
        drop_element.id = `drop_user_${element['id']}`
        let user_type = _('common user')
        if (element['id'] === current_userid) {
            user_type = _("it's you")
        }
        drop_element.innerHTML = ` <img src="${element['avatar']}" alt="user_avatar" class="dropdown-profile-avatar">
                                        <div class="dropdown-profile-description">
                                            <span>${element['username']}</span>
                                            <span class="dropdown-profile-description-status">${_("online")}</span>
                                            <span class="dropdown-profile-description-type">${user_type}</span>
                                        </div>`
    }
    return drop_element
}

function addDropdownValues() {

}