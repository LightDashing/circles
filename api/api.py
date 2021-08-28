from flask import Blueprint, request, jsonify, render_template
from database import DataBase
from flask_login import login_required, current_user
from files import FileOperations
import re

api_bp = Blueprint('api_bp', __name__, template_folder='templates')
DBC = DataBase()


@api_bp.route('/join_group', methods=['POST'])
def join_group():
    data = request.get_json()
    DBC.join_group(data['group_name'], current_user)
    return jsonify(True)


@api_bp.route('/leave_group', methods=['POST'])
@login_required
def leave_group():
    data = request.get_json()
    DBC.leave_group(data['group_name'], current_user)
    return jsonify(True)


@api_bp.route('/publish_post', methods=['POST'])
@login_required
def publish_post():
    if request.method == 'POST':
        data = request.get_json()
        if data.get("fromid", None):
            userdata = DBC.userdata_by_name(data['whereid'])
            if not userdata['can_post']:
                return jsonify(False)
            elif data["view_lvl"] > userdata["min_post_lvl"]:
                return jsonify(False)
            DBC.publish_post(data['message'], data['view_lvl'], data["fromid"], data["whereid"], data['attach'])
        else:
            DBC.publish_post(data['message'], data['view_lvl'], current_user.username,
                             data["whereid"], data['attach'])
    return jsonify(True)


@api_bp.route('/add_friend', methods=['POST'])
@login_required
def add_friend():
    if request.method == 'POST':
        username = request.get_json()['name']
        result = DBC.add_friend(current_user.id, DBC.get_userid_by_name(username))
        return jsonify(result)


@api_bp.route('/accept_friend', methods=['POST'])
@login_required
def accept_friend():
    if request.method == 'POST':
        username = request.get_json()['name']
        DBC.accept_request(current_user.id, DBC.get_userid_by_name(username))
        return jsonify(True)


@api_bp.route('/remove_friend', methods=['POST'])
@login_required
def cancel_request():
    if request.method == 'POST':
        username = request.get_json()['name']
        DBC.remove_friend(current_user.id, DBC.get_userid_by_name(username))
        return jsonify(True)


@api_bp.route('/check_friend', methods=['POST'])
@login_required
def check_is_friend():
    if request.method == 'POST':
        username = request.get_json()['name']
        fr_check = DBC.is_friend(current_user.id, DBC.get_userid_by_name(username))
        return jsonify(fr_check)


@api_bp.route('/get_user_friends', methods=['POST'])
@login_required
def get_friends_list():
    friends = DBC.get_user_friends(current_user.id)
    return jsonify(friends)


@api_bp.route('/send_message', methods=['POST'])
@login_required
def send_message():
    data = request.get_json()
    cleaner = re.compile('<.*?>')
    message = re.sub(cleaner, '', data['message'])
    DBC.send_message(current_user.id, data['chat_id'], message)
    return jsonify(True)


# TODO: ВАЖНО! Исправить проблему безопасности, необходимо проверить, есть ли юзвер в чате для которого приходит реквест
#  а иначе сейчас можно отправить рандомный чат и получить инфу о нём и его сообщениях, что совсем не есть хорошо
@api_bp.route('/load_messages', methods=['POST'])
@login_required
def load_messages():
    data = request.get_json()
    if data['type'] == 'load':
        user_messages = DBC.load_messages(current_user.username, data['chat_id'])
    else:
        user_messages = DBC.update_messages(data['chat_id'], data['msg_time'])
    return jsonify(user_messages)


@api_bp.route('/load_chat_template', methods=['GET'])
@login_required
def load_chat_template():
    chat_id = request.args.get('id')
    chat = DBC.get_chat_by_id(chat_id)
    messages = DBC.load_messages(current_user.username, chat_id)
    return render_template("chat_template.html", chat=chat, messages=messages)


@api_bp.route('/create_chat', methods=['POST'])
@login_required
def create_chat():
    data = request.get_json()
    chat_id = DBC.create_chat(data['users'], data['chat_name'], data['admin'])
    return jsonify(chat_id)


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
    response['u_name_r'] = DBC.change_username(current_user.username, username)
    response['u_desc_r'] = DBC.change_description(current_user.id, description)
    response['u_pub_r'] = DBC.change_publish_settings(current_user.id, can_post)
    response['u_lvl_r'] = DBC.ch_min_posting_lvl(current_user.id, post_lvl)
    response['u_email_r'] = DBC.change_mail(current_user.id, email)
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
    results = DBC.search_for(search_input)
    return jsonify(results)
