from flask import jsonify, request
import jwt
from email.message import EmailMessage
import ssl
import smtplib
import os
from dotenv import load_dotenv
from typing import Dict
from datetime import datetime , timedelta
from mail_tracker import db
from mail_tracker.models import Token
import json
from mail_tracker.models import BlacklistedToken , User
from functools import wraps

load_dotenv()

def authorization_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        if not token:
            return jsonify({  'message' : 'Token is missing' }) , 401

        has_token_expired = TokenService.validate_token(str(token))
        if has_token_expired:
            return jsonify({  'message' : "Token expired! Login " }) , 401

        try:
            data = jwt.decode(token , os.getenv('JWT_SECRET')  , algorithms=[os.getenv('JWT_ALGO')])
            current_user = User.query.filter_by(id=data['id']).first()

            has_token_expired = TokenService.validate_token(str(token) , current_user.id )
            if has_token_expired:
                return jsonify({  'message' : "Token expired! Login " }) , 401

            if current_user.is_active == False :
                return jsonify({'message': 'You are account is on hold, contact the administrative'})

        except:
            return jsonify({'message':'Invalid token'}) , 401

        return f(current_user , *args , **kwargs)

    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        if not token:
            return jsonify({  'message' : 'Token is missing' }) , 401

        has_token_expired = TokenService.validate_token(str(token))
        if has_token_expired:
            return jsonify({  'message' : "Token expired! Login " }) , 401

        try:
            data = jwt.decode(token , os.getenv('JWT_SECRET') , algorithms=[os.getenv('JWT_ALGO')])
            current_user = User.query.filter_by(id=data['id']).first()
            has_token_expired = TokenService.validate_token(str(token) , current_user.id )
            if has_token_expired:
                return jsonify({  'message' : "Token expired! Login " }) , 401

            if current_user.is_admin != False :
                return jsonify({'message': 'You dont have access to this page'})

            if current_user.is_active == False :
                return jsonify({'message': 'You are account is on hold, contact the administrative'})
        except:
            return jsonify({'message':'Invalid token'}) , 401


        return f(current_user , *args , **kwargs)

    return decorated


class DateTimeEncoder(json.JSONEncoder):
    def default(self,o):
        if isinstance(o , datetime):
            return o.isoformat()
        return json.JSONEncoder.default(self, o)




class TokenService:
    def create_auth_token(id: int)-> str :
        payload = { 'id' : id ,  'expired_at' : datetime.utcnow() + timedelta(days=30) 
            }
        try:
            encoded_jwt = jwt.encode( payload , "secret", algorithm=os.getenv('JWT_ALGO') , json_encoder=DateTimeEncoder  )
      
        except Exception as e :
                return None
        token=encoded_jwt.decode('UTF-8')
        return token

    def create_2fa_token(id: int , code : int)-> str :
        payload = { 'id' : id ,  'expired_at' : datetime.utcnow() + timedelta(days=30)  , 'code' : code
            }
        try:
            encoded_jwt = jwt.encode( payload , os.getenv('JWT_SECRET'), algorithm=os.getenv('JWT_ALGO') , json_encoder=DateTimeEncoder  )
        
        except Exception as e :
                return None
        token=encoded_jwt.decode('UTF-8')
        return token

    def validate_token(token : str , user_id : int ):
        payload = jwt.decode(token, os.getenv('JWT_SECRET'), algorithms=[os.getenv('JWT_ALGO')])
        if payload.get('id') != user_id :
            return False
        if datetime.now() <  payload.get('expired_at') :
            return False
        if BlacklistedToken.query.filter_by(token=token).all() > 0 :
            return False
        return True



    def create_password_reset_token(id: int)-> str :
        payload = { 'id' : id ,  'expired_at' : datetime.utcnow() + timedelta(days=1)  , 'type': 'password-reset'  }
        try:
            encoded_jwt = jwt.encode( payload , os.getenv('JWT_SECRET'), algorithm=os.getenv('JWT_ALGO') , json_encoder=DateTimeEncoder  )
        
        except Exception as e :
                return None

        token = encoded_jwt.decode('UTF-8')
        return token

    def validate_password_token(token:str , user_id:int):
        payload = jwt.decode(token, os.getenv('JWT_SECRET'), algorithms=[os.getenv('JWT_ALGO')])
        if payload.get('id') != user_id :
            return False
        if datetime.now() <  payload.get('expired_at') :
            return False
        if payload.type == 'password-reset':
            return True

        return False




class MailService:
    

    async def send_reset_mail(receiver , token ):
        sender_email = os.getenv('EMAIL_SENDER') 
        receiver_email = receiver
        password = os.getenv('EMAIL_PASSWORD') 
        subject = "Password reset"
        body = f"""
                we receive a request to reset your password\n
                You can ignore if you don't make the request. Click the link below the to set new password.\n
                http://127.0.0.1:5000/api/v1/auth/password-reset/{token}/confirm
            """

        em = EmailMessage()
        em["From"] = receiver_email
        em["To"] = sender_email
        em["subject"] = subject
        em.set_content(body)
        context = ssl.create_default_context()

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", port=465, context=context) as connection:
                connection.login(sender_email, password)
                await connection.sendmail(sender_email, receiver_email, em.as_string())
        except:
            pass
        return True

    async def send_sign_two_factor_authentication_mail(receiver , code  ):
        sender_email = os.getenv('EMAIL_SENDER') 
        receiver_email = receiver
        password = os.getenv('EMAIL_PASSWORD') 
        subject = "Login attempt"
        body = f"""
                we receive a request to sign in your account\n
                You can ignore if you don't make the request.\n
                CODE : {code}
            """

        em = EmailMessage()
        em["From"] = receiver_email
        em["To"] = sender_email
        em["subject"] = subject
        em.set_content(body)
        context = ssl.create_default_context()

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", port=465, context=context) as connection:
                connection.login(sender_email, password)
                await connection.sendmail(sender_email, receiver_email, em.as_string())
        except:
            pass
        return True