import datetime

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from database import DataBase, OpenConnectionToBD
from files import FileOperations
import re

# from smtp_mail import Email
# from flask_mail import Message, Mail
# import jwt
app = Flask(__name__)
# app.secret_key = 'SomeSuperDuperSecretKey'
app.config['SECRET_KEY'] = 'SomeSuperDuperSecretKey'
app.config['SESSION_COOKIE_SECURE'] = True
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 20
# app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
# app.config['MAIL_PORT'] = 587
# app.config['MAIL_USE_TLS'] = True
# app.config['MAIL_USERNAME'] = 'add your mail'
# app.config['MAIL_DEFAULT_SENDER'] = 'add your mail'
# app.config['MAIL_PASSWORD'] = 'add your password'
# email_app = Email(app)

db = DataBase()
login_manager = LoginManager()
login_manager.login_view = '/login'
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
    with OpenConnectionToBD(db):
        db.set_online(user_id, True)
        user = db.get_user(user_id)
    return user


@app.context_processor
def utility_processor():
    def format_datetime(date_time):
        return date_time.strftime("%R, %e %b, %Y")

    def get_username(userid):
        with OpenConnectionToBD(db):
            user_name = db.get_name_by_userid(userid)
        return user_name

    def get_user_avatar(userid=None, username=None):
        with OpenConnectionToBD(db):
            if userid:
                username = db.get_name_by_userid(userid)
            elif not username:
                return None
            avatar = db.get_avatar_by_name(username)
            return avatar

    def get_current_datetime():
        return datetime.datetime.now()

    return dict(formate_datetime=format_datetime, get_username=get_username, get_current_datetime=get_current_datetime,
                get_user_avatar=get_user_avatar)


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
        email = request.form['email']
        name = request.form['username']
        password = request.form['pw1']
        password_check = request.form['pw2']
        if password != password_check:
            return render_template('index.html', error="passwords_dont_match")
        with OpenConnectionToBD(db):
            created = db.add_user(name, email, password)
        if not created:
            return render_template('index.html', error='already_exist')
        else:
            userid = db.get_userid_by_name(name)
        session['username'] = name
        session['userid'] = userid
        return redirect(url_for('users_page', name=name))


@app.route('/users/<name>', methods=['GET'])
def users_page(name):
    with OpenConnectionToBD(db):
        if current_user.is_anonymous:
            view_level = 5
        elif name != current_user.username:
            friend_data = db.is_friend(db.get_userid_by_name(name), current_user.id)
            if friend_data:
                view_level = friend_data['first_ulevel']
            else:
                view_level = 5
        else:
            view_level = 0
        user = db.userdata_by_name(db.get_userid_by_name(name))
        posts = db.get_posts_by_id(name, view_level)
    return render_template('user.html', name=name, posts=posts, user=user)


@app.route('/groups/<group_name>', methods=['GET'])
def group_page(group_name):
    with OpenConnectionToBD(db):
        data = db.get_group_data(group_name)
        data = data.serialize
        is_in_group = db.is_joined(current_user.username, group_name)
    return render_template('group.html', group=data, joined=is_in_group)


@app.route('/_join_group', methods=['POST'])
@login_required
def join_group():
    data = request.get_json()
    with OpenConnectionToBD(db):
        db.join_group(current_user.username, data['group_name'])
    return jsonify(True)


@app.route('/_leave_group', methods=['POST'])
@login_required
def leave_group():
    data = request.get_json()
    with OpenConnectionToBD(db):
        db.leave_group(current_user.username, data['group_name'])
    return jsonify(True)


@app.route('/create/group', methods=['GET', 'POST'])
@login_required
def create_group():
    if request.method == 'POST':
        data = request.get_json()
        with OpenConnectionToBD(db):
            db.create_group(current_user.username, data['group_name'], data['group_description'],
                            data['group_rules'], data['group_tags'])
            db.join_group(session.get("username"), data['group_name'])
        # TODO: редирект не работает? исправить
        return redirect(url_for("group_page", group_name=data['group_name']))
    else:
        return render_template("create_group.html")


