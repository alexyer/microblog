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


class LoginForm(Form):
    """LoginForm"""
    openid = TextField('openid', validators=[Required()])
    remember_me = BooleanField('remember_me', default=False)
        

class EditForm(Form):
    nickname = TextField('nickname', validators=[Required()])
    about_me = TextAreaField('about_me', validators=[Length(min=0, max=140)])
