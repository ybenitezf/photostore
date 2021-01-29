from photostore import ma
from photostore.models.security import User
from photostore.models.security import Role


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
