from . import ma
from .models.security import User
from .models.security import Role
from pprint import pprint


class UserSchema(ma.SQLAlchemySchema):

    class Meta:
        model = User

    id = ma.auto_field()
    name = ma.auto_field()
    username = ma.auto_field()
    


class RoleSchema(ma.SQLAlchemySchema):

    class Meta:
        model = Role

    id = ma.auto_field()
    name = ma.auto_field()
    description = ma.auto_field()
