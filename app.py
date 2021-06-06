from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from database import DataBase, OpenConnectionToBD
# from smtp_mail import Email
# from flask_mail import Message, Mail
# import jwt
from time import time

app = Flask(__name__)
# app.secret_key = 'SomeSuperDuperSecretKey'
app.config['SECRET_KEY'] = 'SomeSuperDuperSecretKey'
# app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
# app.config['MAIL_PORT'] = 587
# app.config['MAIL_USE_TLS'] = True
# app.config['MAIL_USERNAME'] = 'add your mail'
# app.config['MAIL_DEFAULT_SENDER'] = 'add your mail'
# app.config['MAIL_PASSWORD'] = 'add your password'
# email_app = Email(app)

# def get_reset_password_token(user_id, expires_in=600):
#     return jwt.encode({'reset_password': user_id, 'exp':time() + expires_in}, app.secret_key, algorithm='HS256').decode('utf-8')

# def veryfy_reset_password_token(token):
#     try:
#         id = jwt.decode(token, app.secret_key, algorithms=['HS256'])['reset_password']
#     except:
#         return
#     return id

db = DataBase()


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
        session['username'] = name
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
        postlist = []
        if posts:
            postlist = [i.message for i in posts]
        return render_template('user.html', name=name, descrip=user['description'], posts=postlist, v_lvl=view_level)


@app.route('/_publish_post', methods=['POST'])
def publish_post():
    if request.method == 'POST':
        data = request.get_json()
        with OpenConnectionToBD(db):
            if data.get("fromid", None):
                userdata = db.userdata_by_name(data['whereid'])
                if not userdata['can_post']:
                    return jsonify(False)
                elif data["view_lvl"] < userdata["min_post_lvl"]:
                    return jsonify(False)
                db.publish_post(data['message'], data['view_lvl'], data["fromid"], \
                                data["whereid"], data['attach'])
            else:
                db.publish_post(data['message'], data['view_lvl'], session.get("username"), \
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
        with OpenConnectionToBD(db):
            userdata = db.userdata_by_name(session.get("username"))
            friends = db.return_friendslist(session.get("username"))
    return render_template("friends.html", userdata=userdata, friends=friends)


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


@app.route('/user/settings', methods=['GET', 'POST'])
def user_settings():
    if request.method == 'POST':
        name = request.form['username']
        email = request.form['email']
        descrip = request.form.get('descrip')
        pub = request.form.get("other_post")
        v_lvl = request.form.get("view_level", 5)
        if pub:
            pub = True
        else:
            pub = False
        with OpenConnectionToBD(db):
            db.change_username(session['username'], name)
            db.change_mail(name, email)
            db.change_description(name, descrip)
            db.change_publish_settings(name, pub)
            db.ch_min_posting_lvl(name, v_lvl)
        session['username'] = name
        return redirect(url_for("users_page", name=name))
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
                               m_p_lvl=min_pub_lvl)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['pw1']
        with OpenConnectionToBD(db):
            if not db.login_user(email, password):
                return render_template('login.html', error='dont_match')
            name = db.name_by_mail(email)
        session['username'] = name
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
