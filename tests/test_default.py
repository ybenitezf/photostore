from flask.testing import FlaskClient
from . import ClientUtility

def test_default_route(client):
    res = client.get('/')

    assert "users/login" in res.headers.get('Location')
    assert res.status_code == 302

    res = client.get('/', follow_redirects=True)
    assert res.status_code == 200
    assert b"username" in res.data
    assert b"password" in res.data

def test_security(client: FlaskClient):
    ClientUtility.createUser(client, 'jdoe', 'secret')
    res = ClientUtility.login(client, 'jdoe', 'secret')
    assert res.status_code == 200
    print(res.data)
    assert b"photo.index::testcase" in res.data
