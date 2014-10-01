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

from forms import EditForm
from forms import LoginForm
import models

from datetime import datetime


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
    if g.user.is_authenticated():
        g.user.last_seen = datetime.utcnow()
        db.session.add(g.user)
        db.session.commit()


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/user/<nickname>')
def user(nickname):
    user = models.User.query.filter_by(nickname=nickname).first()

    if not user:
        flash('User {nick} not found.'.format(nick=nickname))
        return redirect(url_for('index'))

    posts = [{'author': user, 'body': 'Test'},
             {'author': user, 'body': 'Test2'}]

    return render_template('user.html',
                           user=user,
                           posts=posts)


@app.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    form = EditForm()
    if form.validate_on_submit():
        g.user.nickname = form.nickname.data
        g.user.about_me = form.about_me.data
        db.session.add(g.user)
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit'))
    else:
        form.nickname.data = g.user.nickname
        form.about_me.data = g.user.about_me
    return render_template('edit.html',
                           form=form)


@lm.user_loader
def load_user(user_id):
    return models.User.query.get(user_id)


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
