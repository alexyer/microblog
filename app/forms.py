# -*- coding: utf-8; -*-
#!/usr/bin/env python

__author__ = 'Olexander Yermakov'
__email__ = 'mannavard1611@gmail.com'


from flask.ext.wtf import Form

from wtforms import BooleanField
from wtforms import TextField
from wtforms import TextAreaField

from wtforms.validators import Length
from wtforms.validators import Required

from app import models


class LoginForm(Form):
    """LoginForm"""
    openid = TextField('openid', validators=[Required()])
    remember_me = BooleanField('remember_me', default=False)
        

class EditForm(Form):
    nickname = TextField('nickname', validators=[Required()])
    about_me = TextAreaField('about_me', validators=[Length(min=0, max=140)])

    def __init__(self, original_nickname, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.original_nickname = original_nickname

    def validate(self):
        if not Form.validate(self):
            return False

        if self.nickname.data == self.original_nickname:
            return True

        user = models.User.query.filter_by(nickname=self.nickname.data).first()

        if user:
            self.nickname.errors.append('This nickname is already in use. Please choose another one.')
            return False

        return True


class SearchForm(Form):
    search = TextField('search', validators=[Required()])
