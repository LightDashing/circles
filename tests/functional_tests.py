import unittest
import requests
import base64
from integrated_tests import TestServer


class TestCasesAll(unittest.TestCase):

    def setUp(self) -> None:
        self.session = requests.Session()
        self.session2 = requests.Session()
        self.test_server = TestServer()
        self.test_server.setUp()

    def change_user_avatar(self, filepath, file_extension, test_result=True):
        self.session, self.session2 = self.test_server.login_user()
        with open(filepath, "rb") as image:
            encoded_image = base64.b64encode(image.read()).decode()
        r = self.session.post("http://127.0.0.1:5000/api/upload_settings", json={
            "image": f"data:image/{file_extension};base64,{encoded_image}"
        })
        if not (r.json() == test_result):
            raise AssertionError(f"{filepath} avatar isn't working")

    def test_01_first(self):
        self.test_server.test_01_create_user()

    def test_02_send_default_jpg(self):
        self.session, self.session2 = self.test_server.login_user()
        self.change_user_avatar("test_01.jpg", "jpg")

    def test_03_send_big_jpg(self):
        self.session, self.session2 = self.test_server.login_user()
        self.change_user_avatar("test_02.jpg", "jpg")

    def test_04_send_dock(self):
        self.session, self.session2 = self.test_server.login_user()
        self.change_user_avatar("test_03.docx", "docx", False)

    def test_05_send_png(self):
        self.session, self.session2 = self.test_server.login_user()
        self.change_user_avatar("test_04.png", "png")

    def test_06_send_dock_file(self):
        self.session, self.session2 = self.test_server.login_user()
        self.change_user_avatar("test_05", "jpg", False)

    def test_07_send_jpg_file(self):
        self.session, self.session2 = self.test_server.login_user()
        self.change_user_avatar("test_06", "jpg")

    def test_99_delete_accounts(self):
        self.session, self.session2 = self.test_server.login_user()
        self.test_server.test_99_delete_user_page()
