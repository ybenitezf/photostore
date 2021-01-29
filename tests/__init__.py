
from photostore.models.security import create_user
from photostore import db
from flask.testing import FlaskClient


class ClientUtility(object):

    @classmethod
    def createUser(
            cls, client: FlaskClient, username, password, email='', name=''):
        with client.application.app_context():
            u = create_user(username, password, email=email, name=name)
            db.session.add(u)
            db.session.commit()

        return u

    @classmethod
    def login(cls, client: FlaskClient, username, password):
        return client.post('/users/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    @classmethod
    def logout(cls, client: FlaskClient):
        return client.get('/logout', follow_redirects=True)
