# -*- coding: utf-8; -*-
#!/usr/bin/env python

__author__ = 'Olexander Yermakov'
__email__ = 'mannavard1611@gmail.com'


from app import app
from app import db
from app import lm
from app import oid

from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for

from flask.ext.login import current_user
from flask.ext.login import login_required
from flask.ext.login import login_user
from flask.ext.login import logout_user

from forms import LoginForm
import models


@app.route('/')
@app.route('/index')
@login_required
def index():
    user = g.user
    posts = [{'author': {'nickname': 'Tommy'},
              'body': 'wow'},
             {'author': {'nickname': 'Mick'},
              'body': 'yep'}]

    return render_template('index.html',
                           title='Home',
                           user=user,
                           posts=posts)


@app.route('/login', methods=['GET', 'POST'])
@oid.loginhandler
def login():
    if g.user and g.user.is_authenticated():
        return redirect(url_for('index'))

    form = LoginForm()

    if form.validate_on_submit():
        session['remember_me'] = form.remember_me.data
        return oid.try_login(form.openid.data, ask_for=['nickname', 'email'])
    return render_template('login.html',
                           title='Sign in',
                           form=form,
                           providers=app.config['OPENID_PROVIDERS'])


@oid.after_login
def after_login(resp):
    if not resp.email:
        flash('Invalid login. Please try again.')
        return redirect(url_for('login'))
    user = models.User.query.filter_by(email=resp.email).first()

    if not user:
        nickname = resp.nickname
        if not nickname:
            nickname = resp.email.split('@')[0]
        user = models.User(nickname=nickname, email=resp.email, role=models.ROLE_USER)
        db.session.add(user)
        db.session.commit()

    if 'remember_me' in session:
        remember_me = session['remember_me']
        session.pop('remember_me', None)
    else:
        remember_me = False
    login_user(user, remember=remember_me)
    return redirect(request.args.get('next') or url_for('index'))


@app.before_request
def before_request():
    g.user = current_user

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@lm.user_loader
def load_user(user_id):
    return models.User.query.get(user_id)
