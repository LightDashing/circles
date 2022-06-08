import datetime

from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_hcaptcha import hCaptcha
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from database import DBC
from models import create_all
from api.api import api_bp
from functools import reduce
import json
from mail import send_verify_email, confirm_token

app = Flask(__name__)
app.register_blueprint(api_bp, url_prefix='/api')
with open("settings.json") as settings_file:
    data = json.load(settings_file)
    if data['first_time_loading']:
        create_all(data["db_settings"]["username"], data["db_settings"]["password"], data["db_settings"]["hostname"],
                   data["db_settings"]["schema"])
    data = data['app_settings']
if data:
    app.config['SECRET_KEY'] = bytes(data['SECRET_KEY'], encoding='utf-8')
    app.config['SESSION_COOKIE_SECURE'] = data['SESSION_COOKIE_SECURE']
    app.config['MAX_CONTENT_LENGTH'] = data['MAX_CONTENT_LENGTH']
    app.config['HCAPTCHA_SITE_KEY'] = data['HCAPTCHA_SITE_KEY']
    app.config['HCAPTCHA_SECRET_KEY'] = data['HCAPTCHA_SECRET_KEY']
    app.config['HCAPTCHA_ENABLED'] = False
else:
    raise Exception("Configure your settings.json file!")
hcaptcha = hCaptcha(app)

login_manager = LoginManager()
login_manager.login_view = '/'
login_manager.blueprint_login_views = {
    'api': '/404/'
}
login_manager.init_app(app)


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
        return full_name.replace(current_user.username, "").strip()

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
            # TODO: пока не забыл!! сделать красивую обложку для друзей в друзьях пользователя, как в профиле
            DBC.set_user_active(name)
            userid = DBC.get_userid_by_name(name)
            user = DBC.get_user(userid)
            login_user(user, remember=True)
            # send_verify_email(app.secret_key, name, email)
            return render_template('index.html', error='confirm_email')


@app.route('/users/<string:name>', methods=['GET'])
def users_page(name):
    can_post = False
    if current_user.is_anonymous:
        user_roles = []
        posts = DBC.get_posts_by_id(name, -1, user_roles)
    elif name != current_user.username:
        user_roles = DBC.get_friend_roles(DBC.get_userid_by_name(name), current_user.id)
        if user_roles:
            can_post = reduce(lambda x, y: x or y, [role["can_post"] for role in user_roles])
            user_roles = [role['role_name'] for role in user_roles]
            posts = DBC.get_posts_by_id(name, current_user.id, user_roles)
        else:
            posts = DBC.get_posts_by_id(name, current_user.id, [])
    else:
        can_post = True
        posts = DBC.get_your_posts(current_user.id)
    user = DBC.userdata_by(DBC.get_userid_by_name(name))
    return render_template('user.html', name=name, posts=posts, user=user, can_post=can_post)


@app.route('/groups/<string:group_name>', methods=['GET'])
def group_page(group_name):
    data = DBC.get_group_data(group_name)
    group_posts = DBC.get_group_posts(None, current_user.id, group_name)[::-1]
    is_in_group = DBC.is_joined(group_name, current_user)
    return render_template('group.html', group=data, joined=is_in_group, posts=group_posts)


@app.route('/feed', methods=['GET'])
@login_required
def feed_page():
    posts_list = DBC.get_user_feed(current_user.id)
    return render_template("feed.html", posts=posts_list)


@app.route('/create_group', methods=['GET', 'POST'])
@login_required
def create_group():
    if request.method == 'POST':
        data = request.get_json()
        if data.get('group_avatar', None) is None:
            data['group_avatar'] = None
        DBC.create_group(current_user.id, data['group_name'], data['group_description'],
                         data['group_summary'], data['group_avatar'])
        DBC.join_group(data['group_name'], current_user)
        print(url_for("group_page", group_name=data['group_name']))
        return redirect(url_for("group_page", group_name=data['group_name']))
    else:
        return render_template("create_group.html")


@app.route('/user/groups', methods=['GET'])
@login_required
def user_groups():
    user_subs = DBC.get_user_groups(current_user.id)
    print(user_subs)
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
            return redirect(url_for('index', error='dont_match'))
        user_id = DBC.get_userid(email)
        user = DBC.get_user(user_id)
        login_user(user, remember=True)
        DBC.set_online(user_id, True)
        if not current_user.is_active:
            return render_template('index.html', error="account_error")
        return redirect(url_for('users_page', name=current_user.username))


@app.route('/logout')
@login_required
def logout():
    DBC.set_online(current_user.id, False)
    logout_user()
    return redirect(request.path)


@app.route('/confirm_email/<token>', methods=['GET'])
def confirm_email(token):
    result = confirm_token(app.secret_key, token)
    if result["confirmed"]:
        result = DBC.set_user_active(result["user_name"])
        if not result:
            return render_template('404.html')
        return render_template('index.html')
    else:
        return render_template('404.html')


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
