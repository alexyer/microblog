# -*- coding: utf-8; -*-
#!/usr/bin/env python

__author__ = 'Olexander Yermakov'
__email__ = 'mannavard1611@gmail.com'


from flask.ext.wtf import Form

from wtforms import BooleanField
from wtforms import TextField

from wtforms.validators import Required


class LoginForm(Form):
    """LoginForm"""
    openid = TextField('openid', validators=[Required()])
    remember_me = BooleanField('remember_me', default=False)
        
