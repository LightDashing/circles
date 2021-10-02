import os
import sys
import uuid
import base64


class FileOperations:
    IMAGES_EXTENSIONS = ['png', 'jpg', 'jpeg', 'jfif', 'pjpeg', 'pjp', 'gif']
    DOCUMENT_EXTENSIONS = ['.docx' '.doc', '.ppt', '.pptx']
    MAX_SIZE = 1024 * 1024 * 20
    SAVE_FOLDER = os.path.join('static', 'user_files')

    @staticmethod
    def get_file_extension(encoded_img):
        extension = encoded_img[encoded_img.find('/') + 1:encoded_img.find(';')]
        return extension

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
            os.mkdir(self.SAVE_FOLDER)
            os.mkdir(os.path.join(self.SAVE_FOLDER, "attach"))
            os.mkdir(os.path.join(self.SAVE_FOLDER, "avatar"))

    def save_image(self, file, filetype: str = 'attach') -> str:
        """This is function to save files, it gets a base64-encoded image file and saves it either in \n
        ../avatar/<userid>/xyz.png or in ../attach/<userid>/xyz.png \n
        Name is generating using uuid1 with userid as node, returns one of the following codes:\n
        0: File was successfully saved and path was written to database\n
        1: File extension is not allowed \n
        2: File is too large \n"""
        if not self.is_allowed(self.get_file_extension(file)):
            return ""
        if not self.get_file_size(file):
            return ""
        image_name = f"{uuid.uuid1(self.userid)}.{self.get_file_extension(file)}"
        filepath = os.path.join(self.SAVE_FOLDER, filetype, str(self.userid), image_name)
        file = file[file.find(',') + 1:]
        if os.path.exists(os.path.join(self.SAVE_FOLDER, filetype, str(self.userid))):
            with open(filepath, 'wb') as img:
                img.write(base64.decodebytes(file.encode()))
        else:
            os.mkdir(os.path.join(self.SAVE_FOLDER, filetype, str(self.userid)))
            with open(filepath, 'wb') as img:
                img.write(base64.decodebytes(file.encode()))
        if filetype == 'avatar':
            old_avatar = self.db.userdata_by(self.userid)['avatar']
            if old_avatar[old_avatar.rfind('\\') + 1:] != 'user-avatar.svg':
                os.remove(old_avatar[old_avatar.find('.') + 1:])
            return os.path.join("..", filepath)
        else:
            return os.path.join("..", filepath)

    def save_document(self, file, userid):
        pass

    def load_object(self, object_id):
        pass
