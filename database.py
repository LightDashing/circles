from sqlalchemy import or_, and_
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import datetime
from models import User, UserPost, Message, Friend


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

    def change_username(self, oldname: str, newname: str):
        try:
            self.session.query(User).filter(User.username == oldname).update({User.username: newname})
            self.session.commit()
            return True
        except IntegrityError:
            return False

    def change_description(self, name: str, descrip: str):
        try:
            self.session.query(User).filter(User.username == name).update({User.description: descrip})
            self.session.commit()
            return True
        except IntegrityError:
            return False

    def change_mail(self, name: str, email: str):
        try:
            self.session.query(User).filter(User.username == name).update({User.email: email})
            self.session.commit()
            return True
        except IntegrityError:
            return False

    def ch_min_posting_lvl(self, name: str, lvl: int):
        try:
            self.session.query(User).filter(User.username == name).update({User.min_posting_lvl: lvl})
            self.session.commit()
            return True
        except IntegrityError:
            return False

    def change_publish_settings(self, name: str, publish: bool):
        try:
            self.session.query(User).filter(User.username == name).update({User.other_publish: publish})
            self.session.commit()
            return True
        except IntegrityError:
            return False

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

    def get_messages_with_user(self, name: str, username: str):
        name = self.get_userid_by_name(name)
        username = self.get_userid_by_name(username)
        messages = self.session.query(Message) \
            .filter(or_(and_(Message.userid == name, Message.fromuserid == username),
                        and_(Message.userid == username, Message.fromuserid == name))) \
            .order_by(Message.message_date).all()
        return messages

    def update_messages(self, f_user: str, s_user: str, msg_time: str) -> list:
        try:
            msg_time = datetime.datetime.strptime(msg_time, "%Y-%m-%d %H:%M:%S.%f")
        except TypeError:
            msg_time = datetime.datetime.now()
        f_user = self.get_userid_by_name(f_user)
        s_user = self.get_userid_by_name(s_user)
        messages = self.session.query(Message) \
            .filter(or_(and_(Message.userid == f_user, Message.fromuserid == s_user, Message.message_date > msg_time),
                        and_(Message.userid == s_user, Message.fromuserid == f_user, Message.message_date > msg_time))) \
            .order_by(Message.message_date).all()
        return messages

    def send_message(self, name: str, to: str, msg: str) -> bool:
        to = self.get_userid_by_name(to)
        name = self.get_userid_by_name(name)
        self.session.add(Message(userid=to, fromuserid=name, message=msg, message_date=datetime.datetime.now()))
        self.session.commit()
        return True

    def publish_post(self, msg: str, v_lvl: int, user: str, whereid: str = None, att: str = None) -> bool:
        userid = self.get_userid_by_name(user)
        if whereid:
            whereid = self.get_userid_by_name(whereid)
            self.session.add(UserPost(userid=userid, message=msg, view_level=v_lvl, attachment=att, whereid=whereid))
        else:
            self.session.add(UserPost(userid=userid, message=msg, view_level=v_lvl, attachment=att, whereid=userid))
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
