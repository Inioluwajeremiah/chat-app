from flask import Blueprint, request, jsonify, session, url_for, make_response
from werkzeug.security import check_password_hash, generate_password_hash
from markupsafe import Markup
import validators
from app.status_codes import HTTP_200_OK, HTTP_201_CREATED,\
    HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED_ACCESS, HTTP_404_NOT_FOUND, \
    HTTP_409_CONFLICT, HTTP_500_INTERNAL_SERVER_ERROR
import random
from app.databaseModel import db, Student, Supervisor
from app import mail
from flask_mail import Message
import datetime
from datetime import timezone
from flask_jwt_extended import get_jwt, jwt_required, create_access_token, create_refresh_token, get_jwt_identity, set_access_cookies, unset_jwt_cookies
from os import  urandom
from itsdangerous import URLSafeTimedSerializer
import os


auth_blueprint = Blueprint("auth", __name__)

# sitemap
'''
    def is_valid_password(password)
    def generate_random_code()
    def sendEmail(eml, code)
    def index()
    def register()
    def verifyUser()
    def rrsendCode()
    def login()
    def logout()
'''

# Using an `after_request` callback, we refresh any token that is within 30
# minutes of expiring. Change the timedeltas to match the needs of your application.
@auth_blueprint.after_request
def refresh_expiring_jwts(response):
    try:
        identity = get_jwt_identity()
        exp_timestamp = get_jwt()["exp"]
        now = datetime.now(timezone.utc)
        target_timestamp = datetime.timestamp(now + datetime.timedelta(minutes=30))
        if target_timestamp > exp_timestamp:
            access_token = create_access_token(identity=identity)
            set_access_cookies(response, access_token)
        return response
    except (RuntimeError, KeyError):
        # Case where there is not a valid JWT. Just return the original response
        return response

@auth_blueprint.after_request
def set_referrer_policy(response):
    response.headers["Referrer-Policy"] = "origin-when-cross-origin"
    return response
    
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
    verification_link = url_for('auth.verify_user', token=token, _external=True)
    msg = Message("Authentication Code", recipients=[eml])
    
    # msg.html = f"<div style='padding:8px; background-color:#2563eb; color:#f5f5f5; font-weight:bold; border-radius:20px;'> \
    #                 <h3 style='padding:5px 2px; text-align:center; color:#f5f5f5;'>SIWES Authentication Code</h3> \
    #                 <p style='color:#f5f5f5;'>Here is your authentication code for SIWES. <br/> <b>NB:</b> \
    #                 Code expires in 10 mins.</p> \
    #                 <h4 style='text:center; letter-spacing:5px;'>{code}</h4> \
    #                 <p style='padding:5px; color:#fff;'>or visit this link for verficaation: {verification_link}</p> \
    #             <div>" 

    msg.html = f"<div style='padding:8px; background-color:#2563eb; color:#f5f5f5; font-weight:bold; border-radius:20px;'> \
                <h3 style='padding:5px 2px; text-align:center; color:#f5f5f5;'>SIWES Authentication Code</h3> \
                <p style='color:#f5f5f5;'>Here is your authentication code for SIWES. <br/> <b>NB:</b> \
                Code expires in 10 mins.</p> \
                <h4 style='text:center; letter-spacing:5px;'>{code}</h4> \
                <p style='padding:5px; background-color:#f5f5f5; color:#000;'>or visit this link for verficaation: {verification_link}</p> \
            <div>" 
    # msg.body = f"{code}"
        # send auth code to email
    mail.send(msg)

# home
@auth_blueprint.route('/home')
def index():
    return "home page"

