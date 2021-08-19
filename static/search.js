let search_list = {};
let dropdown;

$(function initSearch() {
    const $search_input = $("#search_users");
    dropdown = document.getElementById("dropdown-search")
    searchInit()

    $search_input.on('keyup', function (event) {
        console.log(event.key)
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
        }, 100)
    })
})

function searchUsers(query) {
    console.log(query)
    $.ajax({
        url: '/search',
        method: 'POST',
        dataType: 'json',
        contentType: 'application/json',
        data: JSON.stringify({"search_input": query}),
        success: function (data) {
            console.log(data)
            data.forEach(function appendDropdown(element) {
                if (!(element['id'] in search_list)) {
                    search_list[element['id']] = element;
                    let drop_element = createDropdownElement(element);
                    dropdown.append(drop_element);
                }
            })
        }
    })
}

function searchInit() {
    $.ajax({
        url: '/_get_user_friends',
        method: 'POST',
        success: function (data) {
            data.forEach(function createDropdown(element) {
                search_list[element['id']] = element;
                let drop_element = createDropdownElement(element)
                dropdown.append(drop_element)
            })
        }
    })
}

function findDropdown(text) {
    for (const [key, value] of Object.entries(search_list)) {
        if (value['username'].toUpperCase().indexOf(text.toUpperCase()) > -1) {

        } else {
            $(`#drop_${value['id']}`).remove()
            delete search_list[key]
        }
    }
}

function createDropdownElement(element) {
    let drop_element = document.createElement("div");
    drop_element.classList.add("dropdown-profile")
    drop_element.onclick = function () {
        location.href = `/users/${element['username']}`
    }
    drop_element.id = `drop_${element['id']}`
    let user_type = 'common user'
    if (element['id'] === current_userid) {
        user_type = "it's you"
    }
    drop_element.innerHTML = ` <img src="${element['avatar']}" alt="user_avatar" class="dropdown-profile-avatar">
                                        <div class="dropdown-profile-description">
                                            <span>${element['username']}</span>
                                            <span class="dropdown-profile-description-status">online</span>
                                            <span class="dropdown-profile-description-type">${user_type}</span>
                                        </div>`
    return drop_element
}

function addDropdownValues() {

}