@app.route('/user/groups', methods=['GET'])
@login_required
def user_groups():
    with OpenConnectionToBD(db):
        user_subs = db.get_user_groups(current_user.username)
    return render_template('user_groups.html', groups=user_subs)


@app.route('/_publish_post', methods=['POST'])
@login_required
def publish_post():
    if request.method == 'POST':
        data = request.get_json()
        with OpenConnectionToBD(db):
            if data.get("fromid", None):
                userdata = db.userdata_by_name(data['whereid'])
                if not userdata['can_post']:
                    return jsonify(False)
                elif data["view_lvl"] > userdata["min_post_lvl"]:
                    return jsonify(False)
                db.publish_post(data['message'], data['view_lvl'], data["fromid"], data["whereid"], data['attach'])
            else:
                db.publish_post(data['message'], data['view_lvl'], current_user.username,
                                data["whereid"], data['attach'])
        return jsonify(True)


@app.route('/_update_posts', methods=['POST'])
@login_required
def update_posts():
    if request.method == 'POST':
        user = request.get_json()
        with OpenConnectionToBD(db):
            pass


@app.route('/_add_friend', methods=['POST'])
@login_required
def add_friend():
    if request.method == 'POST':
        username = request.get_json()['name']
        with OpenConnectionToBD(db):
            db.add_friend(current_user.id, db.get_userid_by_name(username))
        return jsonify(True)
    return url_for(error_404(Exception("Such page doesn't exists")))


@app.route('/_accept_friend', methods=['POST'])
@login_required
def accept_friend():
    if request.method == 'POST':
        username = request.get_json()['name']
        with OpenConnectionToBD(db):
            db.accept_request(current_user.id, db.get_userid_by_name(username))
        return jsonify(True)
    return url_for(error_404(Exception("Such page doesn't exists")))


@app.route('/_remove_friend', methods=['POST'])
@login_required
def cancel_request():
    if request.method == 'POST':
        username = request.get_json()['name']
        with OpenConnectionToBD(db):
            db.remove_friend(current_user.id, db.get_userid_by_name(username))
        return jsonify(True)
    return url_for(error_404(Exception("Such page doesn't exists")))


@app.route('/_check_friend', methods=['POST'])
@login_required
def check_is_friend():
    if request.method == 'POST':
        username = request.get_json()['name']
        with OpenConnectionToBD(db):
            fr_check = db.is_friend(current_user.id, db.get_userid_by_name(username))
            return jsonify(fr_check)


@app.route('/_get_user_friends', methods=['POST'])
@login_required
def get_friends_list():
    with OpenConnectionToBD(db):
        friends = db.get_user_friends(current_user.id)
    return jsonify(friends)


@app.route('/user/friends')
@login_required
def friends_page():
    if request.method == 'GET':
        with OpenConnectionToBD(db):
            friends = db.get_user_friends(current_user.id, 10)
            print(friends)
        return render_template("friends.html", friends=friends, name=current_user.username)


@app.route('/_send_message', methods=['POST'])
@login_required
def send_message():
    if request.method == 'POST':
        data = request.get_json()
        with OpenConnectionToBD(db):
            db.send_message(current_user.username, data['chat_id'], data['message'], data['attachment'])
        return jsonify("True")


@app.route('/_load_messages', methods=['POST'])
@login_required
def load_messages():
    if request.method == 'POST':
        data = request.get_json()
        with OpenConnectionToBD(db):
            if data['type'] == 'load':
                user_messages = db.get_messages_with_user(current_user.username, data['user'])
            elif data['type'] == 'update':
                user_messages = db.update_messages(data['chat_id'], data['msg_time'])
        return jsonify(user_messages)


@app.route('/dialog/<username>', methods=['GET', 'POST'])
@login_required
def dialog_page(username):
    with OpenConnectionToBD(db):
        messages = db.get_messages_with_user(current_user.username, username)
        chat_id = db.get_dialog_chat_id(current_user.username, username)
    return render_template("dialog.html", name=current_user.username, messages=messages, username=username,
                           chat_id=chat_id)


