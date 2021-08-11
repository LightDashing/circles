from sqlalchemy import or_, and_, func
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import datetime
import re
from models import User, UserPost, Message, Friend, Chat, Group, GroupPost, UserGroupLink


class OpenConnectionToBD:

    def __init__(self, db):
        self.db = db

    def __enter__(self):
        self.db.session = Session(bind=self.db.engine)

    # TODO: Почему exit принимает 3 пустых аргумента none none none?
    def __exit__(self, x1, x2, x3):
        self.db.close()


class DataBase:
    def __init__(self):
        # self.engine = create_engine('postgresql://postgres:YourPassword@localhost/postgres')
        # self.engine = create_engine('sqlite:///test.db')
        self.session = None

    def close(self):
        self.session.close()

    # TODO: пароль должен быть защищён, необходимо хранить пароль в солёном md5 хеше
    def add_user(self, username, email, password):
        self.session.add(User(username=username, email=email, password=password))
        try:
            self.session.commit()
            return True
        except IntegrityError:
            return False

    def login_user(self, email: str, password: str):
        user = self.session.query(User).filter(User.email == email, User.password == password).first()
        if user:
            return True
        else:
            return False

    def name_by_mail(self, email: str):
        user = self.session.query(User).filter(User.email == email).first()
        if user:
            return user.username
        else:
            return False

    def userdata_by_name(self, name: str):
        user = self.session.query(User).filter(User.username == name).first()
        if user:
            return {"friends_count": user.friend_count, "avatar": user.avatar, "description": user.description,
                    "can_post": user.other_publish, "email": user.email, "success": True,
                    "min_post_lvl": user.min_posting_lvl}
        else:
            return {"success": False}

    def change_username(self, old_name: str, new_name: str) -> int:
        """This function changes username, returns one of the codes
        0: username was changed successfully
        1: user with that username already exists
        2: username length is incorrect
        3: new username same as old username
        -1: some unknown error occurred on database side"""
        if not new_name or len(new_name) < 3 or len(new_name) > 30:
            return 2
        if old_name == new_name:
            return 3
        elif self.session.query(User).filter(User.username == new_name).first():
            return 1
        try:
            self.session.query(User).filter(User.username == old_name).update({User.username: new_name})
            self.session.commit()
            return 0
        except IntegrityError:
            return -1

    def change_description(self, name: str, desc: str) -> int:
        """This function changes user description, it returns one of the codes
        0: description was successfully changed
        -1: some unknown error occurred on database side"""
        if not desc:
            desc = 'None was provided'
        try:
            self.session.query(User).filter(User.username == name).update({User.description: desc})
            self.session.commit()
            return 0
        except IntegrityError:
            return -1

    def change_mail(self, name: str, email: str) -> int:
        """This function changes user e-mail, it returns one of the codes
        0: email was successfully changed
        1: email isn't valid
        2: there already exist user with such email
        3: new email same as old email
        -1: some unknown error occurred on database side"""
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

    def ch_min_posting_lvl(self, name: str, lvl: int) -> int:
        """This function changes minimum level other users need, to post on your wall, it returns one of the codes
        0: level was changed successfully
        1: level was incorrect
        -1: some unknown error occurred on database side"""
        if lvl > 5 or lvl < 0:
            return 1
        try:
            self.session.query(User).filter(User.username == name).update({User.min_posting_lvl: lvl})
            self.session.commit()
            return 0
        except IntegrityError:
            return -1

    def change_publish_settings(self, name: str, publish: bool) -> int:
        """This function can change if other users may post on your wall or not, it returns one of the codes
        0: publish settings was successfully changed
        1: some unknown error occurred on database side"""
        try:
            self.session.query(User).filter(User.username == name).update({User.other_publish: publish})
            self.session.commit()
            return 0
        except IntegrityError:
            return -1

    def change_avatar(self, userid: int, filepath: str):
        self.session.query(User).filter(User.id == userid).update({User.avatar: filepath})
        self.session.commit()

    def get_userid_by_name(self, name: str):
        user = self.session.query(User).filter(User.username == name).first()
        if user:
            return user.id
        else:
            return False

    def get_name_by_userid(self, id: int):
        user = self.session.query(User).filter(User.id == id).first()
        if user:
            return user.username
        else:
            return False

    def get_posts_by_id(self, username: str, view_level):
        userid = self.get_userid_by_name(username)
        posts = self.session.query(UserPost).filter(UserPost.whereid == userid, UserPost.view_level >= view_level).all()
        if posts:
            return posts
        else:
            return False

    def get_avatar_by_name(self, username: str) -> str:
        user = self.session.query(User).filter(User.username == username).first()
        return user.avatar

    def get_user_chats(self, name: str) -> list:
        userid = self.get_userid_by_name(name)
        chats = self.session.query(Chat).filter(Chat.userids.contains([userid])).all()
        return chats

    def get_user_groups(self, name: str) -> list:
        user = self.session.query(User).filter(User.username == name).first()
        user_groups = self.session.query(Group).filter(Group.users.contains(user)).all()
        return user_groups
        # userid = self.get_userid_by_name(name)
        # usergroups = self.session.query(UserGroupLink).filter(UserGroupLink.user_id == userid).all()
        # groups = []
        # for group in usergroups:
        #     groups.append(self.session.query(Group).filter(Group.id == group.id).first())
        # return groups

    def create_group(self, username: str, group_name: str, group_desc: str, group_rules: str, group_tags: list = None):
        userid = self.get_userid_by_name(username)
        self.session.add(Group(group_name=group_name, owner=userid, fandom_tags=group_tags, description=group_desc,
                               rules=group_rules))
        self.session.commit()
        return True

    def join_group(self, username, group_name):
        group = self.session.query(Group).filter(Group.group_name == group_name).first()
        user = self.session.query(User).filter(User.username == username).first()
        group.users.append(user)
        self.session.commit()

    def leave_group(self, username, group_name):
        group = self.session.query(Group).filter(Group.group_name == group_name).first()
        user = self.session.query(User).filter(User.username == username).first()
        group.users.remove(user)
        self.session.commit()

    def is_joined(self, username, group_name):
        group = self.session.query(Group).filter(Group.group_name == group_name).first()
        user = self.session.query(User).filter(User.username == username).first()
        if user in group.users:
            return True
        else:
            return False

    def get_group_data(self, group_name: str):
        group = self.session.query(Group).filter(Group.group_name == group_name).first()
        return group

    def create_dialog_chat(self, name: str, username: str) -> str:
        userid = self.get_userid_by_name(name)
        s_userid = self.get_userid_by_name(username)
        chat = Chat(chatname=str(name + ", " + username), userids=[userid, s_userid])
        self.session.add(chat)
        user = self.session.query(User).filter(User.id == userid).first()
        user.chats.append(chat)
        user = self.session.query(User).filter(User.id == s_userid).first()
        user.chats.append(chat)
        self.session.commit()
        return str(name + ", " + username + str(chat.id))

    def get_messages_chatid(self, chatid: int) -> list:
        chat = self.session.query(Chat).filter(Chat.id == chatid).first()
        return chat.messages

    def get_chat_byid(self, chatid: int) -> Chat:
        chat = self.session.query(Chat).filter(Chat.id == chatid).first()
        return chat

    def create_chat(self, users: list, chat_name: str, admin: str, rules: str = None, fandoms: list = None,
                    moderators: list = None) -> int:
        admin = self.get_userid_by_name(admin)
        for i in range(len(users)):
            users[i] = self.get_userid_by_name(users[i])
        if moderators:
            for i in range(len(moderators)):
                moderators[i] = self.get_userid_by_name(moderators[i])
        chat = Chat(chatname=chat_name, userids=users, admin=admin, moders=moderators, rules=rules, fandom_tags=fandoms)
        self.session.add(chat)
        for userid in users:
            user = self.session.query(User).filter(User.id == userid).first()
            user.chats.append(chat)
        self.session.commit()
        return chat.id

    def get_messages_with_user(self, name: str, username: str):
        userid = self.get_userid_by_name(name)
        s_userid = self.get_userid_by_name(username)
        chat = self.session.query(Chat).filter(Chat.userids.contains([userid, s_userid]),
                                               func.array_length(Chat.userids, 1) == 2).first()
        if chat:
            messages = [0, []]
            for message in chat.messages:
                messages[1].append(
                    {"user": self.get_name_by_userid(message.fromuserid), "message": message.message,
                     "attachment": message.attachments,
                     "date": message.message_date})
                messages[0] = str(message.message_date)
            return messages
        else:
            chat_name = self.create_dialog_chat(name, username)
            return [{"chat-name": chat_name, 'messages': None}]

    def get_dialog_chat_id(self, name: str, username: str) -> int:
        userid = self.get_userid_by_name(name)
        s_userid = self.get_userid_by_name(username)
        chat = self.session.query(Chat).filter(Chat.userids.contains([userid, s_userid]),
                                               func.array_length(Chat.userids, 1) == 2).first()
        return chat.id

    def load_messages(self, user: str, chat_id: int):
        userid = self.get_userid_by_name(user)
        chat = self.session.query(Chat).filter(Chat.id == chat_id).first()
        if chat.messages:
            for message in chat.messages:
                message.fromuserid = self.get_name_by_userid(message.fromuserid)
            return chat.messages
        else:
            return False

    def update_messages(self, chat_id: int, msg_time: str):
        if not msg_time:
            msg_time = str(datetime.datetime.now())
        msg_time = datetime.datetime.strptime(msg_time, "%Y-%m-%d %H:%M:%S.%f")
        chat = self.session.query(Chat).filter(Chat.id == chat_id).first()
        new_messages = [0, []]
        for message in chat.messages:
            if message.message_date > msg_time:
                new_messages[1].append(
                    {"user": self.get_name_by_userid(message.fromuserid), "message": message.message,
                     "attachment": message.attachments,
                     "date": message.message_date})
            new_messages[0] = str(message.message_date)
        return new_messages

    def send_message(self, user: str, chat_id: int, msg: str, attachment: str = None) -> bool:
        userid = self.get_userid_by_name(user)
        chat = self.session.query(Chat).filter(Chat.id == chat_id).first()
        self.session.add(Message(fromuserid=userid, message_date=datetime.datetime.now(), message=msg, chat_id=chat.id,
                                 attachments=attachment))
        self.session.commit()
        return True

    def publish_post(self, msg: str, v_lvl: int, user: str, whereid: str = None, att: str = None) -> bool:
        userid = self.get_userid_by_name(user)
        if whereid:
            whereid = self.get_userid_by_name(whereid)
            self.session.add(UserPost(userid=userid, message=msg, view_level=v_lvl, attachment=att, whereid=whereid,
                                      date_added=datetime.datetime.now()))
        else:
            self.session.add(UserPost(userid=userid, message=msg, view_level=v_lvl, attachment=att, whereid=userid,
                                      date_added=datetime.datetime.now()))
        self.session.commit()
        return True

    def return_friendslist(self, user: str) -> dict:
        userid = self.get_userid_by_name(user)
        friends = self.session.query(Friend).filter(and_(or_(Friend.first_user == userid, Friend.second_user == userid), \
                                                         Friend.is_request == False)).order_by(Friend.date_added).all()
        if friends:
            friendlist = []
            for friend in friends:
                friend_dict = {}
                if friend.first_user == userid:
                    friend_dict['name'] = self.get_name_by_userid(friend.second_user)
                    frienddata = self.userdata_by_name(friend_dict['name'])
                else:
                    friend_dict['name'] = self.get_name_by_userid(friend.first_user)
                    frienddata = self.userdata_by_name(friend_dict['name'])
                friend_dict['avatar'] = frienddata['avatar']
                # TODO: добавить в таблицу пользователей колонку статуса
                # friend['status'] = frienddata['status']
                friendlist.append(friend_dict)
            return {"success": True, "friendslist": friendlist}
        else:
            return {"success": False}

    def add_friend(self, user, second_user):
        #  TODO: Пофиксить ошибку, из-за которой можно одновременно нажать на кнопку и добавить в друзья с двух сторон
        user = self.get_userid_by_name(user)
        second_user = self.get_userid_by_name(second_user)
        self.session.add(Friend(first_user=user, second_user=second_user))
        self.session.commit()
        return True

    # TODO: при отмене запроса, кол-во друзей не нужно уменьшать
    def remove_friend(self, user, second_user):
        user = self.get_userid_by_name(user)
        second_user = self.get_userid_by_name(second_user)
        self.session.query(Friend).filter(Friend.first_user == user, Friend.second_user == second_user).delete()
        self.session.query(Friend).filter(Friend.first_user == second_user, Friend.second_user == user).delete()
        self.session.query(User).filter(User.id == user).update({User.friend_count: User.friend_count - 1})
        self.session.query(User).filter(User.id == second_user).update({User.friend_count: User.friend_count - 1})
        self.session.commit()
        return True

    def accept_request(self, user, second_user):
        userid = self.get_userid_by_name(user)
        s_userid = self.get_userid_by_name(second_user)
        self.session.query(Friend).filter(Friend.first_user == userid, Friend.second_user == s_userid).update(
            {Friend.is_request: False, Friend.first_ulevel: 4, Friend.second_ulevel: 4})
        self.session.query(User).filter(User.id == userid).update({User.friend_count: User.friend_count + 1})
        self.session.query(User).filter(User.id == s_userid).update({User.friend_count: User.friend_count + 1})
        self.session.commit()
        return True

    def is_friend(self, user: str, second_user: str) -> dict:
        userid = self.get_userid_by_name(user)
        s_userid = self.get_userid_by_name(second_user)
        req = self.session.query(Friend).filter(Friend.first_user == userid, Friend.second_user == s_userid).first()
        if req:
            if not req.is_request:
                return {"friend": True, "request": False, "sent_by": user, "u1_lvl": req.second_ulevel,
                        "u2_lvl": req.first_ulevel}
            else:
                return {"friend": True, "request": True, "sent_by": user, "u1_lvl": 5}
        req = self.session.query(Friend).filter(Friend.first_user == s_userid, Friend.second_user == userid).first()
        if req:
            if not req.is_request:
                return {"friend": True, "request": False, "sent_by": second_user, "u1_lvl": req.first_ulevel,
                        "u2_lvl": req.second_ulevel}
            else:
                return {"friend": True, "request": True, "sent_by": second_user, "u1_lvl": 5}
        return {"friend": False, "request": False, "sent_by": None, "u1_lvl": 5}
