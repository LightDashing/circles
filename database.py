import time

from sqlalchemy import or_, and_, func, delete, select, update
from sqlalchemy.engine import create_engine
from sqlalchemy.pool import NullPool, AssertionPool, QueuePool
from sqlalchemy.orm import Session, sessionmaker, scoped_session
from sqlalchemy.exc import IntegrityError
import datetime
import re
from models import User, UserPost, Message, Friend, Chat, Group, GroupPost, UserGroupLink
from user_exceptions import UserAlreadyExist


class DataBase:
    class ConnectionHandler:

        def __init__(self):
            # ВНИМАНИЕ! AssertionPool разрешает только одно соединение и используется для тестирования
            # Для дальнейшей работы нужно будет подумать над пределами БД и сколько разрешать подключений
            # На данный момент всё работает относительно хорошо и стабильно
            self.engine = create_engine('postgresql://postgres:YourPassword@localhost/postgres',
                                        poolclass=AssertionPool)
            self.g_session = scoped_session(sessionmaker(self.engine))

        def __enter__(self):
            self.sp_sess = self.g_session()

        def __exit__(self, *args):
            try:
                self.sp_sess.commit()
            except IntegrityError:  # TODO: это просто затычка, нужно придумать что-то лучше
                self.sp_sess.rollback()
                raise UserAlreadyExist
            finally:
                self.g_session.remove()

    def __init__(self):
        self.conn_handler = self.ConnectionHandler()

    # TODO: пароль должен быть защищён, необходимо хранить пароль в солёном md5 хеше
    def add_user(self, username, email, password):
        try:
            with self.conn_handler:
                self.conn_handler.sp_sess.add(User(username=username, email=email, password=password))
            return True
        except UserAlreadyExist:
            return False

    def login_user(self, email: str, password: str):
        with self.conn_handler:
            statement = select(User).filter(User.email == email, User.password == password)
            user = self.conn_handler.sp_sess.execute(statement).first()
        if user:
            return True
        else:
            return False

    def set_online(self, user_id: int, online: bool):
        with self.conn_handler:
            statement = update(User).filter(User.id == user_id).values(is_online=online)
            self.conn_handler.sp_sess.execute(statement)

    def get_user(self, userid: int, scoped: bool = False) -> User:
        """
        This function returns user by their userid, if user exists. If user exists it's expunge him to be outside
        scoped session, so be careful when using this function on big arrays of data without scoped = True!\n
        :param userid: User.id
        :param scoped: If true, function will not create it's own scoped session, also it won't expunge it, default false
        :return: object User
        """
        if scoped:
            statement = select(User).filter(User.id == userid)
            user = self.conn_handler.sp_sess.execute(statement).scalar()
            return user

        with self.conn_handler:
            statement = select(User).filter(User.id == userid)
            user = self.conn_handler.sp_sess.execute(statement).scalar()
            self.conn_handler.sp_sess.expunge(user)
        return user

    def get_userid(self, email):
        with self.conn_handler:
            statement = select(User).filter(User.email == email)
            user = self.conn_handler.sp_sess.execute(statement).scalar()
            return user.id

    def userdata_by_name(self, userid: int):
        with self.conn_handler:
            statement = select(User).filter(User.id == userid)
            user = self.conn_handler.sp_sess.execute(statement).scalar()
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
        with self.conn_handler:
            statement = select(User).filter(User.username == new_name)
            if old_name == new_name:
                return 3
            elif self.conn_handler.sp_sess.execute(statement).first():
                return 1
            statement = update(User).filter(User.username == old_name).values(username=new_name)
            self.conn_handler.sp_sess.execute(statement)

    def change_description(self, user_id: int, desc: str) -> int:
        """
        This function changes user description, it returns one of the codes
        0: description was successfully changed
        -1: some unknown error occurred on database side
        """
        if not desc:
            desc = 'None was provided'
        with self.conn_handler:
            statement = update(User).filter(User.id == user_id).values(description=desc)
            self.conn_handler.sp_sess.execute(statement)
        return 0

    # TODO: ПеределатЬ!
    def change_mail(self, name: str, email: str) -> int:
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
        elif self.session.query(User).filter(User.username == name).first().email == email:
            return 3
        elif self.session.query(User).filter(User.email == email).first():
            return 2
        try:
            self.session.query(User).filter(User.username == name).update({User.email: email})
            self.session.commit()
            return 0
        except IntegrityError:
            return -1

    # TODO: переделать!
    def ch_min_posting_lvl(self, name: str, lvl: int) -> int:
        """
        his function changes minimum level other users need, to post on your wall, it returns one of the codes
        0: level was changed successfully
        1: level was incorrect
        -1: some unknown error occurred on database side
        """
        if lvl > 5 or lvl < 0:
            return 1
        try:
            self.session.query(User).filter(User.username == name).update({User.min_posting_lvl: lvl})
            self.session.commit()
            return 0
        except IntegrityError:
            return -1

    # TODO: переделать!
    def change_publish_settings(self, name: str, publish: bool) -> int:
        """
        This function can change if other users may post on your wall or not, it returns one of the codes
        0: publish settings was successfully changed
        1: some unknown error occurred on database side
        """
        try:
            self.session.query(User).filter(User.username == name).update({User.other_publish: publish})
            self.session.commit()
            return 0
        except IntegrityError:
            return -1

    # TODO: переделать!
    def change_avatar(self, userid: int, filepath: str):
        self.session.query(User).filter(User.id == userid).update({User.avatar: filepath})
        self.session.commit()

    def search_for(self, search_query: str, search_type: str = 'user') -> list[dict]:
        """
        This function search users by their name and then returns result with limit of 5 users\n
        :param search_query: str
        :param search_type: str, user or group
        :return: array of dicts, User.serialize
        """
        if search_type == 'user':
            with self.conn_handler:
                query = select(User).filter(User.username.like(f"%{search_query}%"))
                result = self.conn_handler.sp_sess.execute(query).scalars().fetchmany(5)
                users = [user.serialize for user in result]
        # TODO: сделать поиск по группам
        else:
            query = self.session.query().scalars()
        return users

    # TODO: сделать систему дозагрузки при прокрутке страницы
    def get_user_friends(self, userid: int, amount: int = 5) -> list[dict]:
        """
        This function returns user friends in specified amount\n
        :param userid: int, User.id
        :param amount: int, amount of friends to return
        :return: array of User.serialize
        """
        with self.conn_handler:
            statement = select(Friend).filter(or_(Friend.first_user_id == userid, Friend.second_user_id == userid))
            friends = self.conn_handler.sp_sess.execute(statement).scalars().fetchmany(amount)
            user_friends = []
            for friend in friends:
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
        :return: int, User.id or None if there was no user
        """
        if scoped:
            statement = select(User).filter(User.username == name)
            user = self.conn_handler.sp_sess.execute(statement).scalar()
            if user:
                return user.id

        with self.conn_handler:
            statement = select(User).filter(User.username == name)
            user = self.conn_handler.sp_sess.execute(statement).scalar()
            if user:
                return user.id

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
        with self.conn_handler:
            user = self.conn_handler.sp_sess.execute(statement).scalar()
            if user:
                return user.username

    def get_posts_by_id(self, username: str, view_level) -> list[UserPost]:
        """
        This function gets all posts on user page with specified view level\n
        :param username: str, User.username
        :param view_level: int, UserPost.view_level
        :return: list of UserPost objects or None if there was no UserPosts
        """
        user_id = self.get_userid_by_name(username)
        with self.conn_handler:
            statement = select(UserPost).filter(UserPost.whereid == user_id, UserPost.view_level >= view_level)
            posts = self.conn_handler.sp_sess.execute(statement).scalars()
            if posts:
                posts = [post.serialize for post in posts]
                return posts

    def get_avatar_by_name(self, username: str) -> str:
        with self.conn_handler:
            statement = select(User).filter(User.username == username)
            user = self.conn_handler.sp_sess.execute(statement).scalar()
            return user.avatar

    def get_user_chats(self, user_id: int) -> list:
        """
        This function is gets all chats which user are member of and returns their serialize property\n
        :param user_id: int
        :return: list[dict], "id", "chatname", "admin", "rules"
        """
        with self.conn_handler:
            statement = select(User).filter(User.id == user_id)
            user = self.conn_handler.sp_sess.execute(statement).scalar()
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
        with self.conn_handler:
            statement = select(User).filter(User.id == user_id)
            user = self.conn_handler.sp_sess.execute(statement).scalar()
            groups = []
            for group in user.groups:
                groups.append(group.serialize)
            return groups

    # TODO: переписать
    def create_group(self, username: str, group_name: str, group_desc: str, group_rules: str, group_tags: list = None):
        userid = self.get_userid_by_name(username)
        self.session.add(Group(group_name=group_name, owner=userid, fandom_tags=group_tags, description=group_desc,
                               rules=group_rules))
        self.session.commit()
        return True

    def join_group(self, group_name: str, current_user: User):
        """
        This function get current user and add him to group\n
        :param group_name: str
        :param current_user: User class
        :return: None
        """
        with self.conn_handler:
            statement = select(Group).filter(Group.group_name == group_name)
            group = self.conn_handler.sp_sess.execute(statement).scalar()
            group.users.append(current_user)

    def leave_group(self, group_name: str, current_user: User):
        """
        This function get current user and deletes him from group users list\n
        :param group_name: str
        :param current_user: User class
        :return: None
        """
        with self.conn_handler:
            statement = select(Group).filter(Group.group_name == group_name)
            group = self.conn_handler.sp_sess.execute(statement).scalar()
            group.users.remove(current_user)

    def is_joined(self, group_name: str, current_user: User) -> bool:
        """
        This function get current user and check if he is in the group users list\n
        :param group_name: str
        :param current_user: User class
        :return: True if user in group, False if isn't
        """
        test_user = current_user
        with self.conn_handler:
            assert test_user == current_user
            statement = select(Group).filter(Group.group_name == group_name)
            group = self.conn_handler.sp_sess.execute(statement).scalar()
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
        with self.conn_handler:
            statement = select(Group).filter(Group.group_name == group_name)
            group = self.conn_handler.sp_sess.execute(statement).scalar()
            return group.serialize

    def get_user_dialog(self, user_id: int, s_user_id: int) -> Chat:
        """
        This function gets chat (dialog) between two users and returns it, if there is no chats, it creates new\n
        :param user_id: int, User.id
        :param s_user_id: int, User.id
        :return: Chat object
        """
        with self.conn_handler:
            # This statement is to get both users entries
            statement = select(User).filter(or_(User.id == user_id, User.id == s_user_id))
            users = self.conn_handler.sp_sess.execute(statement).scalars().fetchmany(2)
            # This statement is to get all shared chats between users
            statement = select(Chat).join(User).filter(
                and_(Chat.users.any(id=users[0].id), Chat.users.any(id=users[1].id)))
            chats = self.conn_handler.sp_sess.execute(statement).scalars()
            for chat in chats:
                if chat.is_dialog:
                    return chat.serialize
        # If there are chat where is_dialog is True, then it's right chat, else we create new
        chat = self.create_dialog_chat(users[0], users[1])
        return chat

    def create_dialog_chat(self, user: User, s_user: User) -> Chat:
        """
        This function creates chat only for two users with "is_dialog" set to True, it's usual chat but in
        html it would be displayed as dialog\n
        :param user: User object
        :param s_user: User object
        :return: created Chat object
        """
        dialog = Chat(chatname=f"{user.username}, {s_user.username}", is_dialog=True)
        # chatname isn't really matters because in html it would be displayed as friends name
        with self.conn_handler:
            self.conn_handler.sp_sess.add(dialog)
            dialog.users.append(user), dialog.users.append(s_user)
            return dialog.serialize

    # TODO: redo, not all messages needs to be loaded, only like 30?
    def get_messages_chat_id(self, chat_id: int) -> list:
        """
        This function returns list with all messages in chat\n
        :param chat_id: int, Chat.id
        :return: list with all chat messages
        """
        with self.conn_handler:
            statement = select(Chat).filter(Chat.id == chat_id)
            chat = self.conn_handler.sp_sess.execute(statement).scalar()
            messages = [message.serialize for message in chat.messages]
            return messages

    def get_chat_by_id(self, chat_id: int) -> Chat:
        """
        This function returns Chat object by it's id\n
        :param chat_id: int, Chat.id
        :return: Chat object
        """
        print(type(chat_id))
        with self.conn_handler:
            statement = select(Chat).filter(Chat.id == chat_id)
            chat = self.conn_handler.sp_sess.execute(statement).scalar()
            return chat.serialize

    # TODO: переделать
    def create_chat(self, users: list, chat_name: str, admin: str, rules: str = "There is no rules!") -> int:
        admin_id = self.get_userid_by_name(admin)
        admin = self.get_user(admin_id)
        chat = Chat(chatname=chat_name, admin=admin_id, rules=rules)
        chat.users.append(admin)
        with self.conn_handler:
            self.conn_handler.sp_sess.add(chat)
            for user in users:
                user = self.get_user(self.get_userid_by_name(user, scoped=True), scoped=True)
                if user:
                    chat.users.append(user)
            return chat.id

    def load_messages(self, user: str, chat_id: int):
        userid = self.get_userid_by_name(user)
        with self.conn_handler:
            statement = select(Message).join(Chat).filter(Chat.id == chat_id)
            all_messages = self.conn_handler.sp_sess.execute(statement).all()
            messages = []
            for message in all_messages:
                message = message[0].serialize
                messages.append(message)
        return messages

    # TODO: переделать как-нибудь чтобы было не так затратно по ресурсам
    def update_messages(self, chat_id: int, msg_time: str):
        if not msg_time:
            msg_time = str(datetime.datetime.now())
        msg_time = datetime.datetime.strptime(msg_time, "%Y-%m-%d %H:%M:%S.%f")
        with self.conn_handler:
            statement = select(Message).join(Chat).filter(and_(Chat.id == chat_id, Message.message_date > msg_time))
            # statement = select(Chat).filter(Chat.id == chat_id)
            messages = self.conn_handler.sp_sess.execute(statement).all()
            all_messages = []
            if messages:
                # ВАЖНО! Какая-то странная ошибка, почему-то если я вызываю сначала get_name_by_userid, а лишь потом
                # message.serialize, то message открепляется от сессии и та сессия с которой текущей with просрачивается
                # Скорее всего это какой-то баг внутри sqlaclhemy, и при закрытии локальной сессии закрывается та,
                # которая находится внизу стека, а не вверху, другого объяснения почему так происходить я найти не могу
                for message in messages:
                    message = message[0].serialize
                    message['from_user_id'] = self.get_name_by_userid(message['from_user_id'])
                    all_messages.append(message)
            else:
                return []
        return all_messages

    def send_message(self, user: int, chat_id: int, msg: str) -> bool:
        with self.conn_handler:
            statement = select(Chat).filter(Chat.id == chat_id)
            chat = self.conn_handler.sp_sess.execute(statement).scalar()
            self.conn_handler.sp_sess.add(
                Message(from_user_id=user, message_date=datetime.datetime.now(), message=msg, chat_id=chat.id))
        return True

    def publish_post(self, msg: str, v_lvl: int, user: str, where_id: str = None, att: str = None) -> bool:
        userid = self.get_userid_by_name(user)
        if where_id:
            where_id = self.get_userid_by_name(where_id)
            with self.conn_handler:
                self.conn_handler.sp_sess.add(
                    UserPost(userid=userid, message=msg, view_level=v_lvl, attachment=att, whereid=where_id,
                             date_added=datetime.datetime.now()))
        else:
            with self.conn_handler:
                self.conn_handler.sp_sess.add(
                    UserPost(userid=userid, message=msg, view_level=v_lvl, attachment=att, whereid=userid,
                             date_added=datetime.datetime.now())
                )
        return True

    def add_friend(self, user: int, second_user: int) -> bool:
        """
        This function is checking if friend already exists and if it isn't, adds a new entry to database\n
        returns boolean value, true if new entry was created and false if entry already existed
        """
        with self.conn_handler:  # Checking if there already existing entry
            statement = select(Friend).filter(
                or_(and_(Friend.first_user_id == user, Friend.second_user_id == second_user),
                    and_(Friend.first_user_id == second_user, Friend.second_user_id == user)))
            users = self.conn_handler.sp_sess.execute(statement).scalar()
            if users:
                return False
            else:
                self.conn_handler.sp_sess.add(
                    Friend(first_user_id=user, second_user_id=second_user))  # Adding new entry
                return True

    def remove_friend(self, user: int, second_user: int) -> bool:
        """
        This function removes friend and decreases amount of friends both users have\n
        :param user: id of first user, usually current_user
        :param second_user: id of second user, someone else
        :return: True if deletion was successful, false if there was no friend entry
        """
        with self.conn_handler:
            statement = select(Friend).filter(
                or_(and_(Friend.first_user_id == user, Friend.second_user_id == second_user),
                    and_(Friend.first_user_id == second_user, Friend.second_user_id == user)))
            friend = self.conn_handler.sp_sess.execute(statement).scalar()  # Getting existing rows
            if not friend:  # If there is no friend entry like that
                return False
            if not friend.is_request:  # If friend already accepted
                statement = update(User).filter((User.id == user) | (User.id == second_user)).values(
                    friend_count=User.friend_count - 1)
                self.conn_handler.sp_sess.execute(statement)  # Decreasing number of friends
            statement = delete(Friend).filter((Friend.first_user_id == friend.first_user_id) &
                                              (Friend.second_user_id == friend.second_user_id))
            self.conn_handler.sp_sess.execute(statement)
            return True

    def accept_request(self, second_user: int, user: int) -> bool:
        """
        This function gets two users and finds a friend entry, updating it with is_request to False\n
        :param second_user: int, User.id
        :param user: int, User.id
        :return: True if updating was successful
        """
        with self.conn_handler:
            statement = update(Friend).filter(Friend.first_user_id == user, Friend.second_user_id == second_user) \
                .values(is_request=False, first_ulevel=4, second_ulevel=4)
            self.conn_handler.sp_sess.execute(statement)
            statement = update(User).filter((User.id == user) | (User.id == second_user)).values(
                friend_count=User.friend_count + 1)
            self.conn_handler.sp_sess.execute(statement)
        return True

    def is_friend(self, user: int, second_user: int):
        """
        This function checks if user is a friend of current user\n
        returns either a dict with all friend connection data or just bool false
        """
        with self.conn_handler:
            statement = select(Friend).filter(
                or_(and_(Friend.first_user_id == user, Friend.second_user_id == second_user),
                    and_(Friend.first_user_id == second_user, Friend.second_user_id == user)))
            friend = self.conn_handler.sp_sess.execute(statement).scalar()
            if not friend:
                return False
            else:
                return friend.serialize
