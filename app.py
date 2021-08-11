import datetime

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
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
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 25
# app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
# app.config['MAIL_PORT'] = 587
# app.config['MAIL_USE_TLS'] = True
# app.config['MAIL_USERNAME'] = 'add your mail'
# app.config['MAIL_DEFAULT_SENDER'] = 'add your mail'
# app.config['MAIL_PASSWORD'] = 'add your password'
# email_app = Email(app)

# def get_reset_password_token(user_id, expires_in=600):
#     return jwt.encode({'reset_password': user_id, 'exp':time() + expires_in}, app.secret_key, algorithm='HS256').decode('utf-8')

# def verify_reset_password_token(token):
#     try:
#         id = jwt.decode(token, app.secret_key, algorithms=['HS256'])['reset_password']
#     except:
#         return
#     return id

db = DataBase()


# TODO: ВАЖНО! хранить в куках одноразовую сессию, проверять код сессии при загрузке каждой странциы, юзернейм в
#  куках не хранить


@app.context_processor
def utility_processor():
    def format_datetime(date_time):
        return date_time.strftime("%Y-%m-%d %H:%M")

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
        if session.get('username'):
            return redirect(url_for('users_page', name=session['username']))
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


@app.route('/users/<name>', methods=['GET', 'POST'])
def users_page(name):
    if request.method == 'POST':
        pass
    else:
        with OpenConnectionToBD(db):
            if name != session.get("username"):
                view_level = db.is_friend(name, session.get("username"))['u1_lvl']
            else:
                view_level = 0
            user = db.userdata_by_name(name)
            posts = db.get_posts_by_id(name, view_level)
        return render_template('user.html', name=name, descrip=user['description'], posts=posts, v_lvl=view_level,
                               avatar=user['avatar'])


@app.route('/groups/<group_name>', methods=['GET'])
def group_page(group_name):
    with OpenConnectionToBD(db):
        data = db.get_group_data(group_name)
        data = data.serialize
        is_in_group = db.is_joined(session.get("username"), group_name)
    return render_template('group.html', group=data, joined=is_in_group)


@app.route('/_join_group', methods=['POST'])
def join_group():
    data = request.get_json()
    with OpenConnectionToBD(db):
        db.join_group(session.get("username"), data['group_name'])
    return jsonify(True)


@app.route('/_leave_group', methods=['POST'])
def leave_group():
    data = request.get_json()
    with OpenConnectionToBD(db):
        db.leave_group(session.get("username"), data['group_name'])
    return jsonify(True)


@app.route('/create/group', methods=['GET', 'POST'])
def create_group():
    if request.method == 'POST':
        data = request.get_json()
        with OpenConnectionToBD(db):
            db.create_group(session.get("username"), data['group_name'], data['group_description'],
                            data['group_rules'], data['group_tags'])
            db.join_group(session.get("username"), data['group_name'])
        # TODO: редирект не работает? исправить
        return redirect(url_for("group_page", group_name=data['group_name']))
    else:
        return render_template("create_group.html")


@app.route('/user/groups', methods=['GET'])
def user_groups():
    with OpenConnectionToBD(db):
        username = session.get("username")
        avatar = db.get_avatar_by_name(username)
        user_groups = db.get_user_groups(username)
    return render_template('user_groups.html', groups=user_groups, name=username, avatar=avatar)


@app.route('/_publish_post', methods=['POST'])
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
                db.publish_post(data['message'], data['view_lvl'], session.get("username"),
                                data["whereid"], data['attach'])
        return jsonify(True)


@app.route('/_update_posts', methods=['POST'])
def update_posts():
    if request.method == 'POST':
        user = request.get_json()
        with OpenConnectionToBD(db):
            pass


@app.route('/_add_friend', methods=['POST'])
def add_friend():
    if request.method == 'POST':
        username = request.get_json()['name']
        with OpenConnectionToBD(db):
            db.add_friend(session.get('username'), username)
        return jsonify(True)
    return url_for(error_404(Exception("Such page doesn't exists")))


@app.route('/_accept_friend', methods=['POST'])
def accept_friend():
    if request.method == 'POST':
        username = request.get_json()['name']
        with OpenConnectionToBD(db):
            db.accept_request(username, session.get("username"))
        return jsonify(True)
    return url_for(error_404(Exception("Such page doesn't exists")))


@app.route('/_remove_friend', methods=['POST'])
def cancel_request():
    if request.method == 'POST':
        username = request.get_json()['name']
        with OpenConnectionToBD(db):
            db.remove_friend(session.get('username'), username)
        return jsonify(True)
    return url_for(error_404(Exception("Such page doesn't exists")))


@app.route('/_check_friend', methods=['POST'])
def check_is_friend():
    if request.method == 'POST':
        username = request.get_json()['name']
        with OpenConnectionToBD(db):
            fr_check = db.is_friend(session.get("username"), username)
            return jsonify(fr_check)


@app.route('/user/friends')
def friends_page():
    if request.method == 'GET':
        username = session.get('username')
        with OpenConnectionToBD(db):
            userdata = db.userdata_by_name(session.get("username"))
            friends = db.return_friendslist(session.get("username"))
        return render_template("friends.html", userdata=userdata, friends=friends, avatar=userdata['avatar'],
                               name=username)


