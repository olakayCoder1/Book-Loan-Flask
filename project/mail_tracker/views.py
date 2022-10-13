from mail_tracker import app , db , bcrypt
from mail_tracker.models import Book , User , Loan
from flask import Response , jsonify, request 
from mail_tracker.serializers import BookSerializer , UserSerializer
from mail_tracker.utils import TokenService , authorization_required , MailService , admin_required
import jwt
import string
import random
import asyncio
import os

@app.route('/')
def home():
    data = []
    return jsonify( data , 200)


@app.route('/register' , methods=['POST'])
def sign_up():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    attempt_user = User.query.filter_by(email=email).first()
    if attempt_user :
        return jsonify( {  'message' : 'Email already exist'} , 400)
        
    new_user  = User(email=email, password=password)
    try:
        new_user.save()
    except:
        db.session.rollback()

    return jsonify( {  'message' : 'Email you are now logged in'} , 200)


@app.route('/login' , methods=['GET', 'POST'])
async def sign_in():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    attempt_user = User.query.filter_by(email=email).first()
    if attempt_user.sign_two_factor_authentication :
        code = ''.join( random.choices(string.digits , k=5))
        send_email = asyncio.create_task( MailService.send_sign_two_factor_authentication_mail(attempt_user.email , code))
        
        token = TokenService.create_2fa_token(attempt_user.id , int(code))
        return jsonify({  'message' : 'Authentication code has been sent to the user email', 'token': token  }) , 200

    if attempt_user and attempt_user.check_password(password):
        id = attempt_user.id
        user_token = TokenService.create_auth_token(id)

        if user_token: 

            res = {
                'id' : attempt_user.id ,
                'email' : attempt_user.email ,
                'token' : user_token
            }
            return jsonify(res) , 200
        return jsonify( {  'message' : 'System down'} , 500 )
    return jsonify( {  'message' : 'Invalid login credentials'} , 401)


@app.route('/login/two-factor-authentication' , methods=['GET' ,'POST'])
def sign_two_factor_authentication():
    data = request.get_json()
    code = data.get('code')
    token = data.get('token')
    try:
        payload = jwt.decode(token, os.getenv('JWT_SECRET') , algorithms=[os.getenv('JWT_ALGO')])
    except:
        return jsonify( {  'message' : 'Authentication code error'} , 401)
    if int(payload['code']) == int(code ) :
        attempt_user = User.query.get_or_404(payload.get('id'))
        user_token = TokenService.create_auth_token(attempt_user.id)
        if user_token: 
            res = {
                'id' : attempt_user.id ,
                'email' : attempt_user.email ,
                'token' : user_token
            }
            return jsonify(res) , 200
        return jsonify( {  'message' : 'System down'} , 500 )
    return jsonify( {  'message' : 'Authentication code'} , 401)



@app.route('/logout')
@authorization_required
def sign_out(current_user):
    token = request.headers['x-access-token']

    return jsonify( {  'message' : 'Invalid login credentials'} , 200)


@app.route('/password-change', methods=['POST'])
@authorization_required
def password_change(current_user):
    data = request.get_json()
    old_password = data.get('old-password')
    password = data.get('password')
    confirm_password = data.get('confirm-password')
    if password and confirm_password :
        if password == confirm_password :
            if current_user.check_password( old_password) :
                current_user.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
                try:
                    current_user.save()
                    return jsonify({'message': 'Password updated successfully'}) , 200
                except:
                    db.session.rollback()
                    return jsonify({'message':'An error occurred'}) , 401
            return jsonify({'message':'Old password did not match'}) , 401
        return jsonify({'message':'Password does not match'}) , 401
    return jsonify({'message' : 'Either password and confirm password is not provided'}) , 401


