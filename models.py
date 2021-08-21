from sqlalchemy import Column, INTEGER, Text, ForeignKey, DateTime, Boolean, or_, and_, Index
from sqlalchemy.dialects.postgresql import VARCHAR
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from flask_login import UserMixin
import datetime

Base = declarative_base()


# TODO: ВАЖНО! вернуть ограничения по полям, сделать его большим, но существующим, чтобы нельзя было сохранять
#  десятки мегабайт текста

class User(UserMixin, Base):
    __tablename__ = 'users'
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    username = Column(VARCHAR(30), unique=True, nullable=False)
    email = Column(VARCHAR(30), unique=True, nullable=False)
    password = Column(VARCHAR(512), nullable=False)
    registration_date = Column(DateTime, nullable=False, default=datetime.datetime.now())
    last_time_online = Column(DateTime, nullable=False)
    is_online = Column(Boolean)
    # email_active = Column(Boolean, nullable=False, default=False)
    description = Column(VARCHAR())
    status = Column(VARCHAR(30), nullable=False, default=' ')
    avatar = Column(VARCHAR(128), default='..\\static\\img\\user-avatar.svg')
    friend_count = Column(INTEGER, nullable=False, default=0)
    # Могут ли другие люди оставлять у этого пользователя записи на стене
    other_publish = Column(Boolean, nullable=False, default=True)
    # Здесь можно указать уровень людей, способных постить на стене
    min_posting_lvl = Column(INTEGER, nullable=False, default=5)
    # TODO: в группах можно ограничить очки с которыми человек может начинать постить, пока очки не реализованы
    # user_points = Column(INTEGER, default=0)
    # TODO: ещё одна фишка! добавить возможность, чтобы пользователя можно было просматривать в списках состоящих
    #  в группе, либо чтобы его видели только друзья, либо чтобы только друзья тоже состоящие в этой группе

    # chats = relationship("Chat")
    groups = relationship("Group", secondary="user_group_link", back_populates="users")
    chats = relationship("Chat", secondary="user_chat_link", back_populates="users")
    # user_friends = relationship("Friend", backref="id",cascade="all, delete-orphan")
    user_posts = relationship("UserPost", cascade="all, delete-orphan")
    user_characters = relationship("UserCharacter", cascade='all, delete')

    @property
    def serialize(self):
        return {
            "id": self.id,
            "username": self.username,
            "avatar": self.avatar,
            "status": self.status,
            "friends_count": self.friend_count,
            "is_online": self.is_online,
            "last_time_online": self.last_time_online,
            "description": self.description,
            "v_lvl": self.min_posting_lvl,
        }


