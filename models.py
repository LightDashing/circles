from sqlalchemy import Column, INTEGER, Text, ForeignKey, DateTime, Boolean, or_, and_
from sqlalchemy.dialects.postgresql import ARRAY, VARCHAR
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import datetime
from sqlalchemy.exc import IntegrityError

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    username = Column(VARCHAR(30), unique=True, nullable=False)
    email = Column(VARCHAR(30), unique=True, nullable=False)
    password = Column(VARCHAR(512), nullable=False)
    registration_date = Column(DateTime, nullable=False, default=datetime.datetime.now())
    description = Column(VARCHAR())
    status = Column(VARCHAR(30), nullable=False, default=' ')
    avatar = Column(VARCHAR(128))
    friend_count = Column(INTEGER, nullable=False, default=0)
    # Могут ли другие люди оставлять у этого пользователя записи на стене
    other_publish = Column(Boolean, nullable=False, default=True)
    # Здесь можно указать уровень людей, способных постить на стене
    min_posting_lvl = Column(INTEGER, nullable=False, default=5)
    fandom_tags = ARRAY(VARCHAR(128))
    # TODO: в группах можно ограничить очки с которыми человек может начинать постить, пока очки не реализованы
    # user_points = Column(INTEGER, default=0)

    chats = relationship("Chat")
    groups = relationship("Group", secondary="user_group_link", backref="groups")
    user_friends = relationship("Friend", cascade="all, delete-orphan")
    user_posts = relationship("UserPost", cascade="all, delete-orphan")
    user_characters = relationship("UserCharacter", cascade='all, delete')


class Friend(Base):
    __tablename__ = 'friends'
    first_user = Column(INTEGER, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    second_user = Column(INTEGER, primary_key=True)
    is_request = Column(Boolean, nullable=False, default=True)
    date_added = Column(DateTime, nullable=False, default=datetime.datetime.now())
    # TODO уровень доверия к человеку, выставляется пользователем, нужен для просмотра постов
    # 4 - самый низкий, 5 - этот человек не является другом
    # уровень доверия виден только автору страницы
    first_ulevel = Column(INTEGER, nullable=False, default=5)
    second_ulevel = Column(INTEGER, nullable=False, default=5)


class UserPost(Base):
    __tablename__ = 'userposts'
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    userid = Column(INTEGER, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    # Если пользователь оставил запись у кого-то другого на стене, эта переменная будет указывать на него,
    # по умолчанию сюда будет записываться id самого пользователя, если запись на его собственной стене
    whereid = Column(INTEGER, nullable=False)
    # Уровень поста, 5 - виден для всех, 4 - виден для всех друзей и дальше по уменьшению
    view_level = Column(INTEGER, nullable=False, default=5)
    message = Column(VARCHAR())
    tags = Column(ARRAY(VARCHAR(128)))
    attachment = Column(ARRAY(VARCHAR(128)))


# TODO: ниже будет часть кода ответственного за фандомную часть соц. сети


class UserCharacter(Base):
    __tablename__ = 'usercharacters'
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    userid = Column(INTEGER, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    character_name = Column(VARCHAR(64), nullable=False)
    character_picture = Column(VARCHAR(128))
    ch_desc_short = Column(VARCHAR(128), nullable=False, default="None")
    ch_desc_long = Column(VARCHAR(), nullable=False, default="None")
    ch_main_fandom = Column(INTEGER, nullable=False, default=1)
    ch_fandom_tags = Column(ARRAY(VARCHAR(128)))
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
    fandom_tags = Column(ARRAY(VARCHAR(128)))
    moderators = Column(ARRAY(INTEGER))
    description = Column(VARCHAR(), nullable=False, default='This group have no description')
    rules = Column(VARCHAR(1024), nullable=False, default='This group does not have rules. Anarchy rules!')
    # Очки группы. Для чего-нибудь придумать?
    # group_points = Column(INTEGER, default=0)

    users = relationship(User, secondary='user_group_link', cascade="all, delete")
    posts = relationship("GroupPost", cascade='all, delete-orphan')

    @property
    def serialize(self):
        return {
            "id": self.id,
            "avatar": self.avatar,
            "group_name": self.group_name,
            "status": self.status,
            "owner": self.owner,
            "fandom_tags": self.fandom_tags,
            "moderators": self.moderators,
            "description": self.description,
            "rules": self.rules,
            "users": self.users,
            "posts": self.posts
        }


class GroupPost(Base):
    __tablename__ = 'group_posts'
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    group_id = Column(INTEGER, ForeignKey('groups.id', ondelete='CASCADE'))
    post_short = Column(VARCHAR(128), nullable=False, default=' ')
    post_text = Column(VARCHAR())
    post_attachments = Column(ARRAY(VARCHAR(128)))
    post_tags = Column(ARRAY(VARCHAR(128)))


class Chat(Base):
    __tablename__ = "chats"
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    chatname = Column(VARCHAR(128), nullable=False)
    userids = Column(ARRAY(INTEGER), nullable=False)
    admin = Column(INTEGER, ForeignKey('users.id'))
    moders = Column(ARRAY(INTEGER))
    rules = Column(VARCHAR(1024))
    fandom_tags = Column(ARRAY(VARCHAR(128)))
    messages = relationship("Message", cascade="all, delete-orphan")

    @property
    def serialize(self):
        return {
            "id": self.id,
            "chatname": self.chatname,
            "userids": self.userids,
            "admin": self.admin,
            "moders": self.moders,
            "rules": self.rules,
            "fandoms": self.fandoms,
            "messages": self.messages
        }


class Message(Base):
    __tablename__ = 'messages'
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    fromuserid = Column(INTEGER, nullable=False)
    message_date = Column(DateTime, nullable=False, default=datetime.datetime.now())
    message = Column(VARCHAR(), nullable=False)
    chat_id = Column(INTEGER, ForeignKey('chats.id', ondelete='CASCADE'), nullable=False)
    attachments = Column(ARRAY(VARCHAR(128)))

    @property
    def serialize(self):
        return {
            "id": self.id,
            "fromuserid": self.fromuserid,
            "message_date": self.message_date,
            "message": self.message,
            "attachments": self.attachments
        }
