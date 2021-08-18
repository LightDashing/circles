let search_list = {};
let dropdown;

$(function initSearch() {
    const $search_input = $("#search_users");
    dropdown = document.getElementById("dropdown-search")
    searchInit()

    $search_input.on('keyup', function () {
        let query = $search_input.val()
        searchUsers(query)
    })

    $search_input.on('focus', function () {
        dropdown.style.display = "block";
    })

    $search_input.on('focusout', function () {
        dropdown.style.display = "none";
    })
})

function searchUsers(query) {
    $.ajax({
        url: '/search',
        method: 'POST',
        dataType: 'json',
        contentType: 'application/json',
        data: JSON.stringify({"search_input": query}),
        success: function (data) {
            data.forEach(function appendDropdown() {

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
                search_list[element['id']] = element
                let drop_element = document.createElement("div")
                drop_element.classList.add("dropdown-profile")
                drop_element.onclick = function () {
                    location.href = `/users/${element['username']}`
                }
                drop_element.innerHTML = `<div class="dropdown-profile" onclick="location.href=''">
                                        <img src="${element['avatar']}" alt="user_avatar" class="dropdown-profile-avatar">
                                        <div class="dropdown-profile-description">
                                            <span>${element['username']}</span>
                                            <span class="dropdown-profile-description-status">online</span>
                                            <span class="dropdown-profile-description-type">common user</span>
                                        </div>
                                    </div>`
                dropdown.append(drop_element)
                console.log(search_list)
            })
        }
    })
}

function findDropdown(text){

}

function addDropdownValues() {

}