# register student
@auth_blueprint.route('/student/register', methods=['POST'])
def register_student():

    firstName = request.json['firstname'];
    middleName = request.json['middlename']
    lastName = request.json['lastname']
    email = request.json['email']
    startDate = request.json['startdate']
    endDate  = request.json['enddate']  
    supervisorName = request.json['supervisorname'] 
    gender  = request.json['gender']   
    matricNo = request.json['matricno']
    department = request.json['department']
    course = request.json['course']
    level = request.json['level']
    ppa = request.json['ppa']
    password = request.json['password']
    role = request.json['role']

    # clean input
    firstName = Markup.escape(firstName)
    middleName = Markup.escape(middleName)
    lastName = Markup.escape(lastName)
    matricNo =  Markup.escape(matricNo)
    email = Markup.escape(email)
    startDate  =  Markup.escape(startDate)
    endDate =  Markup.escape(endDate)
    supervisorName = Markup.escape(supervisorName)
    gender =  Markup.escape(gender)
    department =  Markup.escape(department)
    course = Markup.escape(course)
    level = Markup.escape(level)
    ppa =  Markup.escape(ppa)
    password =  Markup.escape(password)
    role =  Markup.escape(role)

    is_user_verified = Student.query.filter_by(email=email, is_verified=True).first()
    user_by_email = Student.query.filter_by(email=email, is_verified=False).first()
    user_by_matric_no = Student.query.filter_by(matricNo=matricNo, is_verified=False).first()
   
    if is_user_verified:
        return {"error_message": "Student already exists"}, HTTP_409_CONFLICT
    if user_by_matric_no:
        return {"error_message": f"{matricNo} registered but not verified"}, HTTP_409_CONFLICT
    if user_by_email and not is_user_verified:
        return {"error_message": f"{email} registered but not verified"}, HTTP_409_CONFLICT
    if not firstName:
         return{"error_message": "Firstname is required"}, HTTP_400_BAD_REQUEST
    if not middleName:
         return{"error_message":"Middlename is required"}, HTTP_400_BAD_REQUEST
    if not lastName:
         return{"error_message": "Lastname is required"}, HTTP_400_BAD_REQUEST
    if not validators.email(email):
        return {"error_message":"Invalid email address"}, HTTP_400_BAD_REQUEST
    if not startDate:
         return{"error_message": "Start date is required"}, HTTP_400_BAD_REQUEST
    if not endDate:
         return{"error_message": "End date is required"}, HTTP_400_BAD_REQUEST
    if not supervisorName:
         return{"error_message": "Supervisor name is required"}, HTTP_400_BAD_REQUEST
    if not gender:
         return{"error_message": "Gender is required"}, HTTP_400_BAD_REQUEST
    if not matricNo:
         return{"error_message": "Matriculation is required"}, HTTP_400_BAD_REQUEST
    if not department:
         return{"error_message": "Department is required"}, HTTP_400_BAD_REQUEST
    if not ppa:
         return{"error_message": "Place of Attachment is required"}, HTTP_400_BAD_REQUEST
    if not is_valid_password(password):
        return {"error_message": "Invalid password"}, HTTP_400_BAD_REQUEST
    if not role:
        return {"error_message": "Select your role"}, HTTP_400_BAD_REQUEST
    
    # Convert the string to a datetime object
    startDate = datetime.datetime.strptime(startDate, "%Y-%m-%d")
    endDate = datetime.datetime.strptime(endDate, "%Y-%m-%d")

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
        user = Student(
            firstName=firstName, middleName=middleName, lastName=lastName, email=email, 
            startDate=startDate, endDate=endDate, supervisorName= supervisorName, gender=gender, matricNo=matricNo, 
            department=department, course=course, level=level, ppa=ppa, password=hashed_password,
            otp=otp, role=role, expiration_time=expiration_time
            )
        db.session.add(user)
        db.session.commit()
        return {"success_message": "Authentication code sent to user email"}, HTTP_200_OK
    except Exception as e:
            return {"error_message": f"error sending authentication code. Reason{e}"}, HTTP_500_INTERNAL_SERVER_ERROR
    
    # # add user to database
    # user = Student(email=email, password=hashed_password, otp=otp, expiration_time=expiration_time)
    # db.session.add(user)
    # db.session.commit()

    # return {"success": "Verification code has been sent to ur email", "email": email}, HTTP_201_CREATED