@app.route('/password-reset', methods=['POST'])
async def password_reset_email():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if user:
        ## SEND EMAIL TO USER
        token = TokenService.create_password_reset_token(user.id)
        send_email = asyncio.create_task(MailService.send_reset_mail(user.email , token))
    return jsonify( { 
        'message':'Instruction to reset your password has been sent to the provided email if existed on our server'
        }) , 200


@app.route('/password-reset/<token>/confirm', methods=['POST'])
def password_reset_confirm(token):
    data = request.get_json()
    password = data.get('password', None)
    confirm_password = data.get('confirm_password', None)
    if password and confirm_password :
        if password == confirm_password :
            payload = jwt.decode(token, os.getenv('JWT_SECRET'), algorithms=[os.getenv('JWT_ALGO')])
            user_id = payload.get('id')
            if TokenService.validate_password_token(token, user_id ) :
                user = User.query.get_or_404(user_id)

                user.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
                try:
                    user.update(password_hash=bcrypt.generate_password_hash(password).decode('utf-8'))
                    return jsonify({'message': 'Password updated successfully'}) , 200
                except:
                    db.session.rollback()
                    return jsonify({'message':'Password reset token is invalid'}) , 401
        return jsonify({'message':'Password does not match'}) , 401
    return jsonify({'message':'Either password or confirm password is not provided'}) , 401


@app.route('/books')
def get_all_books():  
    book = Book.query.all()
    serializer = BookSerializer(many=True)
    data = serializer.dump(book)
    return jsonify(data) , 200


@app.route('/books/<id>', methods=['PUT' ,'GET'])
def get_book(id):
    book = Book.query.get_or_404(id)
    if request.method == 'GET':
        serializer = BookSerializer()
        data = serializer.dump(book)
        return jsonify(data), 200


@app.route('/books/<id>' , methods=['DELETE'])
@authorization_required
def delete_book(current_user,id):
    book = Book.query.all()
    return Response('response')


@app.route('/books' , methods=['POST'])
@authorization_required
def add_book(current_user):
    data = request.get_json()
    new_book = Book(name=data.get('name'))
    db.session.add(new_book)
    db.session.commit()
    serializer = BookSerializer()
    data = serializer.dump(new_book)
    return jsonify(data), 201


@app.route('/books/loan/<book_id>' , methods=['GET'])
@authorization_required
def loan_book(current_user ,book_id):
    # data = request.get_json()
    # if Loan.check_has_loan_book(user_id=data['user_id'], book_id=data['book_id']):
    if Loan.check_has_loan_book(user_id=current_user.id , book_id=book_id):
        return jsonify({ 'message' : 'You have a copy of the book in your loan box' }) , 400
    
    book = Loan(book_id=int(book_id) , user_id=int(current_user.id))
    try:
        db.session.add(book)
        db.session.commit()
    except:
        db.session.rollback()
    return jsonify({ 'message' : 'Book added to your loan list' }) , 200


@app.route('/books/loan/<book_id>/return')
@authorization_required 
def return_loan_book(current_user,book_id):
    if Loan.check_has_loan_book(user_id=current_user.id , book_id=book_id):
        book = Loan.query.filter_by(user_id=current_user.id , book_id=book_id).first()
        book.has_returned = True
        try:
            db.session.add(book)
            db.session.commit()
        except:
            db.session.rollback()
        return jsonify({ 'message' : 'Book remove from your loan box' }) , 200
    return jsonify({ 'message' : 'You do not have a copy of the book in your loan box' }) , 400


@app.route('/books' , methods=['POST'])
@authorization_required
def user(current_user):
    data = request.get_json()
    new_book = Book(name=data.get('name'))
    db.session.add(new_book)
    db.session.commit()
    serializer = BookSerializer()
    data = serializer.dump(new_book)
    return jsonify(data), 201



## ADMINISTRATOR ROUTE
@app.route('/users')
# @admin_required 
def users_list():
    data = request.get_json()
    users = User.query.all()

    serializer = BookSerializer(many=True)
    data = serializer.dump(users)

    return jsonify(data), 200