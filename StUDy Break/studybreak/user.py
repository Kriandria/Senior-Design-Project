from studybreak.db import get_db
from flask import Blueprint, render_template, request, g, flash, session, redirect, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from studybreak.auth import login_required
from studybreak.group import unsubscribe_user, get_subscribed_groups, create_group, subscribe_user
from studybreak.notifications import delAll, mark_all_read, delete

bp = Blueprint('profile', __name__, url_prefix='/profile')

def get_user(uid):
    db = get_db()
    user = db.execute(
        'SELECT id, username, fname, lname, school, gradyear, major, email FROM user WHERE id = ?', (uid,)
    ).fetchone()
    return user

@bp.route('/user', methods=('GET', 'POST'))
@login_required
def profile():
    user = get_user(request.args.get('id', None))
    return render_template('profile/user.html', user=user, active="profile")

@bp.route('/edit', methods=('GET', 'POST'))
@login_required
def edit():
    if request.method=='POST':
        username = request.form['username']
        fname = request.form['fname'].capitalize()
        lname = request.form['lname'].capitalize()
        gyear = request.form['gyear']
        major = request.form['major'].title()
        univ = request.form['colleges']
        email = request.form['email']
        db = get_db()
        error = None
        change = 0

        if gyear != g.user['gradyear']:
            uid = db.execute('SELECT substr(\'00000\' || id, -5, 5) FROM user WHERE username = ?', (username,)
            ).fetchone()[0]

            gname = univ + '-' + major + " Class of " + gyear
            create_group(gname)
            subscribe_user(gname, uid)
            change = 2

        if univ != g.user['school']:
            uid = db.execute('SELECT substr(\'00000\' || id, -5, 5) FROM user WHERE username = ?', (username,)
            ).fetchone()[0]

            gname = univ + '-' + major
            create_group(gname)
            subscribe_user(gname, uid)

            gname = univ + '-' + major + " Class of " + gyear
            create_group(gname)
            subscribe_user(gname, uid)
            change = 1

        if major != g.user['major']:
            uid = db.execute('SELECT substr(\'00000\' || id, -5, 5) FROM user WHERE username = ?', (username,)
            ).fetchone()[0]

            gname = univ + '-' + major
            create_group(gname)
            subscribe_user(gname, uid)

            gname = univ + '-' + major + " Class of " + gyear
            create_group(gname)
            subscribe_user(gname, uid)
            change = 3 

        name = db.execute(
            'SELECT id FROM user WHERE username = ?',(username,)
        ).fetchone()

        if name is not None and name[0] is not g.user['id']:
            error = "Username is unavailable."
        elif '@' not in email or '.' not in email:
            error = "Please enter a valid email address."
        elif db.execute(
            'SELECT id FROM colleges WHERE cname = ?',(univ,)
        ).fetchone() is None:
            error = 'School name \'{0}\' is invalid. Select a school from the drop-down list.'.format(univ)

        if error is None:
            # the name is available, store it in the database and go to
            # the login page
            db.execute(
                'UPDATE user SET (username, fname, lname, \
                school, gradyear, major, email) = (?, ?, ?, ?, ?, ?, ?) WHERE id = ?',
                (username, fname, lname, univ, gyear, major, email, g.user['id'])
            )

            if db.execute(
                'SELECT id FROM majors WHERE major = ?', (major,)
            ).fetchone() is None:
                db.execute(
                    'INSERT INTO majors (major) VALUES (?)', (major,)
                )

            db.commit()

            if change == 1:
                flash('You have been subscribed to your new school\'s primary groups.')
            elif change == 2:
                flash('You have been subscribed to {}.'.format(gname))
            elif change == 3:
                flash('you have been subscribed to your new major\'s primary groups at {}.'.format(univ))

            return redirect(url_for('profile.profile', id=g.user['id']))

        flash (error)

    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT cname FROM colleges')
    
    college_list = []
    for row in cursor.fetchall():
        college_list.append(row[0])

    major_list = []
    cursor.execute('SELECT major FROM majors')

    for row in cursor.fetchall():
        major_list.append(row[0])

    return render_template('profile/edit.html', clist=college_list, mlist=major_list)

@bp.route('/delAccount')
def deleteAccount():
    db = get_db()

    delAll()

    glist = get_subscribed_groups(g.user['id'])
    for group in glist:
        unsubscribe_user(group, g.user['id'])

    postids = db.execute(
        'SELECT id FROM post WHERE author_id = ?', (g.user['id'],)
    ).fetchall()
    for row in postids:
        db.execute(
            'DELETE FROM notifications WHERE pid = ?', (row[0],)
        )
        db.execute(
            'DELETE FROM post WHERE id = ?', (row[0],)
        )

    db.execute(
        'DELETE FROM user WHERE id = ?', (g.user['id'],)
    )
    db.commit()
    session.clear()
    return redirect(url_for('auth.login'))

@bp.route('/change_pass', methods=('GET', 'POST'))
def change_pass():
    error = None
    if request.method=='POST':
        old = request.form['old']
        new = request.form['new']
        new2 = request.form['new2']

        if not check_password_hash(g.user['password'], old):
            error = "Incorrect Password."
        elif new != new2:
            error = "Passwords do not match."
        elif not (any(x.isupper() for x in new) and any(x.islower() for x in new) 
    and any(x.isdigit() for x in new) and len(new) >= 7):
            error = "Password does not meet specified criteria."

        if error == None:
            flash("Password Successfully Updated.")
            db = get_db()
            db.execute(
                'UPDATE user SET (password) = ? WHERE id = ?',(generate_password_hash(new), g.user['id'])
            )
            db.commit()
            return redirect(url_for('profile.profile', id=g.user['id']))
            
        flash(error)
    return render_template('profile/pass.html')