@app.route('/_send_message', methods=['POST'])
def send_message():
    if request.method == 'POST':
        data = request.get_json()
        with OpenConnectionToBD(db):
            db.send_message(session.get("username"), data['chat_id'], data['message'], data['attachment'])
        return jsonify("True")


@app.route('/_load_messages', methods=['POST'])
def load_messages():
    if request.method == 'POST':
        data = request.get_json()
        with OpenConnectionToBD(db):
            if data['type'] == 'load':
                messages = db.get_messages_with_user(session.get("username"), data['user'])
            elif data['type'] == 'update':
                messages = db.update_messages(data['chat_id'], data['msg_time'])
        return jsonify(messages)


@app.route('/dialog/<username>', methods=['GET', 'POST'])
def dialog_page(username):
    with OpenConnectionToBD(db):
        name = session['username']
        messages = db.get_messages_with_user(name, username)
        chat_id = db.get_dialog_chat_id(name, username)
    return render_template("dialog.html", name=name, messages=messages, username=username, chat_id=chat_id)


@app.route('/user/messages', methods=['GET'])
def messages():
    with OpenConnectionToBD(db):
        username = session['username']
        avatar = db.get_avatar_by_name(username)
        chats = db.get_user_chats(username)
    return render_template("messages.html", chats=chats, name=username, avatar=avatar)


@app.route('/user/create_chat', methods=['GET', 'POST'])
def create_chat():
    if request.method == 'POST':
        data = request.get_json()
        with OpenConnectionToBD(db):
            chat_id = db.create_chat(data['users'], data['chat_name'], data['admin'], moderators=data['moderators'])
        return url_for("chat", chat_id=chat_id)
    else:
        with OpenConnectionToBD(db):
            username = session.get("username")
            friends = db.return_friendslist(username)
        return render_template("create_chat.html", friends=friends, name=username)


@app.route('/chat/send_message', methods=['POST'])
def send_message_v2():
    data = request.get_json()
    cleaner = re.compile('<.*?>')
    message = re.sub(cleaner, '', data['message'])
    with OpenConnectionToBD(db):
        db.send_message(data['user'], data['chat_id'], message, data['attachment'])
    return jsonify(True)


@app.route('/chat/load_messages', methods=['POST'])
def load_messages_v2():
    if request.method == 'POST':
        data = request.get_json()
        with OpenConnectionToBD(db):
            if data['type'] == 'load':
                messages = db.load_messages(session.get("username"), data['chat_id'])
            elif data['type'] == 'update':
                messages = db.update_messages(data['chat_id'], data['msg_time'])
        return jsonify(messages)


@app.route('/chat/<chat_id>', methods=['GET'])
def chat(chat_id):
    username = session.get('username')
    with OpenConnectionToBD(db):
        chat_obj = db.get_chat_byid(chat_id)
        avatar = db.get_avatar_by_name(username)
        messages = chat_obj.serialize['messages']
    for message in messages:
        message.fromuserid = db.get_name_by_userid(message.fromuserid)
    return render_template("chat.html", chat=chat_obj.serialize, name=username, messages=messages, avatar=avatar)


@app.route('/user/_upload_settings', methods=['POST'])
def upload_settings():
    data = request.get_json()
    if data:
        image = data.get("image")
        fo = FileOperations(session.get('userid'))
        fo.save_image(image, 'avatar')
    username = str(request.form["username"])
    description = str(request.form["desc"])
    can_post = bool(request.form["can_post"])
    post_lvl = int(request.form["view_level"])
    email = str(request.form["email"])
    password = str(request.form['pw1'])
    response = {}
    with OpenConnectionToBD(db):
        response['u_name_r'] = db.change_username(session.get('username'), username)
        response['u_desc_r'] = db.change_description(session.get('username'), description)
        response['u_pub_r'] = db.change_publish_settings(session.get('username'), can_post)
        response['u_lvl_r'] = db.ch_min_posting_lvl(session.get('username'), post_lvl)
        response['u_email_r'] = db.change_mail(session.get('username'), email)
        if password:
            # Do something
            pass
        if -1 in response.values():
            return jsonify({'unknown_error': True})
    return jsonify(response)


@app.route('/user/settings', methods=['GET', 'POST'])
def user_settings():
    if request.method == 'POST':
        pass
    else:
        if not session.get('username'):
            return render_template('index.html')
        name = session['username']
        with OpenConnectionToBD(db):
            userdata = db.userdata_by_name(name)
            if not userdata:
                return render_template("404.html")
        email = userdata['email']
        descrip = userdata['description']
        checkbox = userdata['can_post']
        min_pub_lvl = userdata['min_post_lvl']
        return render_template('settings.html', name=name, email=email, descrip=descrip, can_post=checkbox,
                               m_p_lvl=min_pub_lvl, avatar=userdata['avatar'])


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['pw1']
        with OpenConnectionToBD(db):
            if not db.login_user(email, password):
                return render_template('login.html', error='dont_match')
            name = db.name_by_mail(email)
            userid = db.get_userid_by_name(name)
        session['username'] = name
        session['userid'] = userid
        return redirect(url_for('users_page', name=name))
    else:
        if session.get('username'):
            return redirect(url_for('users_page', name=session['username']))
        else:
            return render_template('login.html', error=None)


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))


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
