import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from studybreak.db import get_db
from studybreak.group import create_group, subscribe_user, get_subscribed_groups, get_subscribed_members, load_group

bp = Blueprint('auth', __name__, url_prefix='/auth')

def login_required(view):
    """View decorator that redirects anonymous users to the login page."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view


@bp.before_app_request
def load_logged_in_user():
    """If a user id is stored in the session, load the user object from
    the database into ``g.user``."""
    user_id = session.get('user_id')
    g.memberlist = []

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()
    
        g.grouplist = get_subscribed_groups(format(int(user_id), '05'))

        try:
            g.memberlist = get_subscribed_members(g.grouplist[0])
        except:
            print()

@bp.route('/register', methods=('GET', 'POST'))
def register():
    """Register a new user.

    Validates that the username is not already taken. Hashes the
    password for security.
    """
    college_list = []
    major_list = []
    username = request.args.get('username', "")
    fname = request.args.get('fname', "").capitalize()
    lname = request.args.get('lname', "").capitalize()
    gyear = request.args.get('gyear', "")
    major = request.args.get('major', "").title()
    univ = request.args.get('colleges', "")
    email = request.args.get('email', "")
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password2 = request.form['password2']
        fname = request.form['fname'].capitalize()
        lname = request.form['lname'].capitalize()
        gyear = request.form['gyear']
        major = request.form['major'].title()
        univ = request.form['colleges']
        email = request.form['email']
        db = get_db()
        error = None

        if not email:
            error = 'Email is required.'
        elif '@' not in email or '.' not in email:
            error = "Please enter a valid email address."
            email = ""
        elif not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif not (any(x.isupper() for x in password) and any(x.islower() for x in password) 
    and any(x.isdigit() for x in password) and len(password) >= 7):
            error = "Password does not meet specified criteria."
        elif password != password2:
            error = 'Passwords do not match.'
        if not fname:
            error = 'First name is required.'
        elif not lname:
            error = 'Last name is required.'
        if not univ:
            error = 'School name is required.'
        elif not gyear:
            error = 'Graduation year is required.'
        elif not major:
            error = 'Major is required.'
        elif db.execute(
            'SELECT id FROM colleges WHERE cname = ?', (univ,)
        ).fetchone() is None:
            error = 'School name \'{0}\' is invalid. Select a school from the drop-down list.'.format(univ)
            univ = ""
        elif db.execute(
            'SELECT id FROM user WHERE username = ?', (username,)
        ).fetchone() is not None:
            error = 'User {0} is already registered. Please select a different username.'.format(username)
            username = ""

        if error is None:
            # the name is available, store it in the database and go to
            # the login page
            db.execute(
                'INSERT INTO user (username, password, fname, lname, \
                school, gradyear, major, email) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                (username, generate_password_hash(password), fname, lname, \
                univ, gyear, major, email)
            )

            if db.execute(
                'SELECT id FROM majors WHERE major = ?', (major,)
            ).fetchone() is None:
                db.execute(
                    'INSERT INTO majors (major) VALUES (?)', (major,)
                )

            uidlist = db.execute('SELECT substr(\'00000\' || id, -5, 5) FROM user WHERE username = ?', (username,)
            ).fetchone()

            uid = uidlist[0]

            gname = univ + '-' + major
            create_group(gname)
            subscribe_user(gname, uid)

            gname = univ + '-' + major + " Class of " + gyear
            create_group(gname)
            subscribe_user(gname, uid)            

            db.commit()
            session.clear()
            return redirect(url_for('auth.login'))

        flash(error)
        
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT cname FROM colleges')
    
    for row in cursor.fetchall():
        college_list.append(row[0])

    cursor.execute('SELECT major FROM majors')

    for row in cursor.fetchall():
        major_list.append(row[0])

    return render_template('auth/register.html', college_list=college_list, major_list=major_list, active="register", fname=fname, lname=lname, colleges=univ, major=major, gyear=gyear, uname=username, email=email)


@bp.route('/login', methods=('GET', 'POST'))
def login():
    """Log in a registered user by adding the user id to the session."""
    username = request.args.get('username', "")
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            # store the user id in a new session and return to the index
            session.clear()
            session['user_id'] = format(int(user['id']), '05')
            return redirect(url_for('index'))

        flash(error)

    return render_template('auth/login.html', active="login", username=username)


@bp.route('/logout')
def logout():
    """Clear the current session, including the stored user id."""
    session.clear()
    return redirect(url_for('index'))

@bp.route('/group', methods=('GET', 'POST'))
def show_group_info():
    gname = request.args.get('type', None)
    return redirect(url_for('groups.load_group', gname=gname))

@bp.route('/search', methods=('GET', 'POST'))
def search():
    if request.method == 'POST':
        searchtext = request.form['search']
        return redirect(url_for('search.search', s=searchtext))

def create_group_post():
    if request.method == 'POST':
        gname = request.args.get('g', None)
        return redirect(url_for('blog.create', g=gname))