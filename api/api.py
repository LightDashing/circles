from flask import Blueprint, request, jsonify
from database import DataBase, OpenConnectionToBD
from flask_login import login_required, current_user
from files import FileOperations
import re

api_bp = Blueprint('api_bp', __name__)
db = DataBase()


@api_bp.route('/join_group', methods=['POST'])
def join_group():
    data = request.get_json()
    with OpenConnectionToBD(db):
        db.join_group(data['group_name'], current_user)
    return jsonify(True)


@api_bp.route('/leave_group', methods=['POST'])
@login_required
def leave_group():
    data = request.get_json()
    with OpenConnectionToBD(db):
        db.leave_group(data['group_name'], current_user)
    return jsonify(True)


@api_bp.route('/publish_post', methods=['POST'])
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


@api_bp.route('/add_friend', methods=['POST'])
@login_required
def add_friend():
    if request.method == 'POST':
        username = request.get_json()['name']
        with OpenConnectionToBD(db):
            result = db.add_friend(current_user.id, db.get_userid_by_name(username))
        return jsonify(result)


@api_bp.route('/accept_friend', methods=['POST'])
@login_required
def accept_friend():
    if request.method == 'POST':
        username = request.get_json()['name']
        with OpenConnectionToBD(db):
            db.accept_request(current_user.id, db.get_userid_by_name(username))
        return jsonify(True)


@api_bp.route('/remove_friend', methods=['POST'])
@login_required
def cancel_request():
    if request.method == 'POST':
        username = request.get_json()['name']
        with OpenConnectionToBD(db):
            db.remove_friend(current_user.id, db.get_userid_by_name(username))
        return jsonify(True)


@api_bp.route('/check_friend', methods=['POST'])
@login_required
def check_is_friend():
    if request.method == 'POST':
        username = request.get_json()['name']
        with OpenConnectionToBD(db):
            fr_check = db.is_friend(current_user.id, db.get_userid_by_name(username))
            return jsonify(fr_check)


@api_bp.route('/get_user_friends', methods=['POST'])
@login_required
def get_friends_list():
    with OpenConnectionToBD(db):
        friends = db.get_user_friends(current_user.id)
    return jsonify(friends)


@api_bp.route('/send_message', methods=['POST'])
@login_required
def send_message():
    data = request.get_json()
    cleaner = re.compile('<.*?>')
    message = re.sub(cleaner, '', data['message'])
    with OpenConnectionToBD(db):
        db.send_message(current_user.id, data['chat_id'], message)
    return jsonify(True)


@api_bp.route('/load_messages', methods=['POST'])
@login_required
def load_messages():
    if request.method == 'POST':
        data = request.get_json()
        with OpenConnectionToBD(db):
            if data['type'] == 'load':
                user_messages = db.load_messages(current_user.username, data['chat_id'])
            elif data['type'] == 'update':
                user_messages = db.update_messages(data['chat_id'], data['msg_time'])
        return jsonify(user_messages)


@api_bp.route('/upload_settings', methods=['POST'])
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


@api_bp.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    search_input = data['search_input']
    with OpenConnectionToBD(db):
        results = db.search_for(search_input)
    return jsonify(results)
