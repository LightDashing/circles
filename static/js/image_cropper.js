const IMAGES_EXTENSIONS = ['png', 'jpg', 'jpeg', 'jfif', 'pjpeg', 'pjp']

function getFileExtension(filename) {
    return filename.split('.').pop();
}

function addImage(modal_content_id, cropper_id, image_id, files, send_function) {
    const fileList = files;
    let modal_content = document.getElementById(`${modal_content_id}`);
    if (!IMAGES_EXTENSIONS.includes(getFileExtension(fileList[0].name))) {
        console.log("File isn't image!")
        return
    }
    if ($(`#${image_id}`).length !== 0) {
        let cropper_div = document.getElementById(`${cropper_id}`);
        cropper_div.innerHTML = '';
    }
    modal_content.style.width = '60%';
    modal_content.style.height = '600px';
    setTimeout(() => makeImage(fileList, image_id, cropper_id, send_function), 290)
}

function makeImage(files, image_id, cropper_id, send_function) {
    function createCropper() {
        let image = $(`#${image_id}`)
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
    $(`#${cropper_id}`).append(image)
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
        send_function(upload_image)
    })
}