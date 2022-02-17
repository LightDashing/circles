import unittest
import requests


class TestServer(unittest.TestCase):

    def setUp(self) -> None:
        self.session = requests.Session()
        self.session2 = requests.Session()
        self.session3 = requests.Session()
        pass

    def login_user(self) -> (requests.Session, requests.Session):
        r = self.session.post("http://127.0.0.1:5000/login", data={
            "email": "test@test.com",
            "pw1": "testing12345678"
        })
        r2 = self.session2.post("http://127.0.0.1:5000/login", data={
            "email": "test2@test.com",
            "pw1": "testing12345678"
        })
        r3 = self.session3.post("http://127.0.0.1:5000/login", data={
            "email": "test3@test.com",
            "pw1": "testing12345678"
        })
        if r.status_code != 200 or r2.status_code != 200 or r3.status_code != 200:
            raise AssertionError("Can't login into accounts")
        return self.session, self.session2

    def test_01_create_user(self) -> None:
        r = self.session.post("http://127.0.0.1:5000", data={
            "email": "test@test.com",
            "username": "TestUser",
            "pw1": "testing12345678",
            "pw2": "testing12345678"
        })
        r2 = self.session2.post("http://127.0.0.1:5000", data={
            "email": "test2@test.com",
            "username": "TestUser2",
            "pw1": "testing12345678",
            "pw2": "testing12345678"
        })
        r3 = self.session3.post("http://127.0.0.1:5000", data={
            "email": "test3@test.com",
            "username": "TestUser3",
            "pw1": "testing12345678",
            "pw2": "testing12345678"
        })
        if not (r and r2 and r3):
            raise AssertionError("Can't create users accounts")

    def test_02_negative_user(self) -> None:
        r = self.session.post("http://127.0.0.1:5000/login", data={
            "email": "test@test.com",
            "pw1": "test22ing12345678"
        })
        if r.history[-1].url != "http://127.0.0.1:5000/login":
            raise AssertionError("Negative test was false")

    def test_03_add_friend(self) -> None:
        self.login_user()
        r = self.session.post("http://127.0.0.1:5000/api/add_friend", json={
            "name": "TestUser2"
        })
        if not r.json()["success"]:
            raise AssertionError("Can't add friend")

    def test_04_accept_friend(self) -> None:
        self.login_user()
        r2 = self.session2.post("http://127.0.0.1:5000/api/accept_friend", json={
            "name": "TestUser"
        })
        if r2.status_code != 200:
            raise AssertionError("Can't accept friend")
        pass

    def test_05_create_role(self) -> None:
        self.login_user()
        r = self.session.post("http://127.0.0.1:5000/api/create_role", json={
            "role_name": "new role",
            "role_color": "#FFFFFF"
        })
        r2 = self.session2.post("http://127.0.0.1:5000/api/create_role", json={
            "role_name": "new role 2",
            "role_color": "#FFFFFF"
        })
        if not (r.json()["id"] and r2.json()["id"]):
            raise AssertionError(f"Can't create new roles, {r.status_code}")

    def test_06_set_roles(self) -> None:
        self.login_user()
        roles = self.session.get("http://127.0.0.1:5000/api/get_user_roles").json()
        friend_id = self.session.get("http://127.0.0.1:5000/api/get_user_friends").json()[0]["id"]
        r = self.session.post("http://127.0.0.1:5000/api/change_friend_roles", json={
            "roles": roles,
            "friend_id": friend_id
        })
        roles = self.session2.get("http://127.0.0.1:5000/api/get_user_roles").json()
        friend_id = self.session2.get("http://127.0.0.1:5000/api/get_user_friends").json()[0]["id"]
        r2 = self.session2.post("http://127.0.0.1:5000/api/change_friend_roles", json={
            "roles": roles,
            "friend_id": friend_id
        })
        if not (r.json() and r.json()):
            raise AssertionError("Can't set user roles")

    def test_07_get_friend_roles(self) -> None:
        self.login_user()
        friend_id = self.session.get("http://127.0.0.1:5000/api/get_user_friends").json()[0]["id"]
        r = self.session.get(f"http://127.0.0.1:5000/api/get_friend_roles?f={friend_id}")
        friend_id = self.session2.get("http://127.0.0.1:5000/api/get_user_friends").json()[0]["id"]
        r2 = self.session2.get(f"http://127.0.0.1:5000/api/get_friend_roles?f={friend_id}")
        if not (r.json() and r2.json()):
            raise AssertionError("Can't get roles")

    def test_08_create_chat(self) -> None:
        self.login_user()
        r = self.session.post("http://127.0.0.1:5000/api/create_chat", json={
            "users": ["TestUser", "TestUser2", "TestUser3"],
            "chat_name": "TestChat",
            "admin": "TestUser"
        }).json()
        if not r:
            raise AssertionError

    def test_09_send_message(self) -> None:
        self.login_user()
        chats = self.session.post("http://127.0.0.1:5000/api/load_chats").json()
        r = self.session.post("http://127.0.0.1:5000/api/send_message", json={
            "pinned_images": [],
            "chat_id": chats[0]["id"],
            "message": "TestMessage"
        }).json()
        if not r:
            raise AssertionError

    def test_10_get_updates(self) -> None:
        self.login_user()
        updates = self.session.get("http://127.0.0.1:5000/api/update_all").json()
        if len(updates["chats"]) != 1:
            raise AssertionError

    def test_11_failed_message(self) -> None:
        self.login_user()
        r = self.session2.post("http://127.0.0.1:5000/api/send_message", json={
            "pinned_images": [],
            "chat_id": -1,
            "message": "TestMessage"
        }).json()
        if r:
            raise AssertionError

    def test_12_edit_message(self) -> None:
        self.login_user()
        chats = self.session.post("http://127.0.0.1:5000/api/load_chats").json()
        messages = self.session.post("http://127.0.0.1:5000/api/load_messages", json={
            "type": "load",
            "chat_id": chats[0]["id"]
        }).json()
        r = self.session.patch("http://127.0.0.1:5000/api/edit_message", json={
            "chat_id": chats[0]["id"],
            "message_id": messages[0]["id"],
            "new_text": "Edited message!"
        })
        if not r.json():
            raise AssertionError

    def test_13_delete_message(self) -> None:
        self.login_user()
        chats = self.session.post("http://127.0.0.1:5000/api/load_chats").json()
        messages = self.session.post("http://127.0.0.1:5000/api/load_messages", json={
            "type": "load",
            "chat_id": chats[0]["id"]
        }).json()
        r = self.session.delete("http://127.0.0.1:5000/api/delete_message", json={
            "chat_id": chats[0]["id"],
            "message_id": messages[0]["id"]
        })
        if not r.json():
            raise AssertionError

    def test_97_delete_chat(self) -> None:
        self.login_user()
        chats = self.session.post("http://127.0.0.1:5000/api/load_chats").json()
        r = self.session.delete("http://127.0.0.1:5000/api/delete_chat", json={
            "chat_id": chats[0]["id"],
        }).json()
        if not r:
            raise AssertionError

    def test_98_delete_friend(self) -> None:
        self.login_user()
        r = self.session.post("http://127.0.0.1:5000/api/remove_friend", json={
            "name": "TestUser2"
        })
        if not (r.json()["success"]):
            raise AssertionError("Can't delete friend")

    def test_99_delete_user_page(self) -> None:
        self.login_user()
        r = self.session.post("http://127.0.0.1:5000/api/delete_profile")
        r2 = self.session2.post("http://127.0.0.1:5000/api/delete_profile")
        r3 = self.session3.post("http://127.0.0.1:5000/api/delete_profile")
        if not (r.json()["success"] and r2.json()["success"] and r3.json()["success"]):
            raise AssertionError("Can't delete users profiles")
