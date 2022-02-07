import unittest
from database import DBC
import datetime


class TestDataBase(unittest.TestCase):

    def setUp(self) -> None:
        self.DBC = DBC

    def test_01_user_creation(self):
        self.assertEqual(self.DBC.add_user("TestUser", "test_user@test.com", "testingtesting123456"), True)
        self.assertEqual(self.DBC.add_user("TestUser2", "test_user2@test.com", "testingtesting123456"), True)
        self.assertEqual(self.DBC.add_user("TestUser3", "test_user3@test.com", "testingtesting123456"), True)

    def test_02_login_user(self):
        self.assertEqual(self.DBC.login_user("test_user@test.com", "testingtesting123456"), True)
        self.assertEqual(self.DBC.login_user("test_user@test.com", "123456"), False)

    def test_03_friend_adding(self):
        self.assertEqual(self.DBC.add_friend(self.DBC.get_userid_by_name("TestUser"),
                                             self.DBC.get_userid_by_name("TestUser2")), True)
        self.assertEqual(self.DBC.add_friend(self.DBC.get_userid_by_name("TestUser2"),
                                             self.DBC.get_userid_by_name("TestUser3")), True)

    def test_04_friend_accepting(self):
        self.assertEqual(self.DBC.accept_request(self.DBC.get_userid_by_name("TestUser2"),
                                                 self.DBC.get_userid_by_name("TestUser")), True)
        self.assertEqual(self.DBC.accept_request(self.DBC.get_userid_by_name("TestUser3"),
                                                 self.DBC.get_userid_by_name("TestUser2")), True)

    def test_05_is_friend(self):
        friend = self.DBC.is_friend(self.DBC.get_userid_by_name("TestUser"),
                                    self.DBC.get_userid_by_name("TestUser2"))
        if not friend:
            raise AssertionError("Friend's isn't working")

    def test_06_create_role(self):
        role_1 = self.DBC.create_role("role_1", "#FFFFFF", self.DBC.get_userid_by_name("TestUser"))
        role_2 = self.DBC.create_role("role_2", "#FFFFFF", self.DBC.get_userid_by_name("TestUser2"))
        if not (role_1 and role_2):
            raise AssertionError("Roles doesn't works")

    def test_07_append_role(self):
        roles = self.DBC.get_roles(self.DBC.get_userid_by_name("TestUser"))
        self.assertEqual(self.DBC.change_friend_roles(self.DBC.get_userid_by_name("TestUser"),
                                                      self.DBC.get_userid_by_name("TestUser2"), roles), True)
        roles = self.DBC.get_roles(self.DBC.get_userid_by_name("TestUser2"))
        self.assertEqual(self.DBC.change_friend_roles(self.DBC.get_userid_by_name("TestUser2"),
                                                      self.DBC.get_userid_by_name("TestUser"), roles), True)

    def test_08_get_friend_roles(self):
        roles = self.DBC.get_friend_roles(self.DBC.get_userid_by_name("TestUser"),
                                          self.DBC.get_userid_by_name("TestUser2"))
        roles2 = self.DBC.get_friend_roles(self.DBC.get_userid_by_name("TestUser2"),
                                           self.DBC.get_userid_by_name("TestUser"))
        if not (roles and roles2):
            raise AssertionError("Friend roles error")

    def test_09_create_chat(self):
        chat = self.DBC.create_chat(["TestUser3", "TestUser2", "TestUser"], "TestChat", "TestUser3")
        if not chat:
            raise AssertionError("Chat creation error")

    def test_10_send_messages(self):
        user_id = self.DBC.get_userid_by_name("TestUser")
        chats = self.DBC.get_user_chats(user_id)
        if not chats:
            raise AssertionError("Error loading chats")
        self.assertEqual(self.DBC.send_message(user_id, chats[0]["id"], "Hello! This is test message!"), True)

    def test_11_edit_message(self):
        user_id = self.DBC.get_userid_by_name("TestUser")
        chats = self.DBC.get_user_chats(user_id)
        messages = self.DBC.preload_messages(user_id, chats[0]["id"])
        if not chats:
            raise AssertionError("Error loading chats")
        self.assertEqual(self.DBC.edit_message(user_id, chats[0]["id"], messages[0]["id"], "Edited!"), True)

    def test_12_get_updates(self):
        user_id = self.DBC.get_userid_by_name("TestUser")
        updates = self.DBC.update_all(user_id)
        if not updates:
            raise AssertionError("Updates error")

    def test_13_preload_messages(self):
        user_id = self.DBC.get_userid_by_name("TestUser3")
        chats = self.DBC.get_user_chats(user_id)
        if not chats:
            raise AssertionError("Error loading chats")
        messages = self.DBC.preload_messages(user_id, chats[0]["id"])
        if not messages:
            raise AssertionError("Message wasn't delivered")

    def test_14_update_message(self):
        user_id = self.DBC.get_userid_by_name("TestUser2")
        chats = self.DBC.get_user_chats(user_id)
        if not chats:
            raise AssertionError("Error loading chats")
        messages = self.DBC.preload_messages(user_id, chats[0]["id"])
        msg_date = datetime.datetime.strptime(messages[0]["message_date"], "%Y-%m-%d %H:%M:%S.%f") - datetime.timedelta(
            seconds=10)
        messages = self.DBC.update_messages(chats[0]["id"], str(msg_date), user_id)
        if not messages:
            raise AssertionError("Error loading chats")

    def test_15_message_deletion(self):
        user_id = self.DBC.get_userid_by_name("TestUser")
        chats = self.DBC.get_user_chats(user_id)
        if not chats:
            raise AssertionError("Error loading chats")
        messages = self.DBC.preload_messages(user_id, chats[0]["id"])
        self.assertEqual(self.DBC.delete_message(user_id, chats[0]["id"], messages[0]["id"]), True)

    def test_16_chat_deletion(self):
        user_id = self.DBC.get_userid_by_name("TestUser3")
        chats = self.DBC.get_user_chats(user_id)
        if not chats:
            raise AssertionError("Error loading chats")
        self.assertEqual(self.DBC.delete_chat(user_id, chats[0]["id"]), True)

    def test_17_group_creation(self):
        user_id = self.DBC.get_userid_by_name("TestUser")
        self.assertEqual(self.DBC.create_group(user_id, "TestGroup", "No desc"), True)

    def test_18_group_joining(self):
        users = [self.DBC.get_user(self.DBC.get_userid_by_name(i)) for i in ["TestUser2", "TestUser3"]]
        self.assertEqual([self.DBC.join_group("TestGroup", i) for i in users], [True, True])

    def test_19_is_joined(self):
        user = self.DBC.get_user(self.DBC.get_userid_by_name("TestUser3"))
        self.assertEqual(self.DBC.is_joined("TestGroup", user), True)

    def test_20_group_leave(self):
        user = self.DBC.get_user(self.DBC.get_userid_by_name("TestUser2"))
        self.assertEqual(self.DBC.leave_group("TestGroup", user), True)

    def test_21_group_deletion(self):
        user = self.DBC.get_userid_by_name("TestUser2")
        self.assertEqual(self.DBC.delete_group(user, "TestGroup"), False)
        owner_id = self.DBC.get_userid_by_name("TestUser")
        self.assertEqual(self.DBC.delete_group(owner_id, "TestGroup"), True)

    def test_98_delete_friend(self):
        self.assertEqual(self.DBC.remove_friend(self.DBC.get_userid_by_name("TestUser"),
                                                self.DBC.get_userid_by_name("TestUser2")), True)
        self.assertEqual(self.DBC.remove_friend(self.DBC.get_userid_by_name("TestUser2"),
                                                self.DBC.get_userid_by_name("TestUser3")), True)

    def test_99_delete_user(self):
        self.assertEqual(self.DBC.delete_user("TestUser"), True)
        self.assertEqual(self.DBC.delete_user("TestUser2"), True)
        self.assertEqual(self.DBC.delete_user("TestUser3"), True)

    def tearDown(self) -> None:
        pass