# register supervisor
@auth_blueprint.route('/supervisor/register', methods=['POST'])
def register_supervisor():

    firstName = request.json['firstname'];
    middleName = request.json['middlename']
    lastName = request.json['lastname']
    email = request.json['email'] 
    gender  = request.json['gender']   
    department = request.json['department']
    salutation = request.json['salutation']
    password = request.json['password']
    role = request.json['role']

    # clean input
    firstName = Markup.escape(firstName)
    middleName = Markup.escape(middleName)
    lastName = Markup.escape(lastName)
    email = Markup.escape(email)
    gender =  Markup.escape(gender)
    department =  Markup.escape(department)
    salutation =  Markup.escape(salutation)
    password =  Markup.escape(password)
    role =  Markup.escape(role)

    is_user_verified = Supervisor.query.filter_by(email=email, is_verified=True).first()
    user_by_email = Supervisor.query.filter_by(email=email, is_verified=False).first()
   
    if is_user_verified:
        return {"error_message": "Student already exists"}, HTTP_409_CONFLICT
    if user_by_email and not is_user_verified:
        return {"error_message": f"{email} registered but not verified"}, HTTP_409_CONFLICT
    if not firstName:
         return{"error_message": "Firstname is required"}, HTTP_400_BAD_REQUEST
    if not middleName:
         return{"error_message":"Middlename is required"}, HTTP_400_BAD_REQUEST
    if not lastName:
         return{"error_message": "Last name is required"}, HTTP_400_BAD_REQUEST
    if not validators.email(email):
        return {"error_message":"Invalid email address"}, HTTP_400_BAD_REQUEST
    if not gender:
         return{"error_message": "Gender is required"}, HTTP_400_BAD_REQUEST
    if not department:
         return{"error_message": "Department is required"}, HTTP_400_BAD_REQUEST
    if not is_valid_password(password):
        return {"error_message": "Invalid password"}, HTTP_400_BAD_REQUEST
    if not role:
        return {"error_message": "Select your role"}, HTTP_400_BAD_REQUEST
    

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
        user = Supervisor(
            firstName=firstName, middleName=middleName, lastName=lastName, gender=gender, email=email, 
            department=department, salutation=salutation, role=role, password=hashed_password, 
            otp=otp,  expiration_time=expiration_time
            )
        db.session.add(user)
        db.session.commit()
        return {"success_message": "Authentication code sent to user email"}, HTTP_200_OK
    except Exception as e:
            return {"error_message": f"error sending authentication code. Reason{e}"}, HTTP_500_INTERNAL_SERVER_ERROR
    

# verify user
@auth_blueprint.route('/verify-email/<token>', methods=['GET'])
def verify_user(token):
    serializer = URLSafeTimedSerializer(os.environ.get('SECRET_KEY'))
    try:
        user_email = serializer.loads(token, salt='email-verification', max_age=6000)
       
        # fetch user from database with retrieved email
        user = Student.query.filter_by(email=user_email).first()
        # if user does not exist in database
        if user is None:
            return {"error_message": "Student does not exist, kindly Sign up to continue"}, HTTP_404_NOT_FOUND
        
        #  if user is already verified
        if user.is_verified:
            return {"error_message": "Student already verified."}, HTTP_400_BAD_REQUEST
        
        # compare input code and retrieved code
        if user and not user.is_verified:

            # print(input_code ==  user.otp)
            # update user is_verified status in the databse
            user.is_verified = True
            db.session.add(user)
            db.session.commit()
            # delete email from session
            session.pop('email', None)
            return {"success_message": "Student verification successful"},  HTTP_200_OK
    except Exception as e:
         return {"error_message": f"{e}"}

# verify user using authentication code
@auth_blueprint.route('/verify-user', methods=['POST'])
def verify_User():
        # get code and email from form
    email = request.json['email']
    input_code = request.json['code']
    role = request.json['role']

    # clean email and code
    email = Markup.escape(email)
    input_code =  Markup.escape(input_code)
    role = Markup.escape(role);

    if role == "student":
         # fetch user from database with retrieved email
        user = Student.query.filter_by(email=email).first()
        # if user does not exist in database
        if user is None:
            return {"error_message": "Student does not exist, kindly Sign up to continue"}, HTTP_404_NOT_FOUND
        
        #  if user is already verified
        if user.is_verified:
            return {"error_message": "Student already verified, you can proceed to login"}, HTTP_400_BAD_REQUEST
        
        # compare input code and retrieved code
        user_otp = user.otp
        if input_code != user_otp:
            return {"error_message": "Code does not match"}, HTTP_400_BAD_REQUEST
        
        time_difference = user.expiration_time - datetime.datetime.utcnow()
        
        if time_difference.total_seconds() <= 0:
            return {"error_message": "token has expired"}
        
        # compare input code and retrieved code
        if user and user_otp == input_code:

            # print(input_code ==  user.otp)
            # update user is_verified status in the databse
            user.is_verified = True
            db.session.add(user)
            db.session.commit()
            # delete email from session
            session.pop('email', None)
            return {"success_message": "Student verification successful"},  HTTP_200_OK

    if role == "supervisor":
         # fetch user from database with retrieved email
        user = Supervisor.query.filter_by(email=email).first()
        # if user does not exist in database
        if user is None:
            return {"error_message": "User does not exist, kindly Sign up to continue"}, HTTP_404_NOT_FOUND
        
        #  if user is already verified
        if user.is_verified:
            return {"error_message": "User already verified, you can proceed to login"}, HTTP_400_BAD_REQUEST
        
        # compare input code and retrieved code
        user_otp = user.otp
        if input_code != user_otp:
            return {"error_message": "Code does not match"}, HTTP_400_BAD_REQUEST
        
        time_difference = user.expiration_time - datetime.datetime.utcnow()
        
        if time_difference.total_seconds() <= 0:
            return {"error_message": "token has expired"}
        
        # compare input code and retrieved code
        if user and user_otp == input_code:

            # print(input_code ==  user.otp)
            # update user is_verified status in the databse
            user.is_verified = True
            db.session.add(user)
            db.session.commit()
            # delete email from session
            session.pop('email', None)
            return {"success_message": "User verification successful"},  HTTP_200_OK
    
    
# resend verification code
@auth_blueprint.route('/resend_code', methods=['POST'])
def resend_code():

    role = request.json['resend_role']
    email = request.json['email']

    if role == 'student':

        user_verified = Student.query.filter_by(email=email, is_verified=True).first()
        user = Student.query.filter_by(email=email, is_verified=False).first()

        if user_verified:
            return {"error_message": "Student already verified"}, HTTP_409_CONFLICT
        if not user:
            return {"error_message": "Student not found"}, HTTP_404_NOT_FOUND
        if user:
            # expiration time
            expiration_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
            otp = generate_random_code()
            user.otp = otp
            user.expiration_time = expiration_time

            db.session.add(user)
            db.session.commit()
            sendEmail(email, otp)
            return {"success_message": f"Authentication code sent to {email}"}
    
    if role == "supervisor":

        user_verified = Supervisor.query.filter_by(email=email, is_verified=True).first()
        user = Supervisor.query.filter_by(email=email, is_verified=False).first()

        if user_verified:
            return {"error_message": "User already verified"}, HTTP_409_CONFLICT
        if not user:
            return {"error_message": "User not found"}, HTTP_404_NOT_FOUND
        if user:
            # expiration time
            expiration_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
            otp = generate_random_code()
            user.otp = otp
            user.expiration_time = expiration_time

            db.session.add(user)
            db.session.commit()
            sendEmail(email, otp)
            return {"success_message": f"Authentication code sent to {email}"}
        
