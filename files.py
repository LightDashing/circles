import os
import sys
import uuid
import base64
import io
from PIL import Image


class InvalidImageError(Exception):  # В будущем нужно будет перенести все ошибки в отдельный файл, пока так
    """Image was invalid and can't be loaded with PIL"""


class FileOperations:
    IMAGES_EXTENSIONS = ['png', 'jpg', 'jpeg', 'jfif', 'pjpeg', 'pjp', 'gif']
    DOCUMENT_EXTENSIONS = ['.docx' '.doc', '.ppt', '.pptx']
    MAX_SIZE = 1024 * 1024 * 20
    SAVE_FOLDER = os.path.join('static', 'user_files')

    @staticmethod
    def get_file_extension(encoded_img):
        extension = encoded_img[encoded_img.find('/') + 1:encoded_img.find(';')]
        return extension

    @staticmethod
    def compress_image(decoded_img):
        try:
            image = Image.open(io.BytesIO(decoded_img))
            image = image.convert("RGB")
        except IOError:
            raise InvalidImageError
        if image.size[0] < 10 or image.size[1] < 10:
            raise InvalidImageError
        elif image.size[0] < 100 or image.size[1] < 100:  # Ресайз изображения с целью повышения его разрешения
            coefficient = min(image.size[0], image.size[1])  # Если оно слишком маленькое
            coefficient = 100 // coefficient
            image = image.resize((int(image.size[0] * coefficient), int(image.size[1] * coefficient)),
                                 Image.ANTIALIAS)
        elif image.size[0] <= 1000 or image.size[1] <= 1000:
            return image
        else:
            image = image.resize((int(image.size[0] // 1.5), int(image.size[1] // 1.5)), Image.ANTIALIAS)
        return image

    def get_file_size(self, encoded_img):
        if sys.getsizeof(encoded_img) > self.MAX_SIZE:
            return False
        else:
            return True

    def is_allowed(self, file_extension: str) -> bool:
        if file_extension in self.IMAGES_EXTENSIONS or file_extension in self.DOCUMENT_EXTENSIONS:
            return True
        else:
            return False

    def __init__(self, userid: int):
        self.userid = userid
        if not os.path.exists(self.SAVE_FOLDER):
            os.makedirs(self.SAVE_FOLDER)
            os.makedirs(os.path.join(self.SAVE_FOLDER, "attach"))
            os.makedirs(os.path.join(self.SAVE_FOLDER, "avatar"))
            os.makedirs(os.path.join(self.SAVE_FOLDER, "group"))

    def save_user_image(self, file, filetype: str = 'attach', old_avatar: str = None) -> str:
        """This is function to save files, it gets a base64-encoded image file and saves it either in \n
        ../avatar/<userid>/xyz.png or in ../attach/<userid>/xyz.png \n
        Name is generating using uuid1 with userid as node, returns one of the following codes:\n
        0: File was successfully saved and path was written to database\n
        1: File extension is not allowed \n
        2: File is too large \n"""
        if not self.is_allowed(self.get_file_extension(file)):
            return ""
        image_name = f"{uuid.uuid1(self.userid)}.{self.get_file_extension(file)}"
        filepath = os.path.join(self.SAVE_FOLDER, filetype, str(self.userid), image_name)
        file = file[file.find(',') + 1:]
        image = base64.decodebytes(file.encode())
        try:
            image = self.compress_image(image)
        except InvalidImageError:
            return ""
        if os.path.exists(os.path.join(self.SAVE_FOLDER, filetype, str(self.userid))):
            image.save(filepath, optimize=True, quality=50)
        else:
            os.makedirs(os.path.join(self.SAVE_FOLDER, filetype, str(self.userid)))
            image.save(filepath, optimize=True, quality=50)
        if os.stat(filepath).st_size > self.MAX_SIZE:
            os.remove(filepath)
            return ""
        if filetype == 'avatar':
            if old_avatar:
                if os.path.basename(old_avatar) != 'user-avatar.svg':
                    if old_avatar.find("\\") != -1:
                        os.remove(old_avatar[old_avatar.find("\\") + 1:])
                    else:
                        os.remove(old_avatar)
            return os.path.join("..", filepath)
        else:
            return os.path.join("..", filepath)

    def save_document(self, file, userid):
        pass

    def load_object(self, object_id):
        pass

    def save_group_image(self, file, group_id: int, filetype: str = "group_attach", old_avatar: str = None) -> str:

        if not self.is_allowed(self.get_file_extension(file)):
            return ""
        print(group_id)
        image_name = f"{uuid.uuid1(group_id)}.{self.get_file_extension(file)}"
        filepath = os.path.join(self.SAVE_FOLDER, filetype, str(group_id), image_name)
        file = file[file.find(',') + 1:]
        image = base64.decodebytes(file.encode())
        try:
            image = self.compress_image(image)
        except InvalidImageError:
            return ""

        if os.path.exists(os.path.join(self.SAVE_FOLDER, filetype, str(group_id))):
            image.save(filepath, optimize=True, quality=50)
        else:
            os.makedirs(os.path.join(self.SAVE_FOLDER, filetype, str(group_id)))
            image.save(filepath, optimize=True, quality=50)
        if os.stat(filepath).st_size > self.MAX_SIZE:
            os.remove(filepath)
            return ""
        if filetype == 'group_avatar':
            if old_avatar:
                if os.path.basename(old_avatar) != 'peoples.svg':
                    if old_avatar.find("\\") != -1:
                        os.remove(old_avatar[old_avatar.find("\\") + 1:])
                    else:
                        os.remove(old_avatar)
            return os.path.join("..", filepath)
        else:
            return os.path.join("..", filepath)
