import json
import os
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from flaskr.insta.link import InstagramBot
from flaskr.auth import login_required
from flaskr.db import get_db
from flaskr import create_app
from uuid import uuid4
from flaskr.insta.follow_utility import Follower
from flaskr.insta.direct_utility import Direct
from flaskr.insta.like_utility import Like
from flaskr.insta.stories_utility import Story
from flaskr.insta.challenge_utility import Challenge
from werkzeug.exceptions import abort
from flaskr import create_app

bp = Blueprint('web_app', __name__)
prev = ''


@bp.route('/')
@login_required
def index():
    db = get_db()
    users = db.execute(
        'SELECT user_id'
        ' FROM users'
    )
    clean_users = []
    for user in users:
        clean_users.append(user[0])

    x = [clean_users[i:i + 3] for i in range(0, len(clean_users), 3)]

    return render_template('web_app/utenti.html', users=x)


@bp.route('/add_user', methods=('GET', 'POST'))
@login_required
def new_user():
    global prev
    prev = request.referrer
    if request.method == 'POST':
        user_id = request.form['user_id']
        error = None

        if not user_id:
            error = 'user_id is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO users (user_id)'
                ' VALUES (?)',
                (user_id,)
            )
            db.commit()
            return redirect(url_for('web_app.index'))

    return render_template('web_app/new_user.html', prev=prev)


@bp.route('/challenge/<string:code1>/<string:code2>/<string:username>', methods=('GET', 'POST'))
@login_required
def challenge(code1, code2, username):
    global prev
    prev = request.referrer

    if request.method == 'POST':
        redirect(url_for('web_app.account', username=username))
        code = request.form['code']
        res = 0
        db = get_db()
        password = db.execute(
            'SELECT accounts.password'
            ' FROM accounts'
            ' WHERE accounts.username = ?',
            (str(username),)
        ).fetchone()

        link = f"https://www.instagram.com/challenge/{code1}/{code2}/"

        c = Challenge(username, password, link, code)
        res = c.challenge_sign_in()
        c.close_browser()

        return render_template('web_app/account.html', account=[username, password], status=res)

    else:
        db = get_db()
        password = db.execute(
            'SELECT accounts.password'
            ' FROM accounts'
            ' WHERE accounts.username = ?',
            (str(username),)
        ).fetchone()

        link = f"https://www.instagram.com/challenge/{code1}/{code2}/"

        c = Challenge(username, password, link, '')
        c.challenge_sign_in()
        c.close_browser()

        return render_template('web_app/challenge.html')


@bp.route('/<string:user_id>/user', methods=('GET', 'POST'))
@login_required
def user(user_id):
    global prev
    prev = request.referrer
    db = get_db()

    usernames = db.execute(
        'SELECT accounts.username'
        ' FROM users INNER JOIN accounts ON users.user_id = accounts.user_id'
        ' WHERE users.user_id = ?',
        (str(user_id),)
    ).fetchall()

    clean_usernames = []
    for username in usernames:
        clean_usernames.append(username['username'])

    x = [clean_usernames[i:i + 3] for i in range(0, len(clean_usernames), 3)]

    return render_template('web_app/utente.html', data=(x, user_id), prev=prev)


@bp.route('/<string:username>/account', methods=('GET', 'POST'))
@login_required
def account(username):
    global prev
    if 'user' in request.referrer:
        prev = request.referrer

    db = get_db()
    if request.method == 'POST':
        if 'update' in request.form:
            db.execute(
                'UPDATE accounts'
                ' SET username = ?, password = ?'
                ' WHERE username = ?',
                (request.form['username'], request.form['password'], str(username),)
            ).fetchone()
            db.commit()
        else:
            db.execute(
                'DELETE FROM accounts'
                ' WHERE username = ?',
                (str(username),)
            ).fetchone()
            db.commit()
            return redirect(url_for('web_app.index'))

    account = db.execute(
        'SELECT accounts.username, accounts.password, accounts.account_id'
        ' FROM accounts'
        ' WHERE accounts.username = ?',
        (str(username),)
    ).fetchone()
    db.close()

    return render_template('web_app/account.html', account=account, prev=prev)


