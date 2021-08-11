const IMAGES_EXTENSIONS = ['png', 'jpg', 'jpeg', 'jfif', 'pjpeg', 'pjp']

function send_avatar(data) {
    let base64img = data.toDataURL()
    $.ajax({
        url: '/user/_upload_settings',
        method: 'POST',
        dataType: 'json',
        contentType: 'application/json',
        data: JSON.stringify({"image": base64img}),
        success: function updateModal(data) {
            console.log(data)
        }
    });
}

function send_settings(form) {
    $.ajax({
        url: '/user/_upload_settings',
        method: 'POST',
        processData: false,
        contentType: false,
        data: form,
        success: function displayErrors(data) {
            let msg = document.createElement('a');
            if (data['unknown_error']) {
                msg.innerText = 'Some unknown error occurred!';
                msg.classList.add('error-message');
                $(".unknown-error").append(msg);
            }
            if (data['u_name_r'] === 1) {
                msg.innerText = 'User with that username already exist!';
                msg.classList.add('error-message');
                $(".username-error").append(msg);
            } else if (data['u_name_r'] === 2) {
                msg.innerText = 'Username length is incorrect!';
                msg.classList.add('error-message');
                $(".username-error").append(msg);
            }
            if (data['u_email_r'] === 1) {
                msg.innerText = "Email isn't valid!";
                msg.classList.add('error-message');
                $(".email-error").append(msg)
            } else if (data['u_email_r'] === 2) {
                msg.innerText = "That email already belongs to someone!";
                msg.classList.add('error-message');
                $(".email-error").append(msg)
            }
        }
    })
}

function getFileExtension(filename) {
    return filename.split('.').pop();
}

function addImage() {
    const fileList = this.files;
    let modal_content = document.getElementById('avatar-modal');
    if (!IMAGES_EXTENSIONS.includes(getFileExtension(fileList[0].name))) {
        console.log("File isn't image!")
        return
    }
    if ($("#new_image").length !== 0) {
        let cropper_div = document.getElementById('crop-image');
        cropper_div.innerHTML = '';
    }
    modal_content.style.width = '60%';
    modal_content.style.height = '600px';
    setTimeout(() => makeImage(fileList), 290)
}

function makeImage(files) {
    function createCropper() {
        let image = $("#new_image")
        image.cropper({
            aspectRatio: 1,
            preview: ".preview",
            viewMode: 3,
            crop: function (event) {
            }
        });
        return image
    }

    const image = document.createElement("img")
    image.id = 'new_image'
    $("#crop-image").append(image)
    const reader = new FileReader();
    let cropper;
    if (FileReader && files && files.length) {
        let fr = new FileReader();
        fr.onload = function () {
            image.src = fr.result;
            let img = createCropper()
            cropper = img.data('cropper')
        }
        fr.readAsDataURL(files[0]);
    }

    let crop_button = $("#crop_button")
    crop_button.show()

    let move_button = $("#move_button")
    move_button.show()

    let rotate_left = $("#rotate_90_left")
    rotate_left.show()

    let rotate_right = $("#rotate_90_right")
    rotate_right.show()

    let save_image = $("#save_image")
    save_image.show()

    // let cropper = $image.data('cropper');
    crop_button.click(function () {
        cropper.setDragMode('crop')
    })
    move_button.click(function () {
        cropper.setDragMode('move')
    })
    rotate_right.click(function () {
        cropper.rotate(-90)
    })
    rotate_left.click(function () {
        cropper.rotate(90)
    })
    save_image.click(function () {
        const upload_image = cropper.getCroppedCanvas({maxWidth: 4096, maxHeight: 4096})
        send_avatar(upload_image)
        console.log(upload_image)
    })
}