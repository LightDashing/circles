function pinToObject(params) {
    let html = jQuery("html")

    html.on("dragover", function (e) {
        e.preventDefault()
        e.stopPropagation()
        params["obj"].attr("placeholder", "Drag image here")
    })
    html.on("drop", function (e) {
        e.preventDefault();
        e.stopPropagation()
    })

    params["obj"].on("drop", function loadImage(e) {
        e.preventDefault()
        e.stopPropagation()
        let file = e.originalEvent.dataTransfer.files[0];
        if (file.size > 1024 * 1024 * 25) {
            alert("Size of file must be less than 25 megabytes");
            return;
        }
        if (file.type.substring(0, 5) !== 'image') {
            alert("File must be image!");
            return;
        }
        if (FileReader && file && file.size) {
            let fr = new FileReader();
            fr.onload = function loadFile() {
                console.log(params["image_container"])
                pinImage(fr.result,
                    params["image_container"],
                    params["image_class"],
                    params["image_desc_class"],
                    params["add_element_callback"],
                    params["delete_element_callback"])
            }
            fr.readAsDataURL(file);
        }
    })
}

function pinImage(img_src, image_container, image_class, image_desc_class, adding, deletion) {
    let img = document.createElement("img")
    let img_description = document.createElement("span")
    img_description.innerHTML = '&times;';
    if (image_desc_class) {
        img_description.classList.add(image_desc_class)
    }
    img.src = img_src
    img.classList.add(image_class)
    $(image_container).append(img)
    $(image_container).append(img_description)
    if (adding) {
        window.setTimeout(() => adding(img), 150)
    }
    img_description.onclick = function () {
        if (deletion) {
            deletion(img)
        }
        img.remove()
        img_description.remove()
    }
}