@bp.route('/<string:user_id>/add_account', methods=('GET', 'POST'))
@login_required
def new_account(user_id):
    global prev
    prev = request.referrer
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None

        if not username:
            error = 'user_id is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO accounts (username, password, user_id)'
                ' VALUES (?,?,?)',
                (username, password, str(user_id),)
            )
            db.commit()
            return redirect(url_for('web_app.index'))

    return render_template('web_app/new_account.html', prev=prev)


@bp.route('/<string:username>/link', methods=('GET', 'POST'))
@login_required
def link(username):
    db = get_db()
    password = db.execute(
        'SELECT accounts.password'
        ' FROM accounts'
        ' WHERE accounts.username = ?',
        (str(username),)
    ).fetchone()

    ig = InstagramBot(username, password)
    status = ig.sign_in()
    ig.close_browser()

    if len(status) != 3:
        return render_template('web_app/account.html', account=[username, password], status=status)
    else:
        return redirect(url_for('web_app.challenge', code1=status[0], code2=status[1], username=username))


@bp.route('/<string:username>/follow', methods=('GET', 'POST'))
@login_required
def follow(username):
    global prev
    db = get_db()

    city = []
    x = db.execute(
        'SELECT name'
        ' FROM city',
    ).fetchall()

    for i in x:
        city.append(i[0])

    if 'account' in request.referrer:
        prev = request.referrer

    if request.method == 'POST':
        print(request.form)
        section = request.form['section']
        hashtags_or_locations = request.form['hashtags_or_locations']
        post_number = request.form['post_number']
        follower_number = request.form['follower_number']
        following_number = request.form['following_number']
        bio = request.form['bio']
        in_username = request.form['in_username']
        profiles_number = request.form['profiles_number']

        if section == 'Hashtag':
            f = Follower(username, section, hashtags_or_locations, post_number, follower_number, following_number, bio,
                         in_username, profiles_number)
            f.login()
            f.hashtag()
            f.close_browser()
        else:
            f = Follower(username, section, hashtags_or_locations, post_number, follower_number, following_number, bio,
                         in_username, profiles_number)
            f.login()
            f.location()
            f.close_browser()

    try:
        page = request.args['page']
    except Exception:
        page = ''

    if page == '2':
        users = db.execute(
            'SELECT followed_username, timestamp'
            ' FROM followed_accounts'
            ' WHERE username = ?'
            ' ORDER BY timestamp DESC',
            (username,)
        ).fetchall()

        return render_template('web_app/follow.html', users=users, username=username, page=page, prev=prev)

    else:
        return render_template('web_app/follow.html', username=username, prev=prev, city=json.dumps(city))


@bp.route('/<string:username>/like', methods=('GET', 'POST'))
@login_required
def like(username):
    global prev
    city = []

    db = get_db()
    x = db.execute(
        'SELECT name'
        ' FROM city',
    ).fetchall()

    for i in x:
        city.append(i[0])

    if 'account' in request.referrer:
        prev = request.referrer

    if request.method == 'POST':
        print(request.form)
        section = request.form['section']
        hashtags_or_locations = request.form['hashtags_or_locations']
        post_number = request.form['post_number']
        follower_number = request.form['follower_number']
        following_number = request.form['following_number']
        bio = request.form['bio']
        in_username = request.form['in_username']
        profiles_number = request.form['profiles_number']

        if section == 'Hashtag':
            l = Like(username, section, hashtags_or_locations, post_number, follower_number, following_number, bio,
                     in_username, profiles_number)
            l.login()
            l.hashtag()
            l.close_browser()
        else:
            l = Like(username, section, hashtags_or_locations, post_number, follower_number, following_number, bio,
                     in_username, profiles_number)
            l.login()
            l.location()
            l.close_browser()

    try:
        page = request.args['page']
    except Exception:
        page = ''

    if page == '2':
        users = db.execute(
            'SELECT liked_post, timestamp'
            ' FROM liked_accounts'
            ' WHERE username = ?'
            ' ORDER BY timestamp DESC',
            (username,)
        ).fetchall()
        return render_template('web_app/like.html', users=users, username=username, page=page, prev=prev)

    else:
        return render_template('web_app/like.html', username=username, prev=prev, city=json.dumps(city))


