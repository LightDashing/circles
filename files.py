import os
import uuid
import base64
from database import DataBase, OpenConnectionToBD


class FileOperations:
    IMAGES_EXTENSIONS = ['png', 'jpg', 'jpeg', 'jfif', 'pjpeg', 'pjp']
    DOCUMENT_EXTENSIONS = ['.docx' '.doc', '.ppt', '.pptx']
    SAVE_FOLDER = os.path.join('static', 'user_files')

    @staticmethod
    def get_file_extension(encoded_img):
        extension = encoded_img[encoded_img.find('/') + 1:encoded_img.find(';')]
        return extension

    def is_allowed(self, file_extension: str) -> bool:
        if file_extension in self.IMAGES_EXTENSIONS or file_extension in self.DOCUMENT_EXTENSIONS:
            return True
        else:
            return False

    def __init__(self, userid: int):
        print(self.SAVE_FOLDER)
        self.userid = userid
        self.db = DataBase()
        if not os.path.exists(self.SAVE_FOLDER):
            os.mkdir(self.SAVE_FOLDER)
            os.mkdir(os.path.join(self.SAVE_FOLDER, "attach"))
            os.mkdir(os.path.join(self.SAVE_FOLDER, "avatar"))

    def allowed_image(self, filename):
        return self.get_file_extension(filename) in self.IMAGE_EXTENSIONS

    def save_image(self, file, filetype: str = 'attach'):
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
            with OpenConnectionToBD(self.db):
                old_avatar = self.db.userdata_by_name(self.db.get_name_by_userid(self.userid))['avatar']
                os.remove(old_avatar[old_avatar.find('.') + 1:])
                self.db.change_avatar(self.userid, os.path.join("..", filepath))

    def save_document(self, file, userid):
        pass

    def load_object(self, object_id):
        pass
