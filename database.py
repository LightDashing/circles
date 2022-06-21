import argon2.exceptions
from sqlalchemy import or_, and_, delete, select, update, inspect, desc
from sqlalchemy.engine import create_engine
from sqlalchemy.pool import NullPool, AssertionPool, QueuePool
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from argon2 import PasswordHasher
import datetime
import re
from models import User, UserPost, Message, Friend, Chat, Group, GroupPost, UserChatLink, UserRole, \
    ImageAttachment, Notification, NotificationChatLink, UserGroupLink
from files import FileOperations
from user_exceptions import UserAlreadyExist
import json
import os


class DataBase:
    class ConnectionHandler:

        def __init__(self):
            # Нужно поиграться с параметрами пула, потому что сейчас переодически сыпется с twophase error
            with open("settings.json") as settings_file:
                data = json.load(settings_file)["db_settings"]
            if not data:
                raise Exception("Configure your settings file!")
            self.engine = create_engine(
                f'postgresql://{data["username"]}:{data["password"]}@{data["hostname"]}/{data["schema"]}',
                **{"poolclass": QueuePool, "pool_size": 6, "max_overflow": 0,
                   "pool_timeout": 6})
            self.g_session = scoped_session(sessionmaker(self.engine))
            print("Connection to database successful!")
            print(self.engine)

        def __enter__(self):
            self.sp_sess = self.g_session()
            self.commit_needed = False
            return self.sp_sess

        def __exit__(self, *args):
            if self.commit_needed:
                try:
                    self.sp_sess.commit()
                except AttributeError:
                    self.sp_sess.rollback()
                finally:
                    self.g_session.remove()
                    del self.sp_sess
                    self.sp_sess = None
            else:
                self.g_session.remove()
                del self.sp_sess
                self.sp_sess = None

        def __del__(self):
            self.g_session.remove()

    def __init__(self):
        self.conn_handler = self.ConnectionHandler()
        # Для удобства, здесь будут константы для часто использующихся запросов
        self.FRIEND_STATEMENT = lambda x, y: select(Friend).filter(
            ((Friend.first_user_id == x) & (Friend.second_user_id == y)) |
            ((Friend.first_user_id == y) & (Friend.second_user_id == x)))
        self.ph = PasswordHasher()

    @staticmethod
    def is_arr_part(main_arr, sub_arr):
        matches_count = 0
        if len(main_arr) > len(sub_arr):
            return False
        else:
            for i in range(len(main_arr)):
                if main_arr[i] in sub_arr:
                    matches_count += 1
            if matches_count == len(main_arr):
                return True
            else:
                return False

    def add_user(self, username, email, password) -> bool:
        # TODO: Переписать UserAlreadyExist
        try:
            with self.conn_handler as session:
                user = User(username=username, email=email, password=self.ph.hash(password),
                            last_time_online=datetime.datetime.now(),
                            is_online=False)
                user.is_active = False
                session.add(user)
                self.conn_handler.commit_needed = True
            return True
        except UserAlreadyExist:
            return False

    def set_user_active(self, user_name: str) -> bool:
        """
        This function sets user account active using his user name\n
        :param user_name: user's User.username
        :return: True if operation was successful, else False
        """
        user_id = self.get_userid_by_name(user_name)
        with self.conn_handler as session:
            st = select(User).where(User.id == user_id)
            user = session.execute(st).scalar()
            if not user:
                return False
            user.is_active = True
            self.conn_handler.commit_needed = True
            return True

    def delete_user(self, username: str) -> bool:
        """
        This function deletes user from database\n
        :param username: string
        :return: true if was successful, else false
        """
        with self.conn_handler as session:
            st = delete(User).filter(User.username == username).returning(User.username)
            if session.execute(st).scalar():
                self.conn_handler.commit_needed = True
                return True
            else:
                return False

    def login_user(self, email: str, password: str) -> bool:
        with self.conn_handler as session:
            statement = select(User).filter(User.email == email)
            user = session.execute(statement).scalar()
            if user:
                try:
                    self.ph.verify(user.password, password)
                except (argon2.exceptions.VerificationError, argon2.exceptions.VerifyMismatchError,
                        argon2.exceptions.InvalidHash):
                    return False
                if self.ph.check_needs_rehash(user.password):
                    user.password = self.ph.hash(password)
                    self.conn_handler.commit_needed = True
                    return True
                else:
                    return True
            else:
                return False

    def set_online(self, user_id: int, online: bool):
        with self.conn_handler as session:
            statement = update(User).filter(User.id == user_id).values(is_online=online)
            session.execute(statement)

    def update_last_time(self, user_id):
        self.set_online(user_id, True)
        with self.conn_handler as session:
            self.conn_handler.commit_needed = True
            statement = update(User).filter(User.id == user_id).values(last_time_online=datetime.datetime.now())
            session.execute(statement)

    def get_user(self, userid: int, scoped: bool = False) -> User:
        """
        This function returns user by their userid, if user exists. If user exists it's expunge him to be outside
        scoped session\n
        :param userid: User.id
        :param scoped: If true, function will not create it's own scoped session, also it won't expunge it, default false
        :return: object User
        """
        if scoped:
            statement = select(User).filter(User.id == userid)
            user = self.conn_handler.sp_sess.execute(statement).scalar()
            return user

        with self.conn_handler as session:
            statement = select(User).filter(User.id == userid)
            user = session.execute(statement).scalar()
            try:
                session.expunge(user)
            except InvalidRequestError:
                return user
        return user

    def get_userid(self, email):
        with self.conn_handler as session:
            statement = select(User).filter(User.email == email)
            user = session.execute(statement).scalar()
            return user.id

    def userdata_by(self, userid: int):
        with self.conn_handler as session:
            statement = select(User).filter(User.id == userid)
            user = session.execute(statement).scalar()
            if user:
                return user.serialize
            else:
                return {"success": False}

    def change_username(self, old_name: str, new_name: str) -> int:
        """
        This function changes username, returns one of the codes\n
        0 - username was changed successfully
        1 - user with that username already exists
        2 - username length is incorrect
        3 - new username same as old username
        """
        if not new_name or len(new_name) < 3 or len(new_name) > 30:
            return 2
        user_id = self.get_userid_by_name(old_name)
        with self.conn_handler as session:
            statement = select(User).filter(User.username == new_name)
            if old_name == new_name:
                return 3
            elif session.execute(statement).first():
                return 1
            self.conn_handler.commit_needed = True
            statement = update(User).filter(User.username == old_name).values(username=new_name)
            session.execute(statement)

            statement = select(Chat).join(UserChatLink).filter(UserChatLink.user_id == user_id)
            all_chats = session.execute(statement).all()
            for chat in all_chats:
                if chat[0].is_dialog:
                    chat[0].chatname = chat[0].chatname.replace(old_name, new_name)


    def change_description(self, user_id: int, desc: str) -> int:
        """
        This function changes user description, it returns one of the codes
        0: description was successfully changed
        -1: some unknown error occurred on database side
        """
        if not desc:
            desc = 'None was provided'
        with self.conn_handler as session:
            self.conn_handler.commit_needed = True
            statement = update(User).filter(User.id == user_id).values(description=desc)
            session.execute(statement)
        return 0

    def change_mail(self, user_id: int, email: str) -> int:
        """
        This function changes user e-mail, it returns one of the codes
        0: email was successfully changed
        1: email isn't valid
        2: there already exist user with such email
        3: new email same as old email
        -1: some unknown error occurred on database side
        """
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if not re.fullmatch(pattern, email):
            return 1
        with self.conn_handler as session:
            statement = select(User).filter(User.id == user_id)
            user = session.execute(statement).scalar()
            if user.email == email:
                return 3

            statement = select(User).filter(User.email == email)
            user = session.execute(statement).scalar()
            if user.email == email:
                return 2

            self.conn_handler.commit_needed = True
            return 0

    def change_publish_settings(self, name: str, publish: bool) -> bool:
        """
        This function can change if other users may post on your wall or not, it returns one of the codes\n
        :param name: user nickname
        :param publish: boolean, true or false, can other post or not
        :return: true if operation was successful
        """
        with self.conn_handler as session:
            statement = update(User).filter(User.username == name).values(other_publish=publish)
            session.execute(statement)
            self.conn_handler.commit_needed = True
            return True

    def change_avatar(self, userid: int, filepath: str):
        """
        This function changes filepath to user avatar on server in database entry\n
        :param userid: id of user which avatar you need to change, User.id
        :param filepath: path of new file in server filesystem relative to server directory
        :return: true if operation was successful
        """
        with self.conn_handler as session:
            statement = update(User).filter(User.id == userid).values(avatar=filepath)
            session.execute(statement)
            self.conn_handler.commit_needed = True
            return True

    def get_group_name(self, group_id: int, scoped=True):

        if scoped:
            statement = select(Group).filter(Group.id == group_id)
            group = self.conn_handler.sp_sess.execute(statement).scalar()
            return group.group_name
        with self.conn_handler as session:
            statement = select(Group).filter(Group.id == group_id)
            group = session.execute(statement).scalar()
            return group.group_name

    def update_all(self, user_id: int) -> dict[str, list[dict]]:
        """
        This function checks all chats for new messages and returns a dict, where in "chats" key lays all chats and
        amount of messages in them and in "friends" key amount of new friends requests/n
        :param user_id: Id of user, who getting updates
        :return: dict {"chats":[{"message_amount": message_amount, "is_notified": bool, "chat_id": int}],
        "friends": new_requests_amount}
        """
        new_notifications = {"chats": []}
        with self.conn_handler as session:
            st = select(Chat).join(UserChatLink).filter(UserChatLink.user_id == user_id)
            chats = session.execute(st).all()
            for chat in chats:  # Part of the code that deals with amount of new messages and sets notification for them
                chat_info = {}
                # There we're getting notification for this user and for this chat from list of all chats
                st = select(Notification).filter(Notification.user_id == user_id).join(NotificationChatLink).filter(
                    NotificationChatLink.chat_id == chat[0].id)
                notification = session.execute(st).scalar()
                # If user is already notified about new message, we set is_notified to True
                if notification.is_notified:
                    chat_info["is_notified"] = True
                else:
                    chat_info["is_notified"] = False

                # if user right now is in chat or already opened it and was its contents
                if notification.is_read:
                    continue

                # There we're getting a link with chat and notification by their respective ids
                st = select(NotificationChatLink).filter((NotificationChatLink.chat_id == chat[0].id) & (
                        NotificationChatLink.notification_id == notification.id))
                notification_link = session.execute(st).scalar()
                # If chat is muted, or user right now uses chat, no need for updating him
                if notification_link.is_muted or \
                        notification_link.last_visited >= datetime.datetime.now() - datetime.timedelta(seconds=20):
                    continue

                # There we're getting all messages that are new and from this chat and setting counter for them
                st = select(Message).join(Chat).filter(
                    (Chat.id == chat[0].id) & (Message.message_date > notification_link.last_visited))
                messages = session.execute(st).all()
                self.__set_msg_count_notification(notification.id, chat[0].id, len(messages), session)

                # Adding chat to list of chats with updates
                chat_info["message_amount"] = len(messages)
                chat_info["chat_id"] = chat[0].id
                # ID is converted to str, because Flask jsonify doesn't work other way
                new_notifications["chats"].append(chat_info)
                notification.is_notified = True

            # This part of function updates all user friends and get all updates from them
            st = select(Friend).filter((Friend.is_checked == False) & (Friend.second_user_id == user_id))
            new_friends = session.execute(st).all()
            is_not_notified = False
            for friend in new_friends:
                if not friend[0].is_notified:
                    is_not_notified = True
                friend[0].is_notified = True
                # st = update(Friend).filter(Friend.id == friend[0].id).values(is_notified=True)
                # session.execute(st)

            new_notifications["friends"] = len(new_friends)
            if is_not_notified:
                new_notifications["new_friends"] = True
            else:
                new_notifications["new_friends"] = False
            self.conn_handler.commit_needed = True
        return new_notifications

    def search_for(self, search_query: str) -> list[dict]:
        """
        This function search users by their name and then returns result with limit of 5 users\n
        :param search_query: str
        :param search_type: str, user or group
        :return: array of dicts, User.serialize
        """
        users = []
        with self.conn_handler as session:
            query = select(User).filter(User.username.like(f"%{search_query}%"))
            result = session.execute(query).scalars().fetchmany(5)
            query_2 = select(Group).filter(Group.group_name.like(f"%{search_query}%"))
            result_2 = session.execute(query_2).scalars().fetchmany(5)
            users = [user.serialize for user in result]
            users.extend([group.serialize for group in result_2])
        # TODO: сделать поиск по группам
        return users

    def search_role(self, search_query: str, user_id: int) -> list[dict]:
        """
        This function is searching for
        :param search_query:
        :param user_id:
        :return:
        """
        with self.conn_handler as session:
            query = select(UserRole).filter(UserRole.role_name.like(f"%{search_query}%"), UserRole.creator == user_id)
            results = session.execute(query).scalars()
            roles = [role.serialize for role in results]
        return roles

    # TODO: сделать систему дозагрузки при прокрутке страницы
    def get_user_friends(self, userid: int, amount: int = 5) -> list[dict]:
        """
        This function returns user friends in specified amount\n
        :param userid: int, User.id
        :param amount: int, amount of friends to return
        :return: array of User.serialize
        """
        with self.conn_handler as session:
            statement = select(User).filter(User.id == userid)
            user = session.execute(statement).scalar()
            user_friends = []
            for friend in user.friends:
                if friend.first_user.id == userid:
                    user_friends.append(friend.second_user.serialize)
                else:
                    user_friends.append(friend.first_user.serialize)
        return user_friends

    def get_userid_by_name(self, name: str, scoped: bool = False) -> int:
        """
        Returns user User.id by their name\n
        :param name: str, User.username
        :param scoped: bool, if true function will not create it's own scoped session and will use existing one
        :return: int, User.id or -1 if there was no user
        """
        if scoped:
            statement = select(User).filter(User.username == name)
            user = self.conn_handler.sp_sess.execute(statement).scalar()
            if user:
                return user.id
            else:
                return -1

        with self.conn_handler as session:
            statement = select(User).filter(User.username == name)
            user = session.execute(statement).scalar()
            if user:
                return user.id
            else:
                return -1

    def get_name_by_userid(self, user_id: int, scoped: bool = False) -> str:
        """
        Returns User.username by their id\n
        :param scoped: boolean, if true it will not create new scoped database session
        :param user_id: int, User.id
        :return: str, User.username or None if there was no user
        """
        statement = select(User).filter(User.id == user_id)
        if scoped:
            user = self.conn_handler.sp_sess.execute(statement).scalar()
            if user:
                return user.username
        with self.conn_handler as session:
            user = session.execute(statement).scalar()
            if user:
                return user.username

    def get_your_posts(self, user_id):
        with self.conn_handler as session:
            statement = select(UserPost).filter(UserPost.whereid == user_id)
            posts = session.execute(statement)
            if posts:
                all_posts = []
                for post in posts:
                    ser = post[0].serialize
                    ser["liked"] = self.is_liked(ser["id"], "u", user_id, session)
                    all_posts.append(ser)
                return all_posts[::-1]

    def like_post(self, user_id: int, post_type: str, post_id: int):
        with self.conn_handler as session:
            stmt = select(User).filter(User.id == user_id)
            user = session.execute(stmt).scalar()
            if post_type == "g":
                stmt = select(GroupPost).filter(GroupPost.id == post_id)
            else:
                stmt = select(UserPost).filter(UserPost.id == post_id)
            post = session.execute(stmt).scalar()
            if user in post.likes:
                post.likes.remove(user)
            else:
                post.likes.append(user)
            self.conn_handler.commit_needed = True
            return True

    def get_posts_by_id(self, username: str, your_id: int, user_roles: list[str]) -> list[UserPost]:
        """
        This function gets all posts on user page with specified view level\n
        :param user_roles:
        :param username: str, User.username
        :param your_id: int, id of current user
        :return: list of UserPost objects or None if there was no UserPosts
        """
        user_id = self.get_userid_by_name(username)
        is_friend = self.is_friend(user_id, your_id)
        with self.conn_handler as session:
            if not user_roles:
                if is_friend:
                    statement = select(UserPost).filter((UserPost.whereid == user_id) & (UserPost.roles == None))
                else:
                    statement = select(UserPost).filter(UserPost.whereid == user_id, UserPost.is_private == False)
                posts = session.execute(statement).all()
                if posts:
                    s_posts = []
                    for post in posts:
                        ser = post[0].serialize
                        ser["liked"] = self.is_liked(ser["id"], "u", your_id, session)
                        s_posts.append(ser)
                    # s_posts = [post[0].serialize for post in posts]
                    return s_posts[::-1]
            else:
                statement = select(UserPost).filter(UserPost.whereid == user_id)
                posts = session.execute(statement).all()
                s_posts = []
                for post in posts:
                    role_names = [role.role_name for role in post[0].roles]
                    if self.is_arr_part(role_names, user_roles):
                        ser = post[0].serialize
                        ser["liked"] = self.is_liked(ser["id"], "u", your_id, session)
                        s_posts.append(ser)
                return s_posts[::-1]

    def get_avatar_by_name(self, username: str) -> str:
        with self.conn_handler as session:
            statement = select(User).filter(User.username == username)
            user = session.execute(statement).scalar()
            print(username, user)
            return user.avatar

    def get_user_chats(self, user_id: int) -> list:
        """
        This function is gets all chats which user are member of and returns their serialize property\n
        :param user_id: int
        :return: list[dict], "id", "chatname", "admin", "rules"
        """
        with self.conn_handler as session:
            statement = select(User).filter(User.id == user_id)
            user = session.execute(statement).scalar()
            chats = []
            for chat in user.chats:
                chats.append(chat.serialize)
        return chats

    def get_user_groups(self, user_id: int) -> list:
        """
        This function is requesting database and returning all groups user are member of\n
        :param user_id: int:
        :return: list[Group]:
        """
        with self.conn_handler as session:
            statement = select(User).filter(User.id == user_id)
            user = session.execute(statement).scalar()
            groups = []
            for group in user.groups:
                groups.append(group.serialize)
            return groups

    def create_group(self, user_id: int, group_name: str, group_desc: str, group_summary: str, group_avatar: str = None,
                     group_rules: str = None):
        with self.conn_handler as session:
            group = Group(group_name=group_name, owner=user_id, description=group_desc,
                          status=group_summary,
                          rules=group_rules)
            session.add(group)
            session.flush()
            session.refresh(group)
            if not group_avatar:
                group_avatar = os.path.join("..", "static", "img", "peoples.svg")
            else:
                fo = FileOperations(user_id)
                # group_avatar = fo.save_group_image(group_avatar, group_name, "group_avatar")
                group.avatar = fo.save_group_image(group_avatar, group.id, "group_avatar")
            self.conn_handler.commit_needed = True
        return True

    def delete_user_post(self, user_id, post_id):
        with self.conn_handler as session:
            stmt = delete(UserPost).filter((UserPost.id == post_id) & (UserPost.userid == user_id))
            res = session.execute(stmt)
            self.conn_handler.commit_needed = True
            if res.rowcount > 0:
                return True
            else:
                stmt = delete(UserPost).filter((UserPost.id == post_id) & (UserPost.whereid == user_id))
                res = session.execute(stmt)
                if res.rowcount > 0:
                    return True
                return False

    def delete_group(self, owner_id: int, group_name: str) -> bool:
        """
        This function deletes group if there is a group with owner_id and group_name\n
        :param owner_id: int, user.id of group owner
        :param group_name: str, group.group_name
        :return: True if deletion was successful, else False
        """
        with self.conn_handler as session:
            st = delete(Group).filter((Group.group_name == group_name) & (Group.owner == owner_id)).returning(
                Group.group_name)
            deleted = session.execute(st).scalar()
            if deleted:
                self.conn_handler.commit_needed = True
                return True
            else:
                return False

    def join_group(self, group_name: str, current_user: User) -> bool:
        """
        This function get current user and add him to group\n
        :param group_name: str
        :param current_user: User class
        :return: True if success, else False
        """
        with self.conn_handler as session:
            statement = select(Group).filter(Group.group_name == group_name)
            group = session.execute(statement).scalar()
            group.users.append(current_user)
            self.conn_handler.commit_needed = True
            return True

    def leave_group(self, group_name: str, current_user: User) -> bool:
        """
        This function get current user and deletes him from group users list\n
        :param group_name: str
        :param current_user: User class
        :return: True if success else False
        """
        with self.conn_handler as session:
            statement = select(Group).filter(Group.group_name == group_name)
            group = session.execute(statement).scalar()
            group.users.remove(current_user)
            self.conn_handler.commit_needed = True
            return True

    def is_joined(self, group_name: str, current_user: User) -> bool:
        """
        This function get current user and check if he is in the group users list\n
        :param group_name: str
        :param current_user: User class
        :return: True if user in group, False if isn't
        """
        test_user = current_user
        with self.conn_handler as session:
            assert test_user == current_user
            statement = select(Group).filter(Group.group_name == group_name)
            group = session.execute(statement).scalar()
            if current_user in group.users:
                return True
            else:
                return False

    def get_group_data(self, group_name: str) -> dict:
        """
        This function returns group.serialize property with it's all info\n
        :param group_name: str
        :return: dict, "id", "avatar", "group_name", "status", "owner", "description", "rules"
        """
        with self.conn_handler as session:
            statement = select(Group).filter(Group.group_name == group_name)
            group = session.execute(statement).scalar()
            return group.serialize

    def get_user_dialog(self, user_id: int, s_user_id: int) -> Chat:
        """
        This function gets chat (dialog) between two users and returns it, if there is no chats, it creates new\n
        :param user_id: int, User.id
        :param s_user_id: int, User.id
        :return: Chat object
        """
        with self.conn_handler as session:
            # This statement is to get both users entries
            statement = select(User).filter(or_(User.id == user_id, User.id == s_user_id))
            users = session.execute(statement).scalars().fetchmany(2)
            # This statement is to get all shared chats between users
            statement = select(Chat).filter(Chat.users.contains(users[0]) & (Chat.users.contains(users[1])))
            chats = session.execute(statement).all()
            for chat in chats:
                if chat[0].is_dialog:
                    return chat[0].serialize
            # If there are chat where is_dialog is True, then it's right chat, else we create new
            chat = self.create_dialog_chat(users[0], users[1], session)
            self.conn_handler.commit_needed = True
        return chat

    def create_dialog_chat(self, user: User, s_user: User, session) -> Chat:
        """
        This function creates chat only for two users with "is_dialog" set to True, it's usual chat but in
        html it would be displayed as dialog\n
        :param user: User object
        :param s_user: User object
        :return: created Chat object
        """
        dialog = Chat(chatname=f"{user.username} {s_user.username}", is_dialog=True,
                      avatar=os.path.join("..", "static", "img", "two-peoples.svg"),
                      chat_color='#FFFFFF')
        # chatname isn't really matters because in html it would be displayed as friends name
        session.add(dialog)
        session.flush()
        session.refresh(dialog)
        self.create_notification(user.id, dialog.id, is_scoped=True, scoped_session=session)
        self.create_notification(s_user.id, dialog.id, is_scoped=True, scoped_session=session)
        dialog.users.append(user), dialog.users.append(s_user)
        return dialog.serialize

    def get_chat_by_id(self, chat_id: int) -> Chat:
        """
        This function returns Chat object by it's id\n
        :param chat_id: int, Chat.idf
        :return: Chat object
        """
        with self.conn_handler as session:
            statement = select(Chat).filter(Chat.id == chat_id)
            chat = session.execute(statement).scalar()
            return chat.serialize

    # TODO: переделать
    def create_chat(self, users: list, chat_name: str, admin: str, rules: str = "There is no rules!", avatar: str = None) -> int:
        admin_id = self.get_userid_by_name(admin)
        admin = self.get_user(admin_id)
        with self.conn_handler as session:
            self.conn_handler.commit_needed = True
            if len(users) < 2:
                chat = self.create_dialog_chat(admin, users[0])
                return chat.id
            chat = Chat(chatname=chat_name, rules=rules, chat_color="#d5d6db")
            session.add(chat)
            if avatar:
                fo = FileOperations(admin_id)
                avatar = fo.save_user_image(avatar)
                chat.avatar = avatar
            for user in users:
                user_id = self.get_userid_by_name(user, scoped=True)
                user = self.get_user(user_id, scoped=True)
                self.create_notification(user_id, chat.id, is_scoped=True, scoped_session=session)
                if user.id == admin_id:
                    session.add(UserChatLink(user_id=user.id, chat_id=chat.id, is_admin=True))
                elif user:
                    chat.users.append(user)
            return chat.id

    def delete_chat(self, admin_id: int, chat_id: int) -> bool:
        """
        This function deletes chat if there is chat with admin as admin_id and chat_id\n
        :param admin_id: integer, user.id of admin user
        :param chat_id: integer, chat.id
        :return: True if deletion was successful, else False
        """
        with self.conn_handler as session:
            st = select(UserChatLink).filter((UserChatLink.is_admin == True) & (UserChatLink.user_id == admin_id))
            chat = session.execute(st).scalar()
            if not chat:
                return False
            else:
                self.conn_handler.commit_needed = True
                delete(Chat).filter((Chat.id == chat_id))
                return True

    def leave_chat(self, chat_id: int, user_id: int):
        with self.conn_handler as session:
            stmt = delete(UserChatLink).filter((UserChatLink.chat_id == chat_id) & (UserChatLink.user_id == user_id))
            session.execute(stmt)
            self.conn_handler.commit_needed = True
            return True

    def preload_messages(self, user_id: int, chat_id: int):
        with self.conn_handler as session:
            # statement = update(UserChatLink).filter(UserChatLink.user_id == user_id).values(is_notified=True)

            statement = select(NotificationChatLink).join(Notification).where(
                (NotificationChatLink.chat_id == chat_id) & (
                        Notification.user_id == user_id))

            notification_chat = session.execute(statement).scalar()
            notification_chat.last_visited = datetime.datetime.now()
            notification_chat.message_count = 0

            statement = select(Notification).join(NotificationChatLink).where(
                (NotificationChatLink.chat_id == chat_id) & (
                        Notification.user_id == user_id))
            notification = session.execute(statement).scalar()
            notification.is_read = True
            notification.is_notified = True

            self.conn_handler.commit_needed = True

            st = select(UserChatLink).filter((UserChatLink.user_id == user_id) & (UserChatLink.chat_id == chat_id))
            if not session.execute(st).scalar():
                return []
            statement = select(Message).join(Chat).filter(Chat.id == chat_id).order_by(desc(Message.message_date))
            all_messages = session.execute(statement).fetchmany(20)
            messages = []
            for message in all_messages:
                message = message[0].serialize
                messages.append(message)
        return messages[::-1]

    def load_messages(self, user_id: int, chat_id: int, f_msg_date: str):
        if not f_msg_date:
            return []
        f_msg_date = datetime.datetime.strptime(f_msg_date, "%Y-%m-%d %H:%M:%S.%f")
        with self.conn_handler as session:
            statement = select(UserChatLink).filter(UserChatLink.user_id == user_id, UserChatLink.chat_id == chat_id)
            users = session.execute(statement).scalar()
            if not users:
                return []

            statement = select(Message).join(Chat).filter((Chat.id == chat_id) & (Message.message_date < f_msg_date))
            messages = session.execute(statement).all()
            all_messages = {"messages": []}
            if len(messages) > 40:
                all_messages["older"] = True
            else:
                all_messages["older"] = False

            if messages:
                for message in messages[:41]:
                    message = message[0].serialize
                    message['from_user_id'] = self.get_name_by_userid(message['from_user_id'], scoped=True)
                    all_messages["messages"].append(message)
            else:
                return []
        return all_messages

    # TODO: переделать как-нибудь чтобы было не так затратно по ресурсам
    def update_messages(self, chat_id: int, msg_time: str, user_id: int):
        if not msg_time:
            msg_time = str(datetime.datetime.now())
        msg_time = datetime.datetime.strptime(msg_time, "%Y-%m-%d %H:%M:%S.%f")
        with self.conn_handler as session:
            statement = select(UserChatLink).filter(UserChatLink.user_id == user_id, UserChatLink.chat_id == chat_id)
            users = session.execute(statement).scalar()
            if not users:
                return []

            statement = select(Message).join(Chat).filter(
                and_(Chat.id == chat_id, Message.message_date > msg_time))
            messages = session.execute(statement).all()

            statement = select(NotificationChatLink).join(Notification).where(
                (NotificationChatLink.chat_id == chat_id) & (
                        Notification.user_id == user_id))

            notification_chat = session.execute(statement).scalar()
            notification_chat.last_visited = datetime.datetime.now()

            statement = select(Notification).join(NotificationChatLink).where(
                (NotificationChatLink.chat_id == chat_id) & (
                        Notification.user_id == user_id))
            notification = session.execute(statement).scalar()
            notification.is_read = True
            notification.is_notified = True

            self.conn_handler.commit_needed = True

            all_messages = []
            if messages:
                for message in messages:
                    message = message[0].serialize
                    message['from_user_id'] = self.get_name_by_userid(message['from_user_id'], scoped=True)
                    all_messages.append(message)
            else:
                return []
        return all_messages

    @staticmethod
    def create_attach(user_id: int, pinned_images: list[str], group_id: int = None) -> ImageAttachment:
        files = FileOperations(user_id)

        if group_id:
            image = files.save_group_image(pinned_images[0], group_id)
        else:
            image = files.save_user_image(pinned_images[0])

        attach = ImageAttachment(a1_link=image, date_added=datetime.datetime.now())

        if len(pinned_images) > 1:
            attach_array = []
            for i in range(1, 5):
                try:
                    if group_id:
                        attach_array.append(files.save_group_image(pinned_images[i], group_id))
                    else:
                        attach_array.append(files.save_user_image(pinned_images[i]))
                except IndexError:
                    break
            attach.image_links = attach_array
        return attach

    def send_message(self, user_id: int, chat_id: int, msg: str, pinned_images: list[str] = None) -> bool:
        with self.conn_handler as session:
            st = select(UserChatLink).filter((UserChatLink.user_id == user_id) & (UserChatLink.chat_id == chat_id))
            if not session.execute(st).scalar():
                return False
            self.conn_handler.commit_needed = True
            statement = select(Chat).filter(Chat.id == chat_id)
            chat = session.execute(statement).scalar()
            message = Message(from_user_id=user_id, message_date=datetime.datetime.now(), message=msg, chat_id=chat.id)
            if pinned_images:
                attach = self.create_attach(user_id, pinned_images)
                message.attachment.append(attach)
            session.add(message)
            statement = select(Notification).join(NotificationChatLink).filter(NotificationChatLink.chat_id == chat_id)
            notifications = session.execute(statement).all()
            for notification in notifications:
                notification[0].is_notified = False
                notification[0].is_read = False

            statement = select(Notification).join(NotificationChatLink).filter(
                (Notification.user_id == user_id) & (NotificationChatLink.chat_id == chat_id))
            notification = session.execute(statement).scalar()
            notification.is_notified = True
            notification.is_read = True
        return True

    def delete_message(self, user_id: int, chat_id: int, message_id: int) -> bool:
        """
        This function deletes message that was sent by user\n
        :param user_id: int, id of user who sent message
        :param chat_id: int, id of chat where message is located
        :param message_id: int, message id
        :return: True if deletion was successful else False
        """
        with self.conn_handler as session:
            st = delete(Message).filter((Message.from_user_id == user_id) & (Message.chat_id == chat_id) & (
                    Message.id == message_id)).returning(Message.id)
            msg = session.execute(st).scalar()
            if msg:
                self.conn_handler.commit_needed = True
                return True
            else:
                return False

    def edit_message(self, user_id: int, chat_id: int, message_id: int, message_text: str):
        with self.conn_handler as session:
            st = update(Message).filter(
                (Message.from_user_id == user_id) & (Message.chat_id == chat_id) & (Message.id == message_id)).values(
                message=message_text, edited=True)
            rows_affected = session.execute(st).rowcount
            if rows_affected > 0:
                self.conn_handler.commit_needed = True
                return True
            else:
                return False

    def publish_group_post(self, msg: str, user_id: int, group_id: int, pinned_images: list[str], is_anonymous: bool):
        if not self.is_joined(self.get_group_name(group_id, False), self.get_user(user_id)):
            return []
        with self.conn_handler as session:
            post = GroupPost(group_id=group_id, date_added=datetime.datetime.now(), posted_user_id=user_id,
                             is_anonymous=is_anonymous, post_text=msg)
            if pinned_images:
                attach = self.create_attach(user_id, pinned_images, group_id)
                post.attachment.append(attach)
            session.add(post)
            session.flush()
            session.refresh(post)
            self.conn_handler.commit_needed = True
            return post.serialize

    # TODO: добавить ограничение на количество ролей в посте
    #  также нужно переработать этот код
    def publish_post(self, msg: str, user_id: int, roles: list[str], pinned_images: list[str], is_private: bool,
                     where_id: int = None) -> bool:
        if where_id:
            roles = self.get_friend_roles(where_id, user_id)
        with self.conn_handler as session:
            if not where_id:
                if not is_private:
                    post = UserPost(userid=user_id, message=msg, whereid=user_id, is_private=is_private,
                                    date_added=datetime.datetime.now())
                else:
                    post = UserPost(userid=user_id, message=msg, whereid=user_id, is_private=is_private,
                                    date_added=datetime.datetime.now())
                    for role in roles:
                        statement = select(UserRole).filter(
                            (UserRole.role_name == role) & (UserRole.creator == user_id))
                        role = session.execute(statement).scalar()
                        post.roles.append(role)
                if pinned_images:
                    attach = self.create_attach(user_id, pinned_images)
                    post.attachment.append(attach)
            else:
                post = UserPost(userid=user_id, message=msg, whereid=where_id, is_private=True,
                                date_added=datetime.datetime.now())
                for role in roles:
                    statement = select(UserRole).filter(
                        (UserRole.role_name == role["role_name"]) & (UserRole.creator == where_id))
                    role = session.execute(statement).scalar()
                    post.roles.append(role)
                print(roles)
                if pinned_images:
                    attach = self.create_attach(user_id, pinned_images)
                    post.attachment.append(attach)
            session.add(post)
            session.flush()
            session.refresh(post)
            self.conn_handler.commit_needed = True
            return post.serialize

    def remove_post(self, post_id):
        with self.conn_handler as session:
            statement = delete(UserPost).filter(UserPost.id == post_id)
            session.execute(statement)
            self.conn_handler.commit_needed = True

    def get_your_post(self, post_id: int, user_id: int):
        with self.conn_handler as session:
            statement = select(UserPost).filter(UserPost.id == post_id, UserPost.userid == user_id)
            post = session.execute(statement).scalar().serialize
            post["liked"] = self.is_liked(post["id"], "u", user_id, session)
            return post

    def get_group_post(self, post_id: int, user_id: int):
        with self.conn_handler as session:
            statement = select(GroupPost).filter(GroupPost.id == post_id, GroupPost.posted_user_id == user_id)
            post = session.execute(statement).scalar()
            return post.serialize

    def get_group_posts(self, group_id: int, user_id: int, group_name: str = None):
        with self.conn_handler as session:
            if group_name:
                statement = select(GroupPost).join(Group).filter(Group.group_name == group_name)
            else:
                statement = select(GroupPost).filter(GroupPost.group_id == group_id)
            posts = session.execute(statement).all()
            posts_a = []
            for post in posts:
                ser = post[0].serialize
                ser["liked"] = self.is_liked(ser["id"], "g", user_id, session)
                posts_a.append(ser)
            return posts_a

    def is_liked(self, post_id: int, post_type: str, user_id: int, session=None) -> bool:
        if session:
            user = session.execute(select(User).filter(User.id == user_id)).scalar()
            if post_type == 'g':
                post = session.execute(select(GroupPost).filter(GroupPost.id == post_id)).scalar()
            else:
                post = session.execute(select(UserPost).filter(UserPost.id == post_id)).scalar()
            if user in post.likes:
                return True
            else:
                return False
        else:
            with self.conn_handler as session:
                user = session.execute(select(User).filter(User.id == user_id)).scalar()
                if post_type == 'g':
                    post = session.execute(select(GroupPost).filter(GroupPost.id == post_id)).scalar()
                else:
                    post = session.execute(select(UserPost).filter(UserPost.id == post_id)).scalar()
                if user in post.likes:
                    return True
                else:
                    return False

    def get_user_friends_posts(self, user_id: int) -> list:
        posts = []
        with self.conn_handler as session:
            statement = select(User).filter(User.id == user_id)
            user = session.execute(statement).scalar()
            friends_list = []
            for friend in user.friends:
                friends_list.append(friend.serialize)
        for friend in friends_list:
            if friend["first_user_id"] == user_id:
                roles = self.get_friend_roles(friend["second_user_id"], user_id)
                if roles:
                    roles = [role['role_name'] for role in roles]
                u_posts = DBC.get_posts_by_id(friend["second_username"], user_id, roles)
            else:
                roles = self.get_friend_roles(friend["first_user_id"], user_id)
                if roles:
                    roles = [role['role_name'] for role in roles]
                u_posts = DBC.get_posts_by_id(friend["first_username"], user_id, roles)
            if u_posts:
                posts.extend(u_posts)
        return posts

    def get_user_groups_posts(self, user_id: int) -> list:
        posts = []
        with self.conn_handler as session:
            stmt = select(GroupPost).join(Group).join(UserGroupLink).filter(UserGroupLink.user_id == user_id)
            all_posts = session.execute(stmt).all()
            for post in all_posts:
                serialized = post[0].serialize
                serialized["liked"] = self.is_liked(serialized["id"], "g", user_id, session)
                posts.append(serialized)
        return posts

    def get_user_feed(self, user_id: int):
        friends_posts = self.get_user_friends_posts(user_id)
        groups_posts = self.get_user_groups_posts(user_id)
        your_wall_posts = self.get_your_posts(user_id)
        all_posts = [*friends_posts, *groups_posts, *your_wall_posts]
        all_posts.sort(key=lambda x: x["date_added"], reverse=True)
        return all_posts

    def a_delete_u_post(self, u_post_id: int):
        with self.conn_handler as session:
            stmt = delete(UserPost).filter(UserPost.id == u_post_id)
            session.execute(stmt)
            self.conn_handler.commit_needed = True

    def a_delete_g_post(self, g_post_id: int):
        with self.conn_handler as session:
            stmt = delete(GroupPost).filter(GroupPost.id == g_post_id)
            session.execute(stmt)
            self.conn_handler.commit_needed = True

    def a_delete_user(self, user_id: int):
        with self.conn_handler as session:
            stmt = delete(User).filter(User.id == user_id)
            session.execute(stmt)
            self.conn_handler.commit_needed = True

    def a_delete_group(self, group_id: int):
        with self.conn_handler as session:
            stmt = delete(Group).filter(Group.id == group_id)
            session.execute(stmt)
            self.conn_handler.commit_needed = True

    def create_role(self, role_name: str, role_color: str, user_id: int):
        # TODO: добавить донаты для монетизации, максимальное кол-во ролей для обычного пользователя - 5
        #  для людей которые задонатили можно сделать до 10
        with self.conn_handler as session:
            statement = select(UserRole).filter(UserRole.creator == user_id)
            roles = session.execute(statement).all()
            if len(roles) < 6:
                user_role = UserRole(role_name=role_name, role_color=role_color, creator=user_id)
                session.add(user_role)
                session.flush()
                session.refresh(user_role)
                self.conn_handler.commit_needed = True
                return user_role.serialize
            else:
                return False

    def delete_role(self, role_id: int, user_id: int):
        with self.conn_handler as session:
            statement = delete(UserRole).filter(UserRole.id == role_id, UserRole.creator == user_id)
            session.execute(statement)
            self.conn_handler.commit_needed = True

    def get_roles(self, user_id: int) -> list[dict]:
        with self.conn_handler as session:
            statement = select(UserRole).filter(UserRole.creator == user_id)
            user_roles = session.execute(statement).all()
            user_roles = [role[0].serialize for role in user_roles]
        return user_roles

    def change_role(self, role_id: int, user_id: int, new_role_name: str = None, new_role_color: str = None,
                    new_font_color: str = None, can_post: bool = None) -> dict:
        with self.conn_handler as session:
            statement = select(UserRole).filter(UserRole.creator == user_id, UserRole.id == role_id)
            user_role = session.execute(statement).scalar()
            if user_role:
                if new_role_name:
                    user_role.role_name = new_role_name
                if new_role_color:
                    user_role.role_color = new_role_color
                if new_font_color:
                    user_role.font_color = new_font_color
                if can_post:
                    user_role.can_post = can_post
                self.conn_handler.commit_needed = True
                return user_role.serialize
            else:
                return {}

    def add_friend(self, user: int, second_user: int) -> bool:
        """
        This function is checking if friend already exists and if it isn't, adds a new entry to database\n
        returns boolean value, true if new entry was created and false if entry already existed
        """
        with self.conn_handler as session:  # Checking if there already existing entry
            statement = self.FRIEND_STATEMENT(user, second_user)
            users = session.execute(statement).all()
            if users:
                return False
            else:
                session.add(
                    Friend(first_user_id=user, second_user_id=second_user,
                           date_added=datetime.datetime.now()))  # Adding new entry
                self.conn_handler.commit_needed = True
                return True

    def remove_friend(self, user: int, second_user: int) -> bool:
        """
        This function removes friend and decreases amount of friends both users have\n
        :param user: id of first user, usually current_user
        :param second_user: id of second user, someone else
        :return: True if deletion was successful, false if there was no friend entry
        """
        with self.conn_handler as session:
            statement = self.FRIEND_STATEMENT(user, second_user)
            friend = session.execute(statement).scalar()  # Getting existing rows
            if not friend:  # If there is no friend entry like that
                return False
            self.remove_all_friend_roles(friend.first_user_id, friend.second_user_id, session)
            self.remove_all_friend_roles(friend.second_user_id, friend.first_user_id, session)
            statement = delete(Friend).filter((Friend.first_user_id == friend.first_user_id) &
                                              (Friend.second_user_id == friend.second_user_id))
            session.execute(statement)
            self.conn_handler.commit_needed = True
            return True

    def remove_all_friend_roles(self, user_id: int, friend_id: int, scoped=False):
        if scoped:
            friend = scoped.execute(self.FRIEND_STATEMENT(user_id, friend_id)).scalar()
            if friend.first_user_id == user_id:
                friend.second_user_roles = []
            else:
                friend.first_user_roles = []

    def accept_request(self, second_user: int, user: int) -> bool:
        """
        This function gets two users and finds a friend entry, updating it with is_request to False\n
        :param second_user: int, User.id
        :param user: int, User.id
        :return: True if updating was successful
        """
        with self.conn_handler as session:
            statement = update(Friend).filter(Friend.first_user_id == user, Friend.second_user_id == second_user) \
                .values(is_request=False, is_checked=True)
            session.execute(statement)
            self.conn_handler.commit_needed = True
        return True

    def is_friend(self, user: int, second_user: int):
        """
        This function checks if user is a friend of current user\n
        returns either a dict with all friend connection data or just bool false
        """
        with self.conn_handler as session:
            statement = self.FRIEND_STATEMENT(user, second_user)
            friend = session.execute(statement).scalar()
            if not friend:
                return False
            else:
                return friend.serialize

    def change_friend_roles(self, user_id: int, friend_id: int, roles: list[dict]) -> bool:
        """
        This function changes roles that your friend have
        :param user_id: your id
        :param friend_id: friends id
        :param roles: array with dict of roles
        :return: true if replacing was success, false if not
        """
        all_roles = self.get_friend_roles(user_id, friend_id)
        id_array = [elem["id"] for elem in all_roles]
        with self.conn_handler as session:
            friend = session.execute(self.FRIEND_STATEMENT(user_id, friend_id)).scalar()
            for role in roles:
                if role["id"] in id_array:
                    id_array.remove(role["id"])
                else:
                    id_array.append(role["id"])
            if len(id_array) > 5:
                return False
            if friend.first_user_id == user_id:
                role_arr = []
                for role_e in roles:
                    st = select(UserRole).filter(UserRole.id == role_e["id"])
                    role = session.execute(st).scalar()
                    role_arr.append(role)
                friend.second_user_roles = role_arr
            else:
                role_arr = []
                for role_e in roles:
                    st = select(UserRole).filter(UserRole.id == role_e["id"])
                    role = session.execute(st).scalar()
                    role_arr.append(role)
                friend.first_user_roles = role_arr
            self.conn_handler.commit_needed = True
            return True

    def get_friend_roles(self, user_id: int, friend_id: int, all_roles: bool = False) -> list:
        with self.conn_handler as session:
            statement = self.FRIEND_STATEMENT(user_id, friend_id)
            friend = session.execute(statement).scalar()
            if not friend:
                return []

            if friend.first_user_id == user_id:
                roles = friend.second_user_roles
                roles = [role.serialize for role in roles]
            else:
                roles = friend.first_user_roles
                roles = [role.serialize for role in roles]
            if all_roles:
                roles = [role["role_name"] for role in roles]
                statement = select(UserRole).filter(UserRole.creator == user_id)
                user_roles = session.execute(statement).scalars()
                user_roles = [role.serialize for role in user_roles]
                for role in user_roles:
                    if role["role_name"] in roles:
                        role["is_active"] = True
                    else:
                        role["is_active"] = False
                return user_roles
            return roles

    def add_friend_role(self, user_id, friend_id, role_id):
        with self.conn_handler as session:
            statement = self.FRIEND_STATEMENT(user_id, friend_id)
            friend = session.execute(statement).scalar()

            statement = select(UserRole).filter(UserRole.id == role_id)
            role = session.execute(statement).scalar()

            if friend.first_user_id == user_id:
                if len(friend.second_user_roles) < 5:
                    friend.second_user_roles.append(role)
                    self.conn_handler.commit_needed = True
                    return True
                else:
                    return None
            elif friend.second_user_id == user_id:
                if len(friend.first_user_roles) < 5:
                    friend.first_user_roles.append(role)
                    self.conn_handler.commit_needed = True
                    return True
                else:
                    return None

    def remove_friend_role(self, user_id, friend_id, role_id):
        with self.conn_handler as session:
            statement = self.FRIEND_STATEMENT(user_id, friend_id)
            friend = session.execute(statement).scalar()

            statement = select(UserRole).filter(UserRole.id == role_id)
            role = session.execute(statement).scalar()

            if friend.first_user == user_id:
                friend.second_user_roles.remove(role)
            elif friend.second_user_id == user_id:
                friend.first_user_roles.remove(role)
            self.conn_handler.commit_needed = True

    def add_attachment_u_post(self, post_id: int, user_id: int, images_list):
        with self.conn_handler as session:
            attach = ImageAttachment(date_added=datetime.datetime.now(), a1_link=images_list[0])
            if len(images_list) > 1:
                attach.image_links = images_list[1:]
            statement = select(UserPost).filter(UserPost.id == post_id, UserPost.userid == user_id)
            post = session.execute(statement).scalar()
            post.attachment.append(attach)
            self.conn_handler.commit_needed = True

    def get_attachment_u_post(self, post_id: int, user_id: int):
        with self.conn_handler as session:
            statement = select(UserPost).filter(UserPost.id == post_id, UserPost.userid == user_id)
            post = session.execute(statement).scalar()
            return [att.serialize for att in post.attachment]

    def add_attachment_msg(self, msg_id: int, user_id: int, images_list):
        with self.conn_handler as session:
            attach = ImageAttachment(date_added=datetime.datetime.now(), a1_link=images_list[0])
            if len(images_list) > 1:
                attach.image_links = images_list[1:]
            statement = select(Message).filter(Message.id == msg_id, Message.from_user_id == user_id)
            message = session.execute(statement).scalar()
            message.attachment.append(attach)
            self.conn_handler.commit_needed = True

    def get_attachment_msg(self, msg_id: int, user_id: int):
        with self.conn_handler as session:
            statement = select(Message).filter(Message.id == msg_id, Message.from_user_id == user_id)
            msg = session.execute(statement).scalar()
            return [att.serialize for att in msg.attachment]

    def add_attachment_g_post(self, post_id: int, group_id: int, images_list):
        with self.conn_handler as session:
            attach = ImageAttachment(date_added=datetime.datetime.now(), a1_link=images_list[0])
            if len(images_list) > 1:
                attach.image_links = images_list[1:]
            statement = select(GroupPost).filter(GroupPost.id == post_id, GroupPost.group_id == group_id)
            message = session.execute(statement).scalar()
            message.attachment.append(attach)
            self.conn_handler.commit_needed = True

    def create_notification(self, user_id: int, chat_id: int, is_scoped: bool = False, scoped_session=None) -> bool:
        """
        This function creates notification with either chat_id.\n
        :param is_scoped:
        :param scoped_session:
        :param user_id: Id of user to whom this notification belongs
        :param chat_id: Id of chat to which this notification belongs
        :return: True if creating was successful, else False
        """
        notification = Notification(user_id=user_id)
        if is_scoped:
            scoped_session.add(notification)
            scoped_session.flush()
            scoped_session.refresh(notification)
            notification_link = NotificationChatLink(notification_id=notification.id, chat_id=chat_id)
            scoped_session.add(notification_link)
            self.conn_handler.commit_needed = True
            return True
        with self.conn_handler as session:
            session.add(notification)
            session.flush()
            session.refresh(notification)
            notification_link = NotificationChatLink(notification_id=notification.id, chat_id=chat_id)
            session.add(notification_link)
            self.conn_handler.commit_needed = True
            return True

    def get_chat_notification(self, user_id: int, chat_id: int) -> tuple[dict, dict]:
        """
        Gets Notification and NotificationChatLink by user id and chat id\n
        :param user_id: User.id id of user
        :param chat_id: Chat.id if of chat
        :return: tuple, first dict is Notification object and second dict is NotificationChatLink object
        """
        with self.conn_handler as session:
            st = select(Notification).filter(Notification.user_id == user_id).join(NotificationChatLink).filter(
                NotificationChatLink.chat_id == chat_id)
            notification = session.execute(st).scalar()

            st = select(NotificationChatLink).filter((NotificationChatLink.chat_id == chat_id) & (
                    NotificationChatLink.notification_id == notification.id))
            notification_link = session.execute(st).scalar()
            return notification.serialize, notification_link.serialize

    @staticmethod
    def __inc_msg_count_notification(notification_id: int, chat_id: int, message_count: int, session) -> int:
        st = select(NotificationChatLink).filter((NotificationChatLink.chat_id == chat_id) & (
                NotificationChatLink.notification_id == notification_id))
        notification_link = session.execute(st).scalar()
        notification_link.message_count += message_count
        return notification_link.message_count

    @staticmethod
    def __set_msg_count_notification(notification_id: int, chat_id: int, message_count: int, session) -> int:
        st = select(NotificationChatLink).filter((NotificationChatLink.chat_id == chat_id) & (
                NotificationChatLink.notification_id == notification_id))
        notification_link = session.execute(st).scalar()
        notification_link.message_count = message_count
        return notification_link.message_count


DBC = DataBase()
