import datetime

from flask import Flask, render_template, request, redirect, url_for, jsonify, g
from flask_hcaptcha import hCaptcha
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from database import DataBase, DBC
from models import create_all
from api.api import api_bp
import re
import json

# from smtp_mail import Email
# from flask_mail import Message, Mail
# import jwt
app = Flask(__name__)
app.register_blueprint(api_bp, url_prefix='/api')
with open("settings.json") as settings_file:
    data = json.load(settings_file)
    if data['first_time_loading']:
        create_all(data["db_settings"]["username"], data["db_settings"]["password"], data["db_settings"]["schema"])
    data = data['app_settings']
if data:
    app.config['SECRET_KEY'] = bytes(data['SECRET_KEY'], encoding='utf-8')
    app.config['SESSION_COOKIE_SECURE'] = data['SESSION_COOKIE_SECURE']
    app.config['MAX_CONTENT_LENGTH'] = data['MAX_CONTENT_LENGTH']
    app.config['HCAPTCHA_SITE_KEY'] = data['HCAPTCHA_SITE_KEY']
    app.config['HCAPTCHA_SECRET_KEY'] = data['HCAPTCHA_SECRET_KEY']
else:
    raise Exception("Configure your settings.json file!")
hcaptcha = hCaptcha(app)
# app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
# app.config['MAIL_PORT'] = 587
# app.config['MAIL_USE_TLS'] = True
# app.config['MAIL_USERNAME'] = 'add your mail'
# app.config['MAIL_DEFAULT_SENDER'] = 'add your mail'
# app.config['MAIL_PASSWORD'] = 'add your password'
# email_app = Email(app)

login_manager = LoginManager()
login_manager.login_view = '/'
login_manager.blueprint_login_views = {
    'api': '/404/'
}
login_manager.init_app(app)


# def get_reset_password_token(user_id, expires_in=600):
#     return jwt.encode({'reset_password': user_id, 'exp':time() + expires_in}, app.secret_key, algorithm='HS256').decode('utf-8')

# def verify_reset_password_token(token):
#     try:
#         id = jwt.decode(token, app.secret_key, algorithms=['HS256'])['reset_password']
#     except:
#         return
#     return id


# TODO: Авторизация переделана под login-manager однако необходимо добавить генерацию временной уникальной куки,
#  чтобы нельзя было украсть сессию чужую и использовать её постоянно

# TODO: ВАЖНО! Переделать все endpointы под flask blueprints, чтобы тут остались только респонсы на get'ы

@login_manager.user_loader
def load_user(user_id):
    user = DBC.get_user(int(user_id))
    return user


@app.context_processor
def utility_processor():
    def format_datetime(date_time):
        return date_time.strftime("%R, %e %b, %Y")

    def get_username(userid):
        user_name = DBC.get_name_by_userid(userid)
        return user_name

    def get_user_avatar(userid=None, username=None):
        if userid:
            username = DBC.get_name_by_userid(userid)
        elif not username:
            return None
        avatar = DBC.get_avatar_by_name(username)
        return avatar

    def get_current_datetime():
        return datetime.datetime.now()

    def get_dialog_name(full_name):
        return full_name.replace(current_user.username, "")

    def format_backslash(backslash_str):
        return backslash_str.replace('\\', '\\\\')

    return dict(formate_datetime=format_datetime, get_username=get_username, get_current_datetime=get_current_datetime,
                get_user_avatar=get_user_avatar, get_dialog_name=get_dialog_name, format_backslash=format_backslash)


@app.errorhandler(404)
def error_404(e):
    return render_template('404.html')


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        if not current_user.is_anonymous:
            return redirect(url_for('users_page', name=current_user.username))
        return render_template('index.html', error=None)
    else:
        if not hcaptcha.verify():
            return render_template('index.html', error='signup_captcha_error')
        email = request.form['email']
        name = request.form['username']
        password = request.form['pw1']
        password_check = request.form['pw2']
        if password != password_check:
            return render_template('index.html', error="passwords_dont_match")
        created = DBC.add_user(name, email, password)
        if not created:
            return render_template('index.html', error='already_exist')
        else:
            userid = DBC.get_userid_by_name(name)
            login_user(DBC.get_user(userid))
            DBC.set_online(userid, True)
        return redirect(url_for('users_page', name=name))


@app.route('/users/<string:name>', methods=['GET'])
def users_page(name):
    if current_user.is_anonymous:
        user_roles = []
        posts = DBC.get_posts_by_id(name, user_roles)
    elif name != current_user.username:
        user_roles = DBC.get_friend_roles(DBC.get_userid_by_name(name), current_user.id)
        if user_roles:
            user_roles = [role['role_name'] for role in user_roles]
            posts = DBC.get_posts_by_id(name, user_roles)
        else:
            posts = DBC.get_posts_by_id(name, [])
    else:
        posts = DBC.get_your_posts(current_user.id)
    user = DBC.userdata_by(DBC.get_userid_by_name(name))
    return render_template('user.html', name=name, posts=posts, user=user)


