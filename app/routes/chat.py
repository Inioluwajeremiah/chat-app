from flask import Blueprint, make_response, jsonify, request
from flask_jwt_extended import jwt_required
from app.status_codes import HTTP_200_OK


chat_blueprint = Blueprint('chat', __name__)

@chat_blueprint.get('/')
# @jwt_required()
def chat():
    data = request.cookies.get('access_token_cookie')
    try:
        return make_response(jsonify({"message": f"My Chats {data}"}), HTTP_200_OK)
    except Exception as e:
        return make_response(jsonify({"message": f"{e}"}), 404)

@chat_blueprint.route("/protected", methods=["GET", "POST"])
@jwt_required()
def protected():
    try:
        return jsonify(foo="bar")
    except Exception as e:
        return make_response(jsonify({"message": f"{e}"}), HTTP_200_OK)

    