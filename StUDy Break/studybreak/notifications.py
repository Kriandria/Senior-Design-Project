from studybreak.db import get_db
from studybreak.auth import login_required
from studybreak.group import get_subscribed_members, get_groupname
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)

bp = Blueprint('notif', __name__, url_prefix='/notif')

def new_notif(title, uid, pid, gid, ntype):
    db = get_db()

    if ntype == 'post':
        gname = get_groupname(gid)
        members, ids = get_subscribed_members(gname)
        creator = g.user['username']
        message = "New post with subject \"{t}\" in {g} by {u}.".format(t=title, g=gname, u=creator)

        for n in ids:
            if int(n) != int(uid):
                db.execute(
                    'INSERT INTO notifications (userid, body, pid, gid) VALUES (?,?,?,?)', (n, message, pid, gid)
                )

                notif_c = db.execute(
                    'SELECT notifs FROM user WHERE id = ?', (n,)
                ).fetchone()

                count = notif_c[0] + 1
                db.execute(
                    'UPDATE user SET notifs = (?) WHERE id = ?', (count, n)
                )
        db.commit()

    elif ntype == 'like':
        gname = get_groupname(gid)
        cuname = db.execute(
        'SELECT username FROM user WHERE id = ?', (uid,)
        ).fetchone()
        message = "New like from {u} on a post in {g}.".format(g=gname, u=cuname[0])

        notif = db.execute(
            'SELECT * FROM notifications WHERE (pid, body) = (?, ?)', (pid, message)
        ).fetchone()

        if notif is None:
            creator = db.execute(
                'SELECT author_id FROM post WHERE id = ?', (pid,)
            ).fetchone()[0]

            db.execute(
                'INSERT INTO notifications (userid, body, pid, gid) VALUES (?,?,?,?)', (creator, message, pid, gid)
            )

            notif_c = db.execute(
                'SELECT notifs FROM user WHERE id = ?', (creator,)
            ).fetchone()

            count = notif_c[0] + 1
            db.execute(
                'UPDATE user SET notifs = (?) WHERE id = ?', (count, creator)
            )
            db.commit()

    elif ntype == "comment":
        gname = get_groupname(gid)
        ulist = get_subscribed_users(pid)
        cuname = db.execute(
        'SELECT username FROM user WHERE id = ?', (uid,)
        ).fetchone()
        message = "New comment by {u} on a post in {g}.".format(g=gname, u=cuname[0])

        for n in ulist:
            if int(n) != int(uid):
                db.execute(
                    'INSERT INTO notifications (userid, body, pid, gid) VALUES (?,?,?,?)', (n, message, pid, gid)
                )

                notif_c = db.execute(
                    'SELECT notifs FROM user WHERE id = ?', (n,)
                ).fetchone()

                count = notif_c[0] + 1
                db.execute(
                    'UPDATE user SET notifs = (?) WHERE id = ?', (count, n)
                )
        db.commit()


@bp.route('/')
@login_required
def index():
    """Show all the posts, most recent first."""
    userid = session.get('user_id')
    db = get_db()
    notifs = db.execute(
        'SELECT read, pid, gid, created, body, id FROM notifications'
        ' WHERE userid = ?'
        ' ORDER BY created DESC', (userid,)
    ).fetchall()

    glist = []
    for row in notifs:
        glist.append(get_groupname(row[2]))

    return render_template('notifications/notifications.html', notifications=notifs, glist=glist, active='notif')

@bp.route('/read')
def mark_read():
    nid = request.args.get('id', None)
    read(nid)
    return redirect(url_for('notif.index'))

@bp.route('/unread')
def mark_unread():
    nid = request.args.get('id', None)

    db = get_db()

    db.execute(
        'UPDATE user SET notifs = (?) WHERE id = ?', (g.user['notifs'] + 1, g.user['id'])
    )
    db.execute(
        'UPDATE notifications SET read = (?) WHERE id = ?', (0, nid)
    )
    db.commit()
    return redirect(url_for('notif.index'))

def read(nid):
    db = get_db()

    notifs = db.execute(
        'SELECT notifs FROM user WHERE id = ?', (g.user['id'],)
    ).fetchone()[0]

    db.execute(
        'UPDATE user SET notifs = (?) WHERE id = ?', (notifs-1, g.user['id'])
    )

    db.execute(
        'UPDATE notifications SET read = (?) WHERE id = ?', (1, nid)
    )
    db.commit()

@bp.route('/movingRead')
def movingRead():
    nid = request.args['n']
    pid = request.args['p']
    gname = request.args['gname']

    db = get_db()
    if db.execute(
        'SELECT read FROM notifications WHERE id = ?', (nid,)
    ).fetchone()[0] == 0:
        read(nid)

    return redirect(url_for('groups.load_post', p=pid, gname=gname))

@bp.route('/markAll')
def mark_all_read():
    db = get_db()
    notifs = db.execute(
        'SELECT read, id FROM notifications WHERE userid = ?', (g.user['id'],)
    ).fetchall()

    for row in notifs:
        if row[0] == 0:
            read(row[1])

    return redirect(url_for('notif.index'))

def delete(nid):
    db = get_db()
    db.execute(
        'DELETE FROM notifications WHERE id = ?', (nid,)
    )
    db.commit()

@bp.route('/delete')
def delNotif():
    db = get_db()
    nid = request.args.get('id')
    notif = db.execute(
        'SELECT read FROM notifications WHERE id = ?', (nid,)
    ).fetchone()[0]
    if notif == 0:
        read(nid)
    delete(nid)
    return redirect(url_for('notif.index'))

@bp.route('/delAll')
def delAll():
    mark_all_read()
    db = get_db()
    notifs = db.execute(
        'SELECT id FROM notifications WHERE userid = ?', (g.user['id'],)
    ).fetchall()

    for row in notifs:
        delete(row[0])
    return redirect(url_for('notif.index'))

def sub_user(uid, pid):
    db = get_db()
    found = 0
    members = []
    ulist = db.execute(
        'SELECT subbed_users FROM post WHERE id = ?',(pid,)
    ).fetchone()[0]

    if ulist is not None:
        members = ulist.split(',')
        for user_id in members:
            if int(uid) == int(user_id):
                found = 1
                break
    
    if not(found):
        members.append(str(uid))
        newstring = ','.join(members)
        db.execute(
            'UPDATE post SET subbed_users = (?) WHERE id = ?', (newstring, pid)
        )
        db.commit()

def get_subscribed_users(pid):
    member_list = []
    id_list = []
    members = []
    db = get_db()
    marray = db.execute('SELECT subbed_users FROM post WHERE id = ?', (pid,)).fetchone()[0]

    id_list = []

    if marray is not None:
        members = marray.split(',')
        for user_id in members:
            id_list.append(user_id)

    return id_list