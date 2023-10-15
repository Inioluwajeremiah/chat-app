from flask import Blueprint, session, request
from itsdangerous import URLSafeTimedSerializer
from app.chat_db_model import User
import os
from app import db
from markupsafe import Markup
from app.status_codes import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
import datetime

verify_user_blueprint = Blueprint("verify_user", __name__)

# verify user
@verify_user_blueprint.get('/verify-email/<token>')
def verify_user(token):
    serializer = URLSafeTimedSerializer(os.environ.get('SECRET_KEY'))
    try:
        user_email = serializer.loads(token, salt='email-verification', max_age=6000)
       
        # fetch user from database with retrieved email
        user =User.query.filter_by(email=user_email).first()
        # if user does not exist in database
        if user is None:
            return {"message": "User does not exist, kindly Sign up to continue"}, HTTP_404_NOT_FOUND
        
        #  if user is already verified
        if user.is_verified:
            return {"message": "User already verified."}, HTTP_400_BAD_REQUEST
        
        # compare input code and retrieved code
        if user and not user.is_verified:

            # print(input_code ==  user.otp)
            # update user is_verified status in the databse
            user.is_verified = True
            db.session.add(user)
            db.session.commit()
            # delete email from session
            session.pop('email', None)
            return {"message": "User verification successful"},  HTTP_200_OK
    except Exception as e:
         return {"message": f"{e}"}
    

# verify user using authentication code
@verify_user_blueprint.post('/')
def verify_User():
        # get code and email from form
    username = request.json['username']
    input_code = request.json['code']

    # clean username and code
    username = Markup.escape(username)
    input_code =  Markup.escape(input_code)

    if not username:
        return{"message": "Kindly input your username"}, HTTP_400_BAD_REQUEST
    if not input_code:
        return {"message": f"Kindly provide verification code {input_code}"}

         # fetch user from database with retrieved username
    user = User.query.filter_by(username=username).first()
    # if user does not exist in database
    if user is None:
        return {"message": "User does not exist, kindly Sign up to continue"}, HTTP_404_NOT_FOUND
    
    #  if user is already verified
    if user.is_verified:
        return {"message": "User already verified, you can proceed to login"}, HTTP_400_BAD_REQUEST
    
    # compare input code and retrieved code
    user_otp = user.otp
    if input_code != user_otp:
        return {"message": "Code does not match"}, HTTP_400_BAD_REQUEST
    
    time_difference = user.expiration_time - datetime.datetime.utcnow()
    
    if time_difference.total_seconds() <= 0:
        return {"message": "token has expired"}
    
    # compare input code and retrieved code
    if user and user_otp == input_code:

        # print(input_code ==  user.otp)
        # update user is_verified status in the databse
        user.is_verified = True
        db.session.add(user)
        db.session.commit()
        # delete username from session
        session.pop('email', None)
        return {"success_message": "User verification successful"},  HTTP_200_OK

  