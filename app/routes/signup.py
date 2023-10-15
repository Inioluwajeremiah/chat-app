from flask import Blueprint, jsonify, request, url_for
from app import mail
from flask_mail import Message
import random
from itsdangerous import URLSafeTimedSerializer
import os
from markupsafe import Markup
from werkzeug.security import check_password_hash, generate_password_hash
from app.chat_db_model import User
from app.status_codes import HTTP_200_OK, HTTP_400_BAD_REQUEST, \
    HTTP_409_CONFLICT, HTTP_500_INTERNAL_SERVER_ERROR
from app import db
import datetime

signup_blueprint = Blueprint("signup", __name__)


# validate password
def is_valid_password(password):
    # Define your password validation criteria
    min_length = 8
    contains_uppercase = any(char.isupper() for char in password)
    contains_lowercase = any(char.islower() for char in password)
    contains_digit = any(char.isdigit() for char in password)
    contains_special = any(char in '!@#$%^&*()_+-=[]{}|;:,.<>?~' for char in password)

    return (
        len(password) >= min_length and
        contains_uppercase and
        contains_lowercase and
        contains_digit and
        contains_special
    )

# generate 6 digits code
def generate_random_code():
    return random.randint(100000, 999999)

# send code to email
def sendEmail(eml, code):
    serializer = URLSafeTimedSerializer(os.environ.get('SECRET_KEY'))
    token = serializer.dumps(eml, salt='email-verification')
    # Create a verification link
    verification_link = url_for('verify_user.verify_user', token=token, _external=True)
    msg = Message("Authentication Code", recipients=[eml])
    
    # msg.html = f"<div style='padding:8px; background-color:#2563eb; color:#f5f5f5; font-weight:bold; border-radius:20px;'> \
    #                 <h3 style='padding:5px 2px; text-align:center; color:#f5f5f5;'>SIWES Authentication Code</h3> \
    #                 <p style='color:#f5f5f5;'>Here is your authentication code for SIWES. <br/> <b>NB:</b> \
    #                 Code expires in 10 mins.</p> \
    #                 <h4 style='text:center; letter-spacing:5px;'>{code}</h4> \
    #                 <p style='padding:5px; color:#fff;'>or visit this link for verficaation: {verification_link}</p> \
    #             <div>" 

    msg.html = f"<div style='padding:8px; background-color:#2563eb; color:#f5f5f5; font-weight:bold; border-radius:20px;'> \
                <h3 style='padding:5px 2px; text-align:center; color:#f5f5f5;'>Chat App Authentication Code</h3> \
                <p style='color:#f5f5f5;'>Here is your authentication code for Chat App. <br/> <b>NB:</b> \
                Code expires in 10 mins.</p> \
                <h4 style='text:center; letter-spacing:5px;'>{code}</h4> \
                <p style='padding:5px; background-color:#f5f5f5; color:#000;'>or visit this link for verficaation: {verification_link}</p> \
            <div>" 
    # msg.body = f"{code}"
        # send auth code to email
    mail.send(msg)

# register user
@signup_blueprint.route('/', methods=['POST'])
def signup():
    email = request.json['email']
    username = request.json['username']
    password = request.json['password']

    # clean input
    email = Markup.escape(email)
    username = Markup.escape(username)
    password =  Markup.escape(password)

    username_length = len(username)

    if not email:
        return {"message": "user email is required"}, HTTP_400_BAD_REQUEST
    if username_length > 20:
        return {"message": "Username cannot be longer than 20 characters"}, HTTP_400_BAD_REQUEST
    if username_length < 5:
        return {"message": "Username cannot be shorter than 5 characters"}, HTTP_400_BAD_REQUEST

    is_user_verified = User.query.filter_by(email=email, is_verified=True).first()
    user_by_email = User.query.filter_by(email=email, is_verified=False).first()
  
    if is_user_verified:
        return {"message": "User already exists"}, HTTP_409_CONFLICT
    if user_by_email and not is_user_verified:
        return {"message": f"{email} registered but not verified"}, HTTP_409_CONFLICT
    if not is_valid_password(password):
        return {"message": "Invalid password"}, HTTP_400_BAD_REQUEST
    
    # hash user password
    hashed_password = generate_password_hash(password)
    # expiration time
    expiration_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
    # generateotp
    otp = generate_random_code()

    # send authentication code to user
    try:
        sendEmail(email, otp)
            # add user to database
        user = User( email=email, username=username, password=hashed_password, otp=otp, expiration_time=expiration_time)
        db.session.add(user)
        db.session.commit()
        return {"message": "Authentication code sent to user email"}, HTTP_200_OK
    except Exception as e:
            return {"message": f"error sending authentication code. Reason{e}"}, HTTP_500_INTERNAL_SERVER_ERROR
    