import time

from sqlalchemy import or_, and_, func, delete, select, update
from sqlalchemy.engine import create_engine
from sqlalchemy.pool import NullPool, AssertionPool, QueuePool
from sqlalchemy.orm import Session, sessionmaker, scoped_session
from sqlalchemy.exc import IntegrityError
import datetime
import re
from models import User, UserPost, Message, Friend, Chat, Group, GroupPost, UserGroupLink, UserChatLink, UserRole, \
    ImageAttachment
from files import FileOperations
from user_exceptions import UserAlreadyExist


class DataBase:
    class ConnectionHandler:

        def __init__(self):
            # Нужно поиграться с параметрами пула, потому что сейчас переодически сыпется с twophase error
            self.engine = create_engine('postgresql://postgres:YourPassword@localhost/postgres',
                                        **{"poolclass": QueuePool, "pool_size": 4, "max_overflow": 1,
                                           "pool_timeout": 10})
            self.g_session = scoped_session(sessionmaker(self.engine))

        def __enter__(self):
            self.sp_sess = self.g_session()

        def __exit__(self, *args):
            try:
                self.sp_sess.commit()
            except IntegrityError:  # TODO: это просто затычка, нужно придумать что-то лучше
                self.sp_sess.rollback()
            finally:
                self.g_session.remove()

    def __init__(self):
        self.conn_handler = self.ConnectionHandler()
        # Для удобства, здесь будут константы для часто использующихся запросов
        self.FRIEND_STATEMENT = lambda x, y: select(Friend).filter(
            ((Friend.first_user_id == x) & (Friend.second_user_id == y)) |
            ((Friend.first_user_id == y) & (Friend.second_user_id == x)))

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

    def userdata_by(self, userid: int):
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
        with self.conn_handler:
            statement = select(User).filter(User.username == name)
            user = self.conn_handler.sp_sess.execute(statement).scalar()
            if user.email == email:
                return 3

            statement = select(User).filter(User.email == email)
            user = self.conn_handler.sp_sess.execute(statement).scalar()
            if user.email == email:
                return 2

            statement = update(User).filter(User.username == name).values(email=email)
            self.conn_handler.sp_sess.execute(statement)
            return 0

    # TODO: Когда будет добавлена система ролей эта штука будет переработана
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
    def change_publish_settings(self, name: str, publish: bool) -> bool:
        """
        This function can change if other users may post on your wall or not, it returns one of the codes\n
        :param name: user nickname
        :param publish: boolean, true or false, can other post or not
        :return: true if operation was successful
        """
        with self.conn_handler:
            statement = update(User).filter(User.username == name).values(other_publish=publish)
            return True

    def change_avatar(self, userid: int, filepath: str):
        """
        This function changes filepath to user avatar on server in database entry\n
        :param userid: id of user which avatar you need to change, User.id
        :param filepath: path of new file in server filesystem relative to server directory
        :return: true if operation was successful
        """
        with self.conn_handler:
            statement = update(User).filter(User.id == userid).values(avatar=filepath)
            self.conn_handler.sp_sess.execute(statement)

    # TODO: доделать функцию
    def update_all(self, userid):
        updates = {}
        with self.conn_handler:
            # user = self.get_user(userid, True)

            statement = select(Friend).filter((Friend.is_checked == False) & (Friend.second_user_id == userid))
            friends = self.conn_handler.sp_sess.execute(statement).all()
            friends_arr = []
            for friend in friends:
                friend = friend[0].serialize
                friend["first_user_id"] = self.get_name_by_userid(friend["first_user_id"], True)
                friends_arr.append(friend)
            updates["friends"] = len(friends_arr)

            statement = select(Message).join(Chat).join(UserChatLink).filter((UserChatLink.user_id == userid) &
                                                                             (UserChatLink.is_muted != True) &
                                                                             (UserChatLink.last_visited <
                                                                              datetime.datetime.now()) &
                                                                             (Message.message_date >
                                                                              UserChatLink.last_visited) &
                                                                             (UserChatLink.is_notified == False))

            messages = self.conn_handler.sp_sess.execute(statement).all()
            updates['messages'] = len(messages)

            statement = update(UserChatLink).filter(UserChatLink.user_id == userid).values(is_notified=True)
            self.conn_handler.sp_sess.execute(statement)
            return updates

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

    def search_role(self, search_query: str, user_id: int) -> list[dict]:
        """
        This function is searching for
        :param search_query:
        :param user_id:
        :return:
        """
        with self.conn_handler:
            query = select(UserRole).filter(UserRole.role_name.like(f"%{search_query}%"), UserRole.creator == user_id)
            results = self.conn_handler.sp_sess.execute(query).scalars()
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

    def get_your_posts(self, user_id):
        with self.conn_handler:
            statement = select(UserPost).filter(UserPost.whereid == user_id)
            posts = self.conn_handler.sp_sess.execute(statement)
            if posts:
                posts = [post[0].serialize for post in posts]
                return posts[::-1]

    def get_posts_by_id(self, username: str, user_roles: list[str]) -> list[UserPost]:
        """
        This function gets all posts on user page with specified view level\n
        :param user_roles:
        :param username: str, User.username
        :return: list of UserPost objects or None if there was no UserPosts
        """
        user_id = self.get_userid_by_name(username)
        with self.conn_handler:
            if not user_roles:
                statement = select(UserPost).filter(UserPost.whereid == user_id, UserPost.is_private == False)
                posts = self.conn_handler.sp_sess.execute(statement).all()
                if posts:
                    s_posts = [post[0].serialize for post in posts]
            else:
                statement = select(UserPost).filter(UserPost.whereid == user_id)
                posts = self.conn_handler.sp_sess.execute(statement).all()
                s_posts = []
                for post in posts:
                    role_names = [role.role_name for role in post[0].roles]
                    if self.is_arr_part(role_names, user_roles):
                        s_posts.append(post[0].serialize)
            return s_posts[::-1]

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
            statement = select(Chat).filter(Chat.users.contains(users[0]) & (Chat.users.contains(users[1])))
            chats = self.conn_handler.sp_sess.execute(statement).all()
            for chat in chats:
                if chat[0].is_dialog:
                    return chat[0].serialize
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
        dialog = Chat(chatname=f"{user.username} {s_user.username}", is_dialog=True)
        # chatname isn't really matters because in html it would be displayed as friends name
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
            if chat:
                messages = [message.serialize for message in chat.messages]
            else:
                messages = []
            return messages

    def get_chat_by_id(self, chat_id: int) -> Chat:
        """
        This function returns Chat object by it's id\n
        :param chat_id: int, Chat.idf
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
            statement = update(UserChatLink).filter(UserChatLink.user_id == userid).values(is_notified=True)
            statement = select(Message).join(Chat).filter(Chat.id == chat_id)
            all_messages = self.conn_handler.sp_sess.execute(statement).all()
            messages = []
            for message in all_messages:
                message = message[0].serialize
                messages.append(message)
        return messages

    # TODO: переделать как-нибудь чтобы было не так затратно по ресурсам
    def update_messages(self, chat_id: int, msg_time: str, user_id: int):
        if not msg_time:
            msg_time = str(datetime.datetime.now())
        msg_time = datetime.datetime.strptime(msg_time, "%Y-%m-%d %H:%M:%S.%f")
        with self.conn_handler:
            statement = select(UserChatLink).filter(UserChatLink.user_id == user_id, UserChatLink.chat_id == chat_id)
            users = self.conn_handler.sp_sess.execute(statement).scalar()
            if not users:
                return []

            statement = select(Message).join(Chat).filter(and_(Chat.id == chat_id, Message.message_date > msg_time))
            messages = self.conn_handler.sp_sess.execute(statement).all()

            statement = update(UserChatLink).filter(
                (UserChatLink.user_id == user_id) & (UserChatLink.chat_id == chat_id)).values(
                last_visited=datetime.datetime.now())
            self.conn_handler.sp_sess.execute(statement)

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

    @staticmethod
    def create_attach(user_id: int, pinned_images: list[str]) -> ImageAttachment:
        files = FileOperations(user_id)
        image = files.save_image(pinned_images[0])
        attach = ImageAttachment(a1_link=image, date_added=datetime.datetime.now())

        if len(pinned_images) > 1:
            attach_array = []
            for i in range(1, 5):
                try:
                    attach_array.append(files.save_image(pinned_images[i]))
                except IndexError:
                    break
            attach.image_links = attach_array
        return attach

    def send_message(self, user_id: int, chat_id: int, msg: str, pinned_images: list[str]) -> bool:
        with self.conn_handler:
            statement = select(Chat).filter(Chat.id == chat_id)
            chat = self.conn_handler.sp_sess.execute(statement).scalar()
            message = Message(from_user_id=user_id, message_date=datetime.datetime.now(), message=msg, chat_id=chat.id)
            if pinned_images:
                attach = self.create_attach(user_id, pinned_images)
                message.attachment.append(attach)
            self.conn_handler.sp_sess.add(message)
            statement = update(UserChatLink).filter(UserChatLink.chat_id == chat_id).values(is_notified=False)
            self.conn_handler.sp_sess.execute(statement)
        return True

    # TODO: добавить ограничение на количество ролей в посте
    #  также нужно переработать этот код
    def publish_post(self, msg: str, user_id: int, roles: list[str], pinned_images: list[str], is_private: bool,
                     where_id: int = None) -> bool:
        with self.conn_handler:
            if not where_id:
                if not is_private:
                    post = UserPost(userid=user_id, message=msg, whereid=user_id, is_private=is_private,
                                    date_added=datetime.datetime.now())
                else:
                    post = UserPost(userid=user_id, message=msg, whereid=user_id, is_private=is_private,
                                    date_added=datetime.datetime.now())
                    for role in roles:
                        statement = select(UserRole).filter(UserRole.role_name == role)
                        role = self.conn_handler.sp_sess.execute(statement).scalar()
                        post.roles.append(role)
                if pinned_images:
                    attach = self.create_attach(user_id, pinned_images)
                    post.attachment.append(attach)
            else:
                # TODO: пока что другие люди не могут постить на стене вообще, нужно придумать как поступать с их
                #  ролями в случае постинга
                pass
            self.conn_handler.sp_sess.add(post)
            self.conn_handler.sp_sess.flush()
            self.conn_handler.sp_sess.refresh(post)
            return post.serialize

    def remove_post(self, post_id):
        with self.conn_handler:
            statement = delete(UserPost).filter(UserPost.id == post_id)
            self.conn_handler.sp_sess.execute(statement)

    def get_your_post(self, post_id, user_id):
        with self.conn_handler:
            statement = select(UserPost).filter(UserPost.id == post_id, UserPost.userid == user_id)
            post = self.conn_handler.sp_sess.execute(statement).scalar()
            return post.serialize

    def create_role(self, role_name: str, role_color: str, user_id: int):
        # TODO: добавить донаты для монетизации, максимальное кол-во ролей для обычного пользователя - 5
        #  для людей которые задонатили можно сделать до 10
        with self.conn_handler:
            statement = select(UserRole).filter(UserRole.creator == user_id)
            roles = self.conn_handler.sp_sess.execute(statement).all()
            if len(roles) < 6:
                user_role = UserRole(role_name=role_name, role_color=role_color, creator=user_id)
                self.conn_handler.sp_sess.add(user_role)
                self.conn_handler.sp_sess.flush()
                self.conn_handler.sp_sess.refresh(user_role)
                return user_role.serialize
            else:
                return False

    def delete_role(self, role_id: int, user_id: int):
        with self.conn_handler:
            statement = delete(UserRole).filter(UserRole.id == role_id, UserRole.creator == user_id)
            self.conn_handler.sp_sess.execute(statement)

    def get_roles(self, user_id: int) -> list[dict]:
        with self.conn_handler:
            statement = select(UserRole).filter(UserRole.creator == user_id)
            user_roles = self.conn_handler.sp_sess.execute(statement).all()
            user_roles = [role[0].serialize for role in user_roles]
        return user_roles

    def change_role(self, role_id: int, user_id: int, new_role_name: str = None, new_role_color: str = None,
                    new_font_color: str = None) -> dict:
        with self.conn_handler:
            statement = select(UserRole).filter(UserRole.creator == user_id, UserRole.id == role_id)
            user_role = self.conn_handler.sp_sess.execute(statement).scalar()
            if user_role:
                if new_role_name:
                    user_role.role_name = new_role_name
                if new_role_color:
                    user_role.role_color = new_role_color
                if new_font_color:
                    user_role.font_color = new_font_color
                return user_role.serialize
            else:
                return {}

    def add_friend(self, user: int, second_user: int) -> bool:
        """
        This function is checking if friend already exists and if it isn't, adds a new entry to database\n
        returns boolean value, true if new entry was created and false if entry already existed
        """
        with self.conn_handler:  # Checking if there already existing entry
            statement = self.FRIEND_STATEMENT(user, second_user)
            users = self.conn_handler.sp_sess.execute(statement).all()
            if users:
                return False
            else:
                self.conn_handler.sp_sess.add(
                    Friend(first_user_id=user, second_user_id=second_user,
                           date_added=datetime.datetime.now()))  # Adding new entry
                return True

    def remove_friend(self, user: int, second_user: int) -> bool:
        """
        This function removes friend and decreases amount of friends both users have\n
        :param user: id of first user, usually current_user
        :param second_user: id of second user, someone else
        :return: True if deletion was successful, false if there was no friend entry
        """
        with self.conn_handler:
            statement = self.FRIEND_STATEMENT(user, second_user)
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
            statement = self.FRIEND_STATEMENT(user, second_user)
            friend = self.conn_handler.sp_sess.execute(statement).scalar()
            if not friend:
                return False
            else:
                return friend.serialize

    def get_friend_roles(self, user_id, friend_id):
        with self.conn_handler:
            statement = self.FRIEND_STATEMENT(user_id, friend_id)
            friend = self.conn_handler.sp_sess.execute(statement).scalar()
            if not friend:
                return

            if friend.first_user_id == user_id:
                roles = friend.second_user_roles
                roles = [role.serialize for role in roles]
                return roles
            elif friend.second_user_id == user_id:
                roles = friend.first_user_roles
                roles = [role.serialize for role in roles]
                return roles

    def add_friend_role(self, user_id, friend_id, role_id):
        with self.conn_handler:
            statement = self.FRIEND_STATEMENT(user_id, friend_id)
            friend = self.conn_handler.sp_sess.execute(statement).scalar()

            statement = select(UserRole).filter(UserRole.id == role_id)
            role = self.conn_handler.sp_sess.execute(statement).scalar()

            if friend.first_user == user_id:
                if len(friend.second_user_roles) < 5:
                    friend.second_user_roles.append(role)
                else:
                    return None
            elif friend.second_user_id == user_id:
                if len(friend.first_user_roles) < 5:
                    friend.first_user_roles.append(role)
                else:
                    return None

    def remove_friend_role(self, user_id, friend_id, role_id):
        with self.conn_handler:
            statement = self.FRIEND_STATEMENT(user_id, friend_id)
            friend = self.conn_handler.sp_sess.execute(statement).scalar()

            statement = select(UserRole).filter(UserRole.id == role_id)
            role = self.conn_handler.sp_sess.execute(statement).scalar()

            if friend.first_user == user_id:
                friend.second_user_roles.remove(role)
            elif friend.second_user_id == user_id:
                friend.first_user_roles.remove(role)

    def add_attachment_u_post(self, post_id: int, user_id: int, images_list):
        with self.conn_handler:
            attach = ImageAttachment(date_added=datetime.datetime.now(), a1_link=images_list[0])
            if len(images_list) > 1:
                attach.image_links = images_list[1:]
            statement = select(UserPost).filter(UserPost.id == post_id, UserPost.userid == user_id)
            post = self.conn_handler.sp_sess.execute(statement).scalar()
            post.attachment.append(attach)

    def get_attachment_u_post(self, post_id: int, user_id: int):
        with self.conn_handler:
            statement = select(UserPost).filter(UserPost.id == post_id, UserPost.userid == user_id)
            post = self.conn_handler.sp_sess.execute(statement).scalar()
            return [att.serialize for att in post.attachment]

    def add_attachment_msg(self, msg_id: int, user_id: int, images_list):
        with self.conn_handler:
            attach = ImageAttachment(date_added=datetime.datetime.now(), a1_link=images_list[0])
            if len(images_list) > 1:
                attach.image_links = images_list[1:]
            statement = select(Message).filter(Message.id == msg_id, Message.from_user_id == user_id)
            message = self.conn_handler.sp_sess.execute(statement).scalar()
            message.attachment.append(attach)

    def get_attachment_msg(self, msg_id: int, user_id: int):
        with self.conn_handler:
            statement = select(Message).filter(Message.id == msg_id, Message.from_user_id == user_id)
            msg = self.conn_handler.sp_sess.execute(statement).scalar()
            return [att.serialize for att in msg.attachment]

    def add_attachment_g_post(self, post_id: int, group_id: int, images_list):
        with self.conn_handler:
            attach = ImageAttachment(date_added=datetime.datetime.now(), a1_link=images_list[0])
            if len(images_list) > 1:
                attach.image_links = images_list[1:]
            statement = select(GroupPost).filter(GroupPost.id == post_id, GroupPost.group_id == group_id)
            message = self.conn_handler.sp_sess.execute(statement).scalar()
            message.attachment.append(attach)
