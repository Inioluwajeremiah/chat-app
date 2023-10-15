
from flask import Blueprint, jsonify
from app.status_codes import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED_ACCESS
from flask_jwt_extended import unset_jwt_cookies

signout_blueprint = Blueprint("signout", __name__)

@signout_blueprint.post("/signout")
def signout():
    response = jsonify({"msg": "logout successful"}), HTTP_200_OK
    unset_jwt_cookies(response)
    return response