@bp.route('/<string:username>/story', methods=('GET', 'POST'))
@login_required
def story(username):
    global prev
    city = []

    db = get_db()
    x = db.execute(
        'SELECT name'
        ' FROM city',
    ).fetchall()

    for i in x:
        city.append(i[0])

    if 'account' in request.referrer:
        prev = request.referrer
    if request.method == 'POST':
        print(request.form)
        section = request.form['section']
        hashtags_or_locations = request.form['hashtags_or_locations']
        post_number = request.form['post_number']
        follower_number = request.form['follower_number']
        following_number = request.form['following_number']
        bio = request.form['bio']
        in_username = request.form['in_username']
        profiles_number = request.form['profiles_number']

        if section == 'Hashtag':
            s = Story(username, section, hashtags_or_locations, post_number, follower_number, following_number, bio,
                      in_username, profiles_number)
            s.login()
            s.hashtag()
            s.close_browser()
        else:
            s = Story(username, section, hashtags_or_locations, post_number, follower_number, following_number, bio,
                      in_username, profiles_number)
            s.login()
            s.location()
            s.close_browser()

    try:
        page = request.args['page']
    except Exception:
        page = ''

    if page == '2':
        users = db.execute(
            'SELECT user_story, num_story_viewed, timestamp'
            ' FROM watched_story'
            ' WHERE username = ?'
            ' ORDER BY timestamp DESC',
            (username,)
        ).fetchall()
        return render_template('web_app/story.html', users=users, username=username, page=page, prev=prev)

    else:
        return render_template('web_app/story.html', username=username, prev=prev, city=json.dumps(city))


@bp.route('/<string:username>/direct', methods=('GET', 'POST'))
@login_required
def direct(username):
    global prev
    city = []

    db = get_db()
    x = db.execute(
        'SELECT name'
        ' FROM city',
    ).fetchall()

    for i in x:
        city.append(i[0])

    if 'account' in request.referrer:
        prev = request.referrer
    if request.method == 'POST':
        section = request.form['section']
        message = request.form['message']
        hashtags_or_locations = request.form['hashtags_or_locations']
        post_number = request.form['post_number']
        follower_number = request.form['follower_number']
        following_number = request.form['following_number']
        bio = request.form['bio']
        in_username = request.form['in_username']
        profiles_number = request.form['profiles_number']

        if section == 'Hashtag':
            d = Direct(username, section, hashtags_or_locations, post_number, follower_number, following_number, bio,
                       in_username, profiles_number, message)
            d.login()
            d.hashtag()
            d.close_browser()
        else:
            d = Direct(username, section, hashtags_or_locations, post_number, follower_number, following_number, bio,
                       in_username, profiles_number, message)
            d.login()
            d.location()
            d.close_browser()

    try:
        page = request.args['page']
    except Exception:
        page = ''

    if page == '2':
        users = db.execute(
            'SELECT directed_username, text, timestamp'
            ' FROM directed_accounts'
            ' WHERE username = ?'
            ' ORDER BY timestamp DESC',
            (username,)
        ).fetchall()
        return render_template('web_app/direct.html', users=users, username=username, page=page, prev=prev)

    else:
        return render_template('web_app/direct.html', username=username, prev=prev, city=json.dumps(city))


