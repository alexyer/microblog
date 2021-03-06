# -*- coding: utf-8; -*-
#!/usr/bin/env python

__author__ = 'Olexander Yermakov'
__email__ = 'mannavard1611@gmail.com'


from app import app
from app import db
from app import lm
from app import oid

from datetime import datetime

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
from forms import SearchForm
from forms import PostForm

import config
import models


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@app.route('/index/<int:page>', methods=['GET', 'POST'])
@login_required
def index(page=1):
    user = g.user
    form = PostForm()

    if form.validate_on_submit():
        post = models.Post(body=form.post.data, timestamp=datetime.utcnow(), author=g.user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('index'))

    posts = g.user.followed_posts().paginate(page, config.POSTS_PER_PAGE)

    return render_template('index.html',
                           title='Home',
                           form=form,
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
        nickname = models.User.make_unique_nickname(nickname)
        user = models.User(nickname=nickname, email=resp.email, role=models.ROLE_USER)

        db.session.add(user)
        db.session.commit()

        db.session.add(user.follow(user))
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
        g.search_form = SearchForm()


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/user/<nickname>')
@app.route('/user/<nickname>/<int:page>')
def user(nickname, page=1):
    user = models.User.query.filter_by(nickname=nickname).first()

    if not user:
        flash('User {nick} not found.'.format(nick=nickname))
        return redirect(url_for('index'))

    posts = user.posts.paginate(page, config.POSTS_PER_PAGE, False)

    return render_template('user.html',
                           user=user,
                           posts=posts)


@app.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    form = EditForm(g.user.nickname)
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


@app.route('/follow/<nickname>')
@login_required
def follow(nickname):
    user = models.User.query.filter_by(nickname=nickname).first()
    if not user:
        flash('User {nickname} not found'.format(nickname=nickname))
        return redirect(url_for('index'))
    elif user == g.user:
        flask('You can\'t follow yourself')
        return redirect(url_for('user', nickname=nickname))

    u = g.user.follow(user)
    if not u:
        flash('Can\'t follow {nickname}'.format(nickname=nickname))
        return redirect(url_for('user', nickname=nickname))

    db.session.add(u)
    db.session.commit()

    flash('You are now following {nickname}'.format(nickname=nickname))
    return redirect(url_for('user', nickname=nickname))


@app.route('/unfollow/<nickname>')
@login_required
def unfollow(nickname):
    user = models.User.query.filter_by(nickname = nickname).first()
    if not user:
        flash('User {nickname} not found.'.format(nickname=nickname))
        return redirect(url_for('index'))
    if user == g.user:
        flash('You can\'t unfollow yourself!')
        return redirect(url_for('user', nickname = nickname))
    u = g.user.unfollow(user)
    if not u:
        flash('Cannot unfollow {nickname}.'.format(nickname=nickname))
        return redirect(url_for('user', nickname = nickname))
    db.session.add(u)
    db.session.commit()
    flash('You have stopped following {nickname}.'.format(nickname=nickname))
    return redirect(url_for('user', nickname = nickname))


@app.route('/search', methods=['POST'])
@login_required
def search():
    if not g.search_form.validate_on_submit():
        return redirect(url_for('index'))
    return redirect(url_for('search_results', query=g.search_form.data))


@app.route('/search_results/<query>')
@login_required
def search_results(query):
    results = models.Post.query.whoosh_search(query, config.MAX_SEARCH_RESULTS).all()
    return render_template('search_results.html',
                           query=query,
                           results=results)


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
