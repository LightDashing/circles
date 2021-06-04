from sqlalchemy import Column, INTEGER, Text, ForeignKey, VARCHAR, DateTime, Boolean, ARRAY, or_, and_
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
    description = Column(VARCHAR(1024))
    status = Column(VARCHAR(30), nullable=False, default=' ')
    avatar = Column(VARCHAR(128))
    friend_count = Column(INTEGER, nullable=False, default=0)
    # Могут ли другие люди оставлять у этого пользователя записи на стене
    other_publish = Column(Boolean, nullable=False, default=True)
    # Здесь можно указать уровень людей, способных постить на стене
    min_posting_lvl = Column(INTEGER, nullable=False, default=5)

    chats = relationship("Chat", cascade="all, delete-orphan")
    user_messages = relationship("Message", cascade="all, delete-orphan")
    user_friends = relationship("Friend", cascade="all, delete-orphan")
    user_posts = relationship("UserPost", cascade="all, delete-orphan")


# TODO: переписать сообщения, сейчас они deprecated
# class Message(Base):
#     __tablename__ = 'messages'
#     id = Column(INTEGER, primary_key=True, autoincrement=True)
#     userid = Column(INTEGER, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
#     fromuserid = Column(INTEGER, nullable=False)
#     message_date = Column(DateTime, nullable=False, default=datetime.datetime.now())
#     message = Column(VARCHAR(1024), nullable=False)
#     #attachments = Column(ARRAY(VARCHAR(128)))
#
#     user = relationship(User)


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

    user = relationship(User)


class UserPost(Base):
    __tablename__ = 'userposts'
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    userid = Column(INTEGER, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    # Если пользователь оставил запись у кого-то другого на стене, эта переменная будет указывать на него,
    # по умолчанию сюда будет записываться id самого пользователя, если запись на его собственной стене
    whereid = Column(INTEGER, nullable=False)
    # Уровень поста, 5 - виден для всех, 4 - виден для всех друзей и дальше по уменьшению
    view_level = Column(INTEGER, nullable=False, default=5)
    message = Column(VARCHAR(8096))
    tags = Column(VARCHAR(128))
    attachment = Column(VARCHAR(128))

    user = relationship(User)

# TODO: ниже будет часть кода ответственного за фандомную часть соц. сети

# class UserCharacter(Base):
#     __tablename__ = 'usercharacters'
#     id = Column(INTEGER, primary_key=True, autoincrement=True)
#     userid = Column(INTEGER, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
#     character_name = Column(VARCHAR(64), nullable=False)
#     character6_picture = Column(VARCHAR(128))
#     ch_desc_short = Column(VARCHAR(64), nullable=False, default="None")
#     ch_desc_long = Column(VARCHAR(2048), nullable=False, default="None")
#     ch_fandom_id = Column(INTEGER, nullable=False, default=1)
#     ch_skills = Column(VARCHAR(512))
#
#     user = relationship(User)


class Chat(Base):
    __tablename__ = "chats"
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    chatname = Column(VARCHAR(128), nullable=False)
    userids = Column(ARRAY(INTEGER), nullable=False)
    admin = Column(INTEGER, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    moders = Column(ARRAY(INTEGER))
    rules = Column(VARCHAR(1024))
    fandoms = Column(ARRAY(VARCHAR(128)))
    messages = relationship("Message", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = 'messages'
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    fromuserid = Column(INTEGER, nullable=False)
    message_date = Column(DateTime, nullable=False, default=datetime.datetime.now())
    message = Column(VARCHAR(1024), nullable=False)
    chat_id = Column(INTEGER, ForeignKey('chats.id', ondelete='CASCADE'), nullable=False)
    attachments = Column(ARRAY(VARCHAR(128)))


