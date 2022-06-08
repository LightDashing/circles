from sqlalchemy import Column, INTEGER, Text, ForeignKey, DateTime, \
    Boolean, or_, and_, Index, SMALLINT, ForeignKeyConstraint
from sqlalchemy.dialects.postgresql import VARCHAR, TEXT
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from flask_login import UserMixin
import datetime
import os

Base = declarative_base()


def create_all(login, password, hostname, schema):
    engine = create_engine(f'postgresql://{login}:{password}@{hostname}/{schema}')
    Base.metadata.create_all(engine)


# TODO: ВАЖНО! вернуть ограничения по полям, сделать его большим, но существующим, чтобы нельзя было сохранять
#  десятки мегабайт текста


class User(UserMixin, Base):
    __tablename__ = 'users'
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    username = Column(VARCHAR(30), unique=True, nullable=False)
    email = Column(VARCHAR(30), unique=True, nullable=False)
    password = Column(VARCHAR(1024), nullable=False)
    registration_date = Column(DateTime, nullable=False, default=datetime.datetime.now())
    last_time_online = Column(DateTime, nullable=False)
    is_online = Column(Boolean)
    # age = Column(SMALLINT)
    # email_active = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=False)
    description = Column(VARCHAR(1024))
    status = Column(VARCHAR(30), nullable=False, default=' ')
    age = Column(INTEGER)
    name = Column(VARCHAR(60))
    surname = Column(VARCHAR(60))
    avatar = Column(TEXT, default=os.path.join("..", "static", "img", "user-avatar.svg"))
    # Могут ли другие люди оставлять у этого пользователя записи на стене
    other_publish = Column(Boolean, nullable=False, default=True)
    # Здесь можно указать уровень людей, способных постить на стене
    # TODO: в группах можно ограничить очки с которыми человек может начинать постить, пока очки не реализованы
    # user_points = Column(INTEGER, default=0)
    # TODO: ещё одна фишка! добавить возможность, чтобы пользователя можно было просматривать в списках состоящих
    #  в группе, либо чтобы его видели только друзья, либо чтобы только друзья тоже состоящие в этой группе

    # chats = relationship("Chat")
    groups = relationship("Group", secondary="user_group_link", back_populates="users")
    chats = relationship("Chat", secondary="user_chat_link", back_populates="users")
    friends = relationship("Friend", primaryjoin="(User.id == Friend.first_user_id) | (User.id == "
                                                 "Friend.second_user_id)")
    # user_friends = relationship("Friend", backref="id",cascade="all, delete-orphan")
    user_posts = relationship("UserPost", cascade="all, delete-orphan")

    notifications = relationship("Notification", cascade='all, delete-orphan')

    @property
    def serialize(self):
        return {
            "id": self.id,
            "username": self.username,
            "avatar": self.avatar,
            "status": self.status,
            "is_online": self.is_online,
            "last_time_online": self.last_time_online,
            "description": self.description
        }


