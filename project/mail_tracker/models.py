from mail_tracker import db  , bcrypt
from datetime import datetime , timedelta
import jwt



class User(db.Model):
    id = db.Column(db.Integer , primary_key=True)
    email =  db.Column( db.String(100) , nullable=False , unique=True )
    password_hash = db.Column(db.String(64) , nullable=False )
    created_at = db.Column(db.DateTime() , nullable=False , default=datetime.utcnow)
    loan = db.relationship( 'Loan' , backref='loan_user', lazy=True)
    token = db.relationship('Token', backref='token_owner', lazy=True) 
    is_active = db.Column(db.Boolean() , default=True)
    is_admin = db.Column(db.Boolean() , default=False)
    sign_two_factor_authentication = db.Column(db.Boolean() , default=False )
    loan_access_maximum  = db.Column(db.Integer() , default=3)

    def save(self):
        db.session.add(self)
        db.session.commit()


    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self , *args , **kwargs):
        if 'email' in args:
            self.email = args.get('email')
        if 'is_admin' in args:
            self.is_admin = args.get('is_admin')
        if 'loan_access_maximum' in args:
            self.loan_access_maximum = args.get('loan_access_maximum')
        if 'password_hash' in args:
            self.password_hash = args.get('password_hash')
        if 'sign_two_factor_authentication' in args:
            self.sign_two_factor_authentication = args.get('sign_two_factor_authentication')
        try:
            self.save()
        except:
            db.session.rollback()




    @property
    def password(self):
        return self.password

    @password.setter
    def password(self, text_password):
        self.password_hash = bcrypt.generate_password_hash(text_password).decode('utf-8')

    
    def check_password(self, text_password):
        return bcrypt.check_password_hash(self.password_hash, text_password)


class Book(db.Model):
    id = db.Column(db.Integer() , primary_key=True)
    name = db.Column(db.String(100) , nullable=False) 
    loan = db.relationship( 'Loan' , backref='loan_book', lazy=True)
    created_at = db.Column(db.DateTime() , nullable=False , default=datetime.utcnow)

    def save(self):
        db.session.add(self)
        db.session.commit()


    def delete(self):
        db.session.delete(self)
        db.session.commit()


    def update(self , *args , **kwargs):
        if 'name' in kwargs:
            self.name = kwargs.get('name')
        try:
            self.save()
        except:
            db.session.rollback()


class Loan(db.Model):
    id = db.Column(db.Integer() , primary_key=True)
    book_id = db.Column(db.Integer(), db.ForeignKey('book.id') )
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id') )
    has_returned = db.Column(db.Boolean() , nullable=False , default=False)
    due_date = db.Column(db.DateTime() , nullable=False , default=datetime.utcnow )
    created_at = db.Column(db.DateTime() , nullable=False , default=datetime.utcnow)


    def save(self):
        db.session.add(self)
        db.session.commit()


    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self , *args , **kwargs):
        if 'has_returned' in kwargs:
            self.has_returned = kwargs.get('has_returned')
        try:
            self.save()
        except:
            db.session.rollback()


    def __repr__(self):
        return f"loan id {self.id}"

    @property
    def date(self):
        return self.date

    @date.setter
    def date(self):
        self.due_date = datetime.utcnow() + timedelta(days=7)
        date = None


    @classmethod
    def check_loan_eligibility(cls , user_id:int) :
        has_reach_max_loan = len(cls.query.filter_by(user_id=user_id).all()) < 4
        return True if has_reach_max_loan else False


    @classmethod
    def check_has_loan_book(cls , user_id:int , book_id:int) :
        has_reach_max_loan = len(cls.query.filter_by(user_id=user_id , book_id=book_id).all()) > 0
        return True if has_reach_max_loan else False






class Token(db.Model):
    id = db.Column(db.Integer() , primary_key=True)
    user =  db.Column(db.Integer(), db.ForeignKey('user.id'))
    token = db.Column(db.Text(), nullable=False)
    created_at = db.Column(db.DateTime() , nullable=False , default=datetime.utcnow)
    blacklist = db.relationship('BlacklistedToken',  backref='token_blacklisted', lazy=True)



    def save(self):
        db.session.add(self)
        db.session.commit()


    def delete(self):
        db.session.delete(self)
        db.session.commit()


    def update(self , *args , **kwargs):
        if 'blacklist' in kwargs:
            self.blacklist = kwargs.get('blacklist')
        if 'token' in kwargs:
            self.token = kwargs.get('token')
        try:
            self.save()
        except:
            db.session.rollback()


    def __repr__(self) -> str: 
        return str(self.id)




class BlacklistedToken(db.Model):
    id = db.Column(db.Integer() , primary_key=True)
    token = db.Column(db.Integer(), db.ForeignKey('token.id'))
    blacklisted_at = db.Column(db.DateTime() , nullable=False , default=datetime.utcnow)


    def save(self):
        db.session.add(self)
        db.session.commit()


    def delete(self):
        db.session.delete(self)
        db.session.commit()

    
    def update(self , *args , **kwargs):
        if 'token' in kwargs:
            self.token = kwargs.get('token')
        try:
            self.save()
        except:
            db.session.rollback()



