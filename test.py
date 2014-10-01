# -*- coding: utf-8; -*-
#!/usr/bin/env python

__author__ = 'Olexander Yermakov'
__email__ = 'mannavard1611@gmail.com'


import os
import unittest


from config import basedir

from app import app
from app import db
from app import models


class TestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'test.db')
        self.app = app.test_client()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_avatar(self):
        u = models.User(nickname='john', email='john@gmail.com')
        avatar = u.avatar(128)
        expected = 'http://www.gravatar.com/avatar/1f9d9a9efc2f523b2f09629444632b5c?=mm&s=128'
        assert avatar == expected

    def test_make_unique_nickname(self):
        u = models.User(nickname='john', email='john@gmail.com')
        db.session.add(u)
        db.session.commit()

        nickname = models.User.make_unique_nickname('john')
        assert nickname != 'john'

        u = models.User(nickname = nickname, email = 'susan@example.com')
        db.session.add(u)
        db.session.commit()
        nickname2 = models.User.make_unique_nickname('john')

        assert nickname2 != 'john'
        assert nickname2 != nickname


if __name__ == '__main__':
    unittest.main()