@app.route('/groups/<string:group_name>', methods=['GET'])
def group_page(group_name):
    data = DBC.get_group_data(group_name)
    is_in_group = DBC.is_joined(group_name, current_user)
    return render_template('group.html', group=data, joined=is_in_group)


@app.route('/create/group', methods=['GET', 'POST'])
@login_required
def create_group():
    if request.method == 'POST':
        data = request.get_json()
        DBC.create_group(current_user.username, data['group_name'], data['group_description'],
                         data['group_rules'], data['group_tags'])
        DBC.join_group(current_user.username, data['group_name'])
        # TODO: редирект не работает? исправить
        return redirect(url_for("group_page", group_name=data['group_name']))
    else:
        return render_template("create_group.html")


@app.route('/user/groups', methods=['GET'])
@login_required
def user_groups():
    user_subs = DBC.get_user_groups(current_user.id)
    return render_template('user_groups.html', groups=user_subs)


@app.route('/user/friends')
@login_required
def friends_page():
    if request.method == 'GET':
        friends = DBC.get_user_friends(current_user.id, 10)
        return render_template("friends.html", friends=friends, name=current_user.username)


@app.route('/dialog/<string:username>', methods=['GET'])
@login_required
def dialog_page(username):
    chat_obj = DBC.get_user_dialog(current_user.id, DBC.get_userid_by_name(username))
    chat_obj["chatname"] = chat_obj["chatname"].replace(current_user.username, "")
    chat_messages = DBC.preload_messages(current_user.id, chat_obj["id"])
    return render_template("chat.html", chat=chat_obj,
                           name=current_user.username, messages=chat_messages)


@app.route('/user/messages', methods=['GET'])
@login_required
def messages():
    chats = DBC.get_user_chats(current_user.id)
    return render_template("messages.html", chats=chats, name=current_user.username)


@app.route('/user/create_chat', methods=['GET'])
@login_required
def create_chat():
    friends = DBC.get_user_friends(current_user.id, 10)
    return render_template("create_chat.html", friends=friends, name=current_user.username)


@app.route('/chat/<int:chat_id>', methods=['GET'])
@login_required
def chat(chat_id):
    chat_obj = DBC.get_chat_by_id(chat_id)
    if chat_obj["is_dialog"]:
        chat_obj["chatname"] = chat_obj["chatname"].replace(current_user.username, "")
    user_messages = DBC.preload_messages(current_user.id, chat_id)
    return render_template("chat.html", chat=chat_obj,
                           name=current_user.username, messages=user_messages)


@app.route('/user/settings', methods=['GET'])
@login_required
def user_settings():
    return render_template('settings.html', name=current_user.username, email=current_user.email,
                           descrip=current_user.description, can_post=current_user.other_publish)


@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        if not hcaptcha.verify():
            return render_template('index.html', error='login_captcha_error')
        email = request.form['email']
        password = request.form['pw1']
        if not DBC.login_user(email, password):
            return render_template('login.html', error='dont_match')
        user_id = DBC.get_userid(email)
        user = DBC.get_user(user_id)
        login_user(user, remember=True)
        DBC.set_online(user_id, True)
        return redirect(url_for('users_page', name=current_user.username))


@app.route('/logout')
@login_required
def logout():
    DBC.set_online(current_user.id, False)
    logout_user()
    return redirect(request.path)


# @app.route('/reset', methods=['GET', 'POST'])
# def reset():
#     if request.method == 'POST':
#         db = DBWork()
#         email = request.form['email']
#         id = db.get_user_data(db.get_user_nickname(email)).id
#         token = get_reset_password_token(id)
#         email_app.send_password_reset_email(token=token, user_id=id, email=email)
#         return render_template('reset.html')
#     else:
#         return render_template('reset.html')
#
#
# @app.route('/reset_password/<token>', methods=['GET', 'POST'])
# def reset_password(token):
#     db = DBWork()
#     user_id = veryfy_reset_password_token(token)
#     if not user_id:
#         return render_template('404.html')
#     if request.method == 'POST':
#         new_password = request.form['pw']
#         db.change_user_password(user_id, db.password_crypter(new_password))
#         db.session.close()
#         return render_template('index.html')
#     else:
#         return render_template('password_change.html')


if __name__ == "__main__":
    app.run(debug=True, threaded=True)