# user login
@auth_blueprint.route('/student/login', methods=['POST'])
def student_login():
        
        email = request.json.get('email')
        password = request.json.get('password')
        remember_me = request.json.get('rememberme')

        # clean inputs
        email =  Markup.escape(email)
        password =  Markup.escape(password)
        remember_me = Markup.escape(remember_me)

        user = Student.query.filter_by(email=email).first()

        if not user:
            return {"error_message": "Student not found. Sign up to continue"}, HTTP_401_UNAUTHORIZED_ACCESS

        # check if user is signed up but not authenticate
        if user and not user.is_verified:
            return {"error_message": "Student not yet authenticate"}, HTTP_401_UNAUTHORIZED_ACCESS
        
        if user and user.is_verified:
            user_id = user.id

            is_password_correct = check_password_hash(user.password, password)
            if is_password_correct:

                access_token = create_access_token(identity=user_id)
                # generate csrf token
                csrf_token = urandom(16).hex();

                response = make_response({
                    'success_message': 'Login successful!', 
                    'firstName':user.firstName,
                    'middleName': user.middleName,
                    'lastName':user.lastName,
                    "email": user.email, 
                    'startDate': user.startDate,
                    'endDate': user.endDate ,
                    'csrf_token': csrf_token,
                    'role': user.role,
                    'gender': user.gender,
                    'matricNo': user.matricNo,
                    'department':user.department,
                    'course':user.course,
                    'level':user.level,
                    'ppa': user.ppa
                })
                
                # Set the http-only JWT cookie
                response.set_cookie('access_token', access_token, httponly=False)
                # set_access_cookies(response, access_token)
                # Set the double submit token as a readable cookie
                response.set_cookie('csrf_token', csrf_token, httponly=False)

                return response, HTTP_200_OK
            else:
                return {"error_message": "Incorrect password"}, HTTP_401_UNAUTHORIZED_ACCESS
 
# supervisor login
@auth_blueprint.route('/supervisor/login', methods=['POST'])
def supervisor_login():
        
    email = request.json.get('email')
    password = request.json.get('password')
    remember_me = request.json.get('rememberme')

    # clean inputs
    email =  Markup.escape(email)
    password =  Markup.escape(password)

    user = Supervisor.query.filter_by(email=email).first()

    if not user:
        return {"error_message": "User not found. Sign up to continue"}, HTTP_401_UNAUTHORIZED_ACCESS

    # check if user is signed up but not authenticate
    if user and not user.is_verified:
        return {"error_message": "User not yet authenticate"}, HTTP_401_UNAUTHORIZED_ACCESS
    
    if user and user.is_verified:

        expiry_date = datetime.datetime.now()
        user_id = user.id

        if remember_me == True:
            expiry_date = datetime.now() + datetime.timedelta(days=120) 

        is_password_correct = check_password_hash(user.password, password)

        if is_password_correct:

            # create access
            access_token = create_access_token(identity=user_id)
            # generate csrf token
            csrf_token = urandom(16).hex();

            response = make_response({
                'success_message': 'Login successful!', 
                'id': user.id,
                'firstName':user.firstName,
                'middleName': user.middleName,
                'lastName':user.lastName,
                'gender': user.gender,
                "email": user.email, 
                'department': user.department,
                'salutation': user.salutation,
                'csrf_token': csrf_token,
                'access_token': access_token,
                'role': user.role
            })
            
            # Set the http-only JWT cookie
            # response.set_cookie('access_token_cookie', access_token, expires=expiry_date, secure=False, httponly=False, samesite='Strict')
            # Set the double submit token as a readable cookie
            response.set_cookie('csrf_token', csrf_token)
            response.set_cookie('access_token_cookie', access_token, expires=expiry_date, secure=False, httponly=False, samesite='None')
            # set_access_cookies(response, access_token)

            return response, HTTP_200_OK
        else:
            return {"error_message": "Incorrect password"}, HTTP_401_UNAUTHORIZED_ACCESS

# user logout
@auth_blueprint.post('/logout')
@jwt_required()
def logout():
    response = make_response({"success_message": "logout successful!"})
    unset_jwt_cookies(response)
    return response