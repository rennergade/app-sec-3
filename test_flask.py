"""
You can auto-discover and run all tests with this command:

    $ pytest

Documentation:

* https://docs.pytest.org/en/latest/
* https://docs.pytest.org/en/latest/fixture.html
* http://flask.pocoo.org/docs/latest/testing/
"""

import pytest

import app as flask_app

@pytest.fixture
def app():
    app = flask_app.create_app()
    app.debug = True
    return app.test_client()


def test_home(app):
    res = app.get("/")
    # print(dir(res), res.status_code)
    assert res.status_code == 200

def test_register(app):
    res = app.get("/register")
    # print(dir(res), res.status_code)
    assert res.status_code == 200

def test_login(app):
    res = app.get("/login")
    # print(dir(res), res.status_code)
    assert res.status_code == 200

def test_spell_check(app):
    res = app.get("/spellcheck")
    # print(dir(res), res.status_code)
    assert res.status_code == 404

def test_admin_no_login(app):
    res = app.get("/admin/history")
    # print(dir(res), res.status_code)
    assert res.status_code == 404

def test_admin_query_no_login(app):
    res = app.get("/admin/history/query1")
    # print(dir(res), res.status_code)
    assert res.status_code == 404

def test_user_no_login(app):
    res = app.get("/user1/history")
    # print(dir(res), res.status_code)
    assert res.status_code == 404

def test_user_query_no_login(app):
    res = app.get("/user1/history/query1")
    # print(dir(res), res.status_code)
    assert res.status_code == 404

