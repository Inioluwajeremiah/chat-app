from flask import Flask, Blueprint
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from .config import DevConfig
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_mail import Mail

db = SQLAlchemy()
mail = Mail()
jwt = JWTManager()


def create_app(config=DevConfig):
    app = Flask(__name__)

    if config is not None:
        app.config.from_object(config)
        print("config file seen")

    CORS(app,  resources={r"/*": {"origins": ["http://localhost:3000", "https://chat-app-client-sooty.vercel.app"]}}, supports_credentials=True)
    db.init_app(app)
    mail.init_app(app)
    migrate = Migrate(app, db)
    jwt.init_app(app)


    @app.route('/')
    def index():
        return "Chat app home"
    
    from .routes.signup import signup_blueprint
    from .routes.signin import signin_blueprint
    from .routes.signout import signout_blueprint
    from .routes.verify_user import verify_user_blueprint
    from .routes.chat import chat_blueprint

    app.register_blueprint(signup_blueprint, url_prefix = "/signup")
    app.register_blueprint(signin_blueprint, url_prefix = "/signin")
    app.register_blueprint(signout_blueprint, url_prefix = "/signout")
    app.register_blueprint(verify_user_blueprint, url_prefix = "/verify_user")
    app.register_blueprint(chat_blueprint, url_prefix = "/chat")
    
    return app
    