@bp.route('/<string:username>/self_publishing', methods=('GET', 'POST'))
@login_required
def self_publishing(username):
    global prev
    if 'account' in request.referrer:
        prev = request.referrer

    if request.method == 'POST':
        image = request.files['image']
        caption = request.form['caption']
        date_time = request.form['date_time']

        ext = str(image.filename).split('.')[1]
        filename = f"{uuid4().hex}.{ext}"
        image.save(os.path.join(create_app().config["IMAGE_UPLOADS"], filename))

        db = get_db()
        account_id = db.execute(
            'SELECT accounts.account_id'
            ' FROM accounts'
            ' WHERE accounts.username = ?',
            (str(username),)
        ).fetchone()

        user_id = db.execute(
            'SELECT accounts.user_id'
            ' FROM users INNER JOIN accounts'
            ' WHERE accounts.username = ?',
            (str(username),)
        ).fetchone()

        db.execute(
            'INSERT INTO post_scheduling(time_to_post,photo,caption,is_posted,account_id)'
            ' VALUES(?,?,?,?,?)',
            (str(date_time), str(filename), str(caption), 0, str(account_id['account_id']),)
        ).fetchone()

        db.commit()
        db.close()

        return redirect(url_for('web_app.programmazioni', user_id=user_id['user_id']))

    return render_template('web_app/post_scheduling.html', prev=prev)


@bp.route('/<string:user_id>/programmazioni', methods=('GET', 'POST'))
@login_required
def programmazioni(user_id):
    global prev
    if 'account' in request.referrer:
        prev = request.referrer
    db = get_db()

    accounts_and_scheduls = db.execute(
        'SELECT accounts.username, time_to_post, caption, is_posted, photo, post_id'
        ' FROM accounts INNER JOIN post_scheduling ON accounts.account_id = post_scheduling.account_id'
        ' WHERE accounts.username IN ('
        ' SELECT accounts.username'
        ' FROM users INNER JOIN accounts ON users.user_id = accounts.user_id'
        ' WHERE users.user_id = ?'
        ' )'
        ' ORDER BY post_scheduling.post_id DESC'
        , (user_id,)
    ).fetchall()

    return render_template('web_app/programmazioni.html', accounts_and_scheduls=accounts_and_scheduls, prev=prev)


@bp.route('/<string:username>/self_publishing_update/<int:post_id>', methods=('GET', 'POST'))
@login_required
def self_publishing_update(username, post_id):
    global prev
    db = get_db()
    if 'account' in request.referrer:
        prev = request.referrer

    pub = db.execute(
        'SELECT *'
        ' FROM post_scheduling'
        ' WHERE post_id = ?',
        (post_id,)
    ).fetchone()

    if request.method == 'POST':
        image = request.files['image']
        caption = request.form['caption']
        date_time = request.form['date_time']

        ext = str(image.filename).split('.')[1]
        filename = f"{uuid4().hex}.{ext}"
        image.save(os.path.join(create_app().config["IMAGE_UPLOADS"], filename))

        account_id = db.execute(
            'SELECT accounts.account_id'
            ' FROM accounts'
            ' WHERE accounts.username = ?',
            (str(username),)
        ).fetchone()

        user_id = db.execute(
            'SELECT accounts.user_id'
            ' FROM users INNER JOIN accounts'
            ' WHERE accounts.username = ?',
            (str(username),)
        ).fetchone()

        db.execute(
            'UPDATE post_scheduling'
            ' SET time_to_post = ?, photo = ?, caption = ?, is_posted = ?, account_id = ?'
            ' WHERE post_id = ?',
            (str(date_time), str(filename), str(caption), 0, str(account_id['account_id']), post_id,)
        )
        db.commit()

        return redirect(url_for('web_app.programmazioni', user_id=user_id['user_id']))

    else:
        return render_template('web_app/post_scheduling_update.html', pub=pub, prev=prev)


@bp.route('/<string:username>/self_publishing_delete/<int:post_id>', methods=('GET', 'POST'))
@login_required
def self_publishing_delete(username, post_id):
    global prev
    if 'account' in request.referrer:
        prev = request.referrer

    db = get_db()
    db.execute(
        'DELETE FROM post_scheduling'
        ' WHERE post_id = ?',
        (int(post_id),)
    )
    db.commit()

    user_id = db.execute(
        'SELECT accounts.user_id'
        ' FROM users INNER JOIN accounts'
        ' WHERE accounts.username = ?',
        (str(username),)
    ).fetchone()

    db.close()

    return redirect(url_for('web_app.programmazioni', user_id=user_id['user_id']))