@app.route('/user/messages', methods=['GET'])
@login_required
def messages():
    with OpenConnectionToBD(db):
        chats = db.get_user_chats(current_user.username)
    return render_template("messages.html", chats=chats, name=current_user.username)


@app.route('/user/create_chat', methods=['GET', 'POST'])
@login_required
def create_chat():
    if request.method == 'POST':
        data = request.get_json()
        with OpenConnectionToBD(db):
            chat_id = db.create_chat(data['users'], data['chat_name'], data['admin'], moderators=data['moderators'])
        return url_for("chat", chat_id=chat_id)
    else:
        with OpenConnectionToBD(db):
            friends = db.get_user_friends(current_user.username, 10)
        return render_template("create_chat.html", friends=friends, name=current_user.username)


# TODO: поменять endpointы для сообщений, выглядит небезопасно
@app.route('/chat/send_message', methods=['POST'])
@login_required
def send_message_v2():
    data = request.get_json()
    cleaner = re.compile('<.*?>')
    message = re.sub(cleaner, '', data['message'])
    with OpenConnectionToBD(db):
        db.send_message(current_user.id, data['chat_id'], message, data['attachment'])
    return jsonify(True)


@app.route('/chat/load_messages', methods=['POST'])
@login_required
def load_messages_v2():
    if request.method == 'POST':
        data = request.get_json()
        with OpenConnectionToBD(db):
            if data['type'] == 'load':
                user_messages = db.load_messages(current_user.username, data['chat_id'])
            elif data['type'] == 'update':
                user_messages = db.update_messages(data['chat_id'], data['msg_time'])
        return jsonify(user_messages)


@app.route('/chat/<chat_id>', methods=['GET'])
@login_required
def chat(chat_id):
    with OpenConnectionToBD(db):
        chat_obj = db.get_chat_byid(chat_id)
        messages = chat_obj.serialize['messages']
    for message in messages:
        message.fromuserid = db.get_name_by_userid(message.fromuserid)
    return render_template("chat.html", chat=chat_obj.serialize,
                           name=current_user.username, messages=messages)


@app.route('/user/_upload_settings', methods=['POST'])
@login_required
def upload_settings():
    data = request.get_json()
    if data:
        image = data.get("image")
        fo = FileOperations(current_user.id)
        response = fo.save_image(image, 'avatar')
        return jsonify(response)
    username = str(request.form["username"])
    description = str(request.form["desc"])
    can_post = bool(request.form["can_post"])
    post_lvl = int(request.form["view_level"])
    email = str(request.form["email"])
    password = str(request.form['pw1'])
    response = {}
    with OpenConnectionToBD(db):
        response['u_name_r'] = db.change_username(current_user.username, username)
        response['u_desc_r'] = db.change_description(current_user.username, description)
        response['u_pub_r'] = db.change_publish_settings(current_user.username, can_post)
        response['u_lvl_r'] = db.ch_min_posting_lvl(current_user.username, post_lvl)
        response['u_email_r'] = db.change_mail(current_user.username, email)
        if password:
            # Do something
            pass
        if -1 in response.values():
            return jsonify({'unknown_error': True})
    return jsonify(response)


@app.route('/user/settings', methods=['GET'])
@login_required
def user_settings():
    return render_template('settings.html', name=current_user.username, email=current_user.email,
                           descrip=current_user.description, can_post=current_user.other_publish,
                           m_p_lvl=current_user.min_posting_lvl)


@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    search_input = data['search_input']
    with OpenConnectionToBD(db):
        results = db.search_for(search_input)
    return jsonify(results)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['pw1']
        with OpenConnectionToBD(db):
            if not db.login_user(email, password):
                return render_template('login.html', error='dont_match')
            user_id = db.get_userid(email)
            login_user(user_id, remember=True)
        return redirect(url_for('users_page', name=current_user.username))
    else:
        if not current_user.is_anonymous:
            return redirect(url_for('users_page', name=current_user.username))
        else:
            return render_template('login.html', error=None)


@app.route('/logout')
@login_required
def logout():
    with OpenConnectionToBD(db):
        db.set_online(current_user.id, False)
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
    app.run(debug=True)
