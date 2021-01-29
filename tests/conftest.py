from photostore import create_app, db
from flask.testing import FlaskClient
import pytest
import os


@pytest.fixture
def app():
    app = create_app('photostore.config.TestConfig')
    if os.path.exists("/tmp/testdb.db"):
        os.remove("/tmp/testdb.db")

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app) -> FlaskClient:

    with app.test_client() as client:
        yield client
