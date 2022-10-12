from marshmallow import Schema , fields



class BookSerializer(Schema):
    id = fields.Integer()
    name = fields.String()
    created_at = fields.DateTime()


class UserSerializer(Schema):
    id = fields.Integer()
    email = fields.String()
    is_active = fields.Boolean()
    is_admin = fields.Boolean()
    loan_access_maximum = fields.Integer()
    created_at = fields.DateTime()