#  TODO: Новая система, теперь друзья должны хранить не уровень доверия, а теги и по тегам будут показываться посты,
#   нужно переделать для этого
class Friend(Base):
    __tablename__ = 'friends'
    first_user_id = Column(INTEGER, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    second_user_id = Column(INTEGER, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    is_request = Column(Boolean, nullable=False, default=True)
    date_added = Column(DateTime, nullable=False, default=datetime.datetime.now())
    first_ulevel = Column(INTEGER, nullable=False, default=5)
    second_ulevel = Column(INTEGER, nullable=False, default=5)

    first_user = relationship("User", foreign_keys=[first_user_id])
    second_user = relationship("User", foreign_keys=[second_user_id])

    @property
    def serialize(self):
        return {
            "first_user_id": self.first_user_id,
            "second_user_id": self.second_user_id,
            "is_request": self.is_request,
            "date_added": self.date_added,
            "first_ulevel": self.first_ulevel,
            "second_ulevel": self.second_ulevel
        }


class UserPost(Base):
    __tablename__ = 'userposts'
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    userid = Column(INTEGER, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    # Если пользователь оставил запись у кого-то другого на стене, эта переменная будет указывать на него,
    # по умолчанию сюда будет записываться id самого пользователя, если запись на его собственной стене
    whereid = Column(INTEGER, nullable=False)
    # Уровень поста, 5 - виден для всех, 4 - виден для всех друзей и дальше по уменьшению
    view_level = Column(INTEGER, nullable=False, default=5)
    date_added = Column(DateTime, nullable=False, default=datetime.datetime.now())
    message = Column(VARCHAR())


class UserCharacter(Base):
    __tablename__ = 'usercharacters'
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    userid = Column(INTEGER, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    character_name = Column(VARCHAR(64), nullable=False)
    character_picture = Column(VARCHAR(128))
    ch_desc_short = Column(VARCHAR(128), nullable=False, default="None")
    ch_desc_long = Column(VARCHAR(), nullable=False, default="None")
    ch_main_fandom = Column(INTEGER, nullable=False, default=1)
    ch_skills = Column(VARCHAR())

    @property
    def serialize(self):
        return {
            "id": self.id,
            "userid": self.userid,
            "character_name": self.character_name,
            "character_picture": self.character_picture,
            "ch_desc_short": self.ch_desc_short,
            "ch_fandom_id": self.ch_fandom_id,
            "ch_skills": self.ch_skills
        }


class UserGroupLink(Base):
    __tablename__ = 'user_group_link'
    user_id = Column(INTEGER, ForeignKey("users.id"), primary_key=True)
    group_id = Column(INTEGER, ForeignKey("groups.id"), primary_key=True)
    # user_view_level = Column(INTEGER, nullable=False, default=4)


class Group(Base):
    __tablename__ = 'groups'
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    avatar = Column(VARCHAR(128))
    status = Column(VARCHAR(128))
    group_name = Column(VARCHAR(128), nullable=False, unique=True)
    owner = Column(INTEGER, nullable=False)
    # TODO: и теги и модераторов нужно сделать отдельной таблицей
    # fandom_tags = Column(ARRAY(VARCHAR(128)))
    # moderators = Column(ARRAY(INTEGER))
    description = Column(VARCHAR(), nullable=False, default='This group have no description')
    rules = Column(VARCHAR(1024), nullable=False, default='This group does not have rules. Anarchy rules!')
    # Очки группы. Для чего-нибудь придумать?
    # group_points = Column(INTEGER, default=0)

    users = relationship(User, secondary='user_group_link', cascade="all, delete", back_populates="groups")
    posts = relationship("GroupPost", cascade='all, delete-orphan')

    @property
    def serialize(self):
        return {
            "id": self.id,
            "avatar": self.avatar,
            "group_name": self.group_name,
            "status": self.status,
            "owner": self.owner,
            "description": self.description,
            "rules": self.rules,
        }


class GroupPost(Base):
    __tablename__ = 'group_posts'
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    group_id = Column(INTEGER, ForeignKey('groups.id', ondelete='CASCADE'))
    post_short = Column(VARCHAR(128), nullable=False, default=' ')
    post_text = Column(VARCHAR())


class UserChatLink(Base):
    __tablename__ = 'user_chat_link'
    user_id = Column(INTEGER, ForeignKey("users.id"), primary_key=True)
    chat_id = Column(INTEGER, ForeignKey("chats.id"), primary_key=True)


class Chat(Base):
    __tablename__ = "chats"
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    chatname = Column(VARCHAR(128), nullable=False)
    admin = Column(INTEGER, ForeignKey('users.id'))
    rules = Column(VARCHAR(1024))
    is_dialog = Column(Boolean, nullable=False, default=False)

    messages = relationship("Message", cascade="all, delete-orphan")
    users = relationship(User, secondary='user_chat_link', cascade="all, delete", back_populates="chats")

    @property
    def serialize(self):
        return {
            "id": self.id,
            "chatname": self.chatname,
            "admin": self.admin,
            "rules": self.rules,
            "is_dialog": self.is_dialog
        }


class Message(Base):
    __tablename__ = 'messages'
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    fromuserid = Column(INTEGER, nullable=False)
    message_date = Column(DateTime, nullable=False, default=datetime.datetime.now())
    message = Column(VARCHAR(), nullable=False)
    chat_id = Column(INTEGER, ForeignKey('chats.id', ondelete='CASCADE'), nullable=False)

    @property
    def serialize(self):
        return {
            "id": self.id,
            "fromuserid": self.fromuserid,
            "message_date": self.message_date,
            "message": self.message,
        }