class Friend(Base):
    __tablename__ = 'friends'
    id = Column(INTEGER, autoincrement=True, nullable=False, primary_key=True)
    first_user_id = Column(INTEGER, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    second_user_id = Column(INTEGER, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    is_request = Column(Boolean, nullable=False, default=True)
    is_checked = Column(Boolean, nullable=False, default=False)
    is_notified = Column(Boolean, nullable=False, default=False)
    date_added = Column(DateTime, nullable=False, default=datetime.datetime.now())

    first_user = relationship("User", foreign_keys=[first_user_id])
    second_user = relationship("User", foreign_keys=[second_user_id])
    first_user_roles = relationship("UserRole", secondary="friend_role_link",
                                    primaryjoin="(FriendRoleLink.first_u_id == Friend.first_user_id) & "
                                                "(FriendRoleLink.second_u_id == Friend.second_user_id)",
                                    overlaps="second_user_roles", cascade="all, delete")
    second_user_roles = relationship("UserRole", secondary="friend_role_link",
                                     primaryjoin="(FriendRoleLink.first_u_id == Friend.second_user_id) &"
                                                 "(FriendRoleLink.second_u_id == Friend.first_user_id)",
                                     overlaps="first_user_roles", cascade="all, delete")

    @property
    def serialize(self):
        return {
            "first_user_id": self.first_user_id,
            "first_username": self.first_user.username,
            "second_user_id": self.second_user_id,
            "second_username": self.second_user.username,
            "is_request": self.is_request,
            "date_added": self.date_added,
        }


class UserPostLikes(Base):
    __tablename__ = 'user_posts_likes'
    group_post_id = Column(INTEGER, ForeignKey("userposts.id", ondelete='CASCADE'), primary_key=True)
    user_id = Column(INTEGER, ForeignKey("users.id", ondelete='CASCADE'), primary_key=True)
    date_liked = Column(DateTime, nullable=False, default=datetime.datetime.now())


class UserPost(Base):
    __tablename__ = 'userposts'
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    userid = Column(INTEGER, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    # Если пользователь оставил запись у кого-то другого на стене, эта переменная будет указывать на него,
    # по умолчанию сюда будет записываться id самого пользователя, если запись на его собственной стене
    whereid = Column(INTEGER, nullable=False)
    is_private = Column(Boolean, nullable=False, default=False)
    date_added = Column(DateTime, nullable=False, default=datetime.datetime.now())
    message = Column(TEXT)

    roles = relationship("UserRole", secondary="user_post_role_link", cascade="all, delete")
    attachment = relationship('ImageAttachment', cascade="all, delete-orphan")
    likes = relationship("User", secondary="user_posts_likes", cascade="all, delete")

    @property
    def serialize(self):
        return {
            "id": self.id,
            "user_id": self.userid,
            "whereid": self.whereid,
            "date_added": self.date_added,
            "message": self.message,
            "is_private": self.is_private,
            "roles": [role.serialize for role in self.roles],
            "likes": len(self.likes),
            "attachment": [attach.serialize for attach in self.attachment]
        }


# TODO: Необходимы правки и тесты для новой системы уведомлений.
class Notification(Base):
    __tablename__ = 'notifications'
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    user_id = Column(INTEGER, ForeignKey("users.id", ondelete='CASCADE'), nullable=False)
    is_read = Column(Boolean, nullable=False, default=False)
    is_notified = Column(Boolean, nullable=False, default=False)

    chat = relationship("Chat", secondary='notification_chat', cascade="all, delete", backref="notifications")

    @property
    def serialize(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "is_read": self.is_read,
            "is_notified": self.is_notified,
            "chat_id": self.chat[0].id if self.chat else 0,
        }


class NotificationChatLink(Base):
    __tablename__ = 'notification_chat'
    notification_id = Column(INTEGER, ForeignKey("notifications.id", ondelete='CASCADE'), primary_key=True)
    chat_id = Column(INTEGER, ForeignKey("chats.id", ondelete='CASCADE'), primary_key=True)
    message_count = Column(INTEGER, nullable=False, default=0)
    last_visited = Column(DateTime, nullable=False, default=datetime.datetime.now())
    is_muted = Column(Boolean, nullable=False, default=False)

    @property
    def serialize(self):
        return {
            "notification_id": self.notification_id,
            "chat_id": self.chat_id,
            "message_count": self.message_count,
            "last_visited": self.last_visited,
            "is_muted": self.is_muted
        }


class UserRole(Base):
    __tablename__ = 'user_roles'
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    role_name = Column(VARCHAR(32), index=True, unique=False)
    role_color = Column(VARCHAR(7), nullable=False, default="#eca7a7")
    font_color = Column(VARCHAR(7), nullable=False, default="#000000")
    can_post = Column(Boolean, nullable=False, default=False)
    creator = Column(INTEGER, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    # can_post = Column(Boolean, nullable=False, default=False)
    # who_can_see = Column(INTEGER, nullable=False, default=0)

    @property
    def serialize(self):
        return {
            "id": self.id,
            "role_name": self.role_name,
            "role_color": self.role_color,
            "font_color": self.font_color,
            "can_post": self.can_post,
            "creator": self.creator
        }


class FriendRoleLink(Base):
    __tablename__ = 'friend_role_link'
    first_u_id = Column(INTEGER, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    second_u_id = Column(INTEGER, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    role_id = Column(INTEGER, ForeignKey("user_roles.id"), primary_key=True)


class UserPostRoleLink(Base):
    __tablename__ = 'user_post_role_link'
    post_id = Column(INTEGER, ForeignKey("userposts.id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(INTEGER, ForeignKey('user_roles.id', ondelete="CASCADE"), primary_key=True)


class UserGroupLink(Base):
    __tablename__ = 'user_group_link'
    user_id = Column(INTEGER, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    group_id = Column(INTEGER, ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True)
    # user_view_level = Column(INTEGER, nullable=False, default=4)


class Group(Base):
    __tablename__ = 'groups'
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    avatar = Column(TEXT)
    status = Column(VARCHAR(128))
    group_name = Column(VARCHAR(128), nullable=False, unique=True)
    owner = Column(INTEGER, nullable=False)
    # TODO: и теги и модераторов нужно сделать отдельной таблицей
    # fandom_tags = Column(ARRAY(VARCHAR(128)))
    # moderators = Column(ARRAY(INTEGER))
    description = Column(VARCHAR(), nullable=False, default='This group have no description')
    rules = Column(TEXT, nullable=False, default='This group does not have rules. Anarchy rules!')
    # Очки группы. Для чего-нибудь придумать?
    # group_points = Column(INTEGER, default=0)

    users = relationship(User, secondary='user_group_link', cascade="all, delete", back_populates="groups")
    posts = relationship("GroupPost", cascade='all, delete-orphan', back_populates="group")

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
            "users_amount": len(self.users)
        }


class GroupPostLikes(Base):
    __tablename__ = 'group_posts_likes'
    group_post_id = Column(INTEGER, ForeignKey("group_posts.id", ondelete='CASCADE'), primary_key=True)
    user_id = Column(INTEGER, ForeignKey("users.id", ondelete='CASCADE'), primary_key=True)
    date_liked = Column(DateTime, nullable=False, default=datetime.datetime.now())


class GroupPost(Base):
    __tablename__ = 'group_posts'
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    group_id = Column(INTEGER, ForeignKey('groups.id', ondelete='CASCADE'))
    date_added = Column(DateTime, nullable=False, default=datetime.datetime.now())
    posted_user_id = Column(INTEGER, ForeignKey('users.id'))
    post_text = Column(VARCHAR(), nullable=False)
    is_anonymous = Column(Boolean, nullable=False, default=True)

    attachment = relationship('ImageAttachment', cascade="all, delete-orphan")
    group = relationship("Group", back_populates="posts")
    likes = relationship("User", secondary="group_posts_likes", cascade="all, delete")

    @property
    def serialize(self):
        return {
            "id": self.id,
            "group_id": self.group_id,
            "group_name": self.group.group_name,
            "user_id": self.posted_user_id,
            "date_added": self.date_added,
            "message": self.post_text,
            "is_anonymous": self.is_anonymous,
            "group_avatar": self.group.avatar,
            "likes": len(self.likes),
            "attachment": [attach.serialize for attach in self.attachment]
        }


class UserChatLink(Base):
    __tablename__ = 'user_chat_link'
    user_id = Column(INTEGER, ForeignKey("users.id", ondelete='CASCADE'), primary_key=True)
    chat_id = Column(INTEGER, ForeignKey("chats.id", ondelete='CASCADE'), primary_key=True)
    is_admin = Column(Boolean, nullable=False, default=False)
    is_muted = Column(Boolean, nullable=False, default=False)
    is_notified = Column(Boolean, nullable=False, default=False)
    last_visited = Column(DateTime, nullable=False, default=datetime.datetime.now())


class Chat(Base):
    __tablename__ = "chats"
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    chatname = Column(VARCHAR(128), nullable=False)
    avatar = Column(TEXT, default=os.path.join("..", "static", "img", "peoples.svg"))
    chat_color = Column(VARCHAR(7))
    rules = Column(TEXT)
    is_dialog = Column(Boolean, nullable=False, default=False)

    messages = relationship("Message", cascade="all, delete-orphan")
    users = relationship(User, secondary='user_chat_link', cascade="all, delete", back_populates="chats")

    @property
    def serialize(self):
        return {
            "id": self.id,
            "chatname": self.chatname,
            "rules": self.rules,
            "avatar": self.avatar,
            "user_count": len(self.users),
            "is_dialog": self.is_dialog,
            "chat_color": self.chat_color
        }


class Message(Base):
    __tablename__ = 'messages'
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    from_user_id = Column(INTEGER, ForeignKey("users.id"), nullable=False)
    message_date = Column(DateTime, nullable=False, default=datetime.datetime.now())
    message = Column(TEXT, nullable=False)
    chat_id = Column(INTEGER, ForeignKey('chats.id', ondelete='CASCADE'), nullable=False)
    edited = Column(Boolean, nullable=False, default=False)

    attachment = relationship('ImageAttachment', cascade="all, delete-orphan")
    sender = relationship('User', backref='message')

    @property
    def serialize(self):
        return {
            "id": self.id,
            "from_user_id": self.from_user_id,
            "user_avatar": self.sender.avatar.replace("\\", "\\\\"),
            "message_date": str(self.message_date),
            "message": self.message,
            "attachment": [attach.serialize for attach in self.attachment],
            "chat_id": self.chat_id
        }


class ImageAttachment(Base):
    __tablename__ = 'image_attachments'
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    date_added = Column(DateTime, nullable=False, default=datetime.datetime.now())

    message_id = Column(INTEGER, ForeignKey("messages.id", ondelete='CASCADE'), unique=True)
    u_post_id = Column(INTEGER, ForeignKey("userposts.id", ondelete='CASCADE'), unique=True)
    g_post_id = Column(INTEGER, ForeignKey("group_posts.id", ondelete='CASCADE'), unique=True)

    a1_link = Column(TEXT, nullable=False)
    a1_likes = Column(INTEGER, default=0)

    a2_link = Column(TEXT)
    a2_likes = Column(INTEGER, default=0)

    a3_link = Column(TEXT)
    a3_likes = Column(INTEGER, default=0)

    a4_link = Column(TEXT)
    a4_likes = Column(INTEGER, default=0)

    a5_link = Column(TEXT)
    a5_likes = Column(INTEGER, default=0)

    @property
    def serialize(self):
        links_arr = [self.a1_link, self.a2_link, self.a3_link, self.a4_link, self.a5_link]
        links_arr = [i.replace("\\", "\\\\") for i in links_arr if i is not None]
        return {
            "id": self.id,
            "date_added": self.date_added,
            "a1_link": self.a1_link,
            "a2_link": self.a2_link,
            "a3_link": self.a3_link,
            "a4_link": self.a4_link,
            "a5_link": self.a5_link,
            "links_array": links_arr
        }

    @property
    def image_links(self):
        return [self.a2_link, self.a3_link, self.a4_link, self.a5_link]

    @image_links.setter
    def image_links(self, links):
        try:
            self.a2_link = links[0]
            self.a3_link = links[1]
            self.a4_link = links[2]
            self.a5_link = links[3]
        except IndexError:
            return

# engine = create_engine('postgresql://postgres:YourPassword@localhost/postgres')
# Base.metadata.create_all(engine)
