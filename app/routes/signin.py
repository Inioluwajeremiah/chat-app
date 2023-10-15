
from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import set_access_cookies, create_access_token
from werkzeug.security import check_password_hash
from markupsafe import Markup
from app.chat_db_model import User
from app.status_codes import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_401_UNAUTHORIZED_ACCESS

signin_blueprint = Blueprint("signin", __name__)

@signin_blueprint.post('/')
def signin():
    email = request.json['email']
    password = request.json['password']

     # clean inputs
    email =  Markup.escape(email)
    password =  Markup.escape(password)

    user = User.query.filter_by(email=email).first()

    if not user:
            return {"message": "User not found. Sign up to continue"}, HTTP_401_UNAUTHORIZED_ACCESS

        # check if user is signed up but not authenticate
    if user and not user.is_verified:
        return {"message": "User not yet authenticate"}, HTTP_401_UNAUTHORIZED_ACCESS
    
    if user and user.is_verified:
        user_id = user.id
        is_password_correct = check_password_hash(user.password, password)

        if is_password_correct:
            resp = make_response(jsonify({"message": "login successful"}), HTTP_200_OK)
            access_token = create_access_token(identity=user_id)
            set_access_cookies(resp, access_token)
            print(resp.headers)
            return resp
        return {"message": "Invalid password"}, HTTP_404_NOT_FOUND
        
    return {"message": f"User not found {user.is_verified}"}, HTTP_404_NOT_FOUND

