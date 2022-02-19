"""
Module for email sending and jwt parsing
"""
import requests
import json
import jwt
from time import time
from flask import render_template

with open("settings.json", "r") as settings_file:
    data = json.load(settings_file)
    PRIVATE_API_KEY = data["mailgun_settings"]["private_api"]
    MAIL_API_ADDRESS = data["mailgun_settings"]["mail_api_address"]
    FROM_MAIL = data["mailgun_settings"]["from_mail"]


def send_verify_email(secret_key: str, user_name: str, email: str, expires_in: int = 1800):
    """
    This function sends verification email.\n
    :param secret_key: app's secret key. It will be used to encode message
    :param user_name: user's User.username
    :param email: user's email, verification mail will be sent there
    :param expires_in: time in which this code would expire, default is one hour
    :return: None
    """
    token = jwt.encode({"user_name": user_name, "confirmed": True, "exp": time() + expires_in}, secret_key,
                       algorithm="HS256")
    requests.post(MAIL_API_ADDRESS,
                  auth=("api", PRIVATE_API_KEY),
                  data={"from": f"Support team {FROM_MAIL}",
                        "to": [email],
                        "subject": "Email confirmation - Circles",
                        "html": render_template("verify_email.html", token=token)})


def confirm_token(secret_key: str, token) -> dict:
    """
    This function validate token and returns dictionary\n
    :param secret_key: app's secret key, must be same as in send_verify_email
    :param token: token which will be decoded
    :return: dict in format {"confirmed": bool, "user_name": User.username if exists else None}
    """
    try:
        result = jwt.decode(token, secret_key, algorithms=["HS256"])
    # TODO: подумать о том какие ошибки нужны
    except Exception:
        return {"confirmed": False, "user_name": None}
    confirmed = result.get("confirmed", None)
    if confirmed:
        return {"confirmed": True, "user_name": result["user_name"]}
    else:
        return {"confirmed": False, "user_name": result["user_name"]}
