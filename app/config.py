import os

class DevConfig:
    # Secret Key
    SECRET_KEY = os.environ.get('SECRET_KEY') 
    # PostgreSQL Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') 
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_USERNAME = 'gbstaiapp@gmail.com'
    MAIL_PASSWORD = os.environ.get('APP_PASSWORD')
    MAIL_DEFAULT_SENDER = 'gbstaiapp@gmail.com'

    JWT_TOKEN_LOCATION = ["cookies", "headers"]
    JWT_COOKIE_SAMESITE = "None"
    JWT_COOKIE_SECURE = True 
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
