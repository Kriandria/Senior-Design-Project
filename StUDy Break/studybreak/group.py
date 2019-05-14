from studybreak.db import get_db
from flask import Blueprint, render_template, request, g, flash, session, redirect, url_for

bp = Blueprint('groups', __name__, url_prefix='/groups')

def create_group(gname):
    admin = request.args.get('a', None)
    db = get_db()
    if db.execute(
        'SELECT id FROM groups WHERE gname = ?', (gname,)
    ).fetchone() is None:
        db.execute(
            'INSERT INTO groups (gname, administrators) VALUES (?, ?)', (gname, admin)
        )
        db.commit()

def subscribe_user(gname, uid):
    found = 0
    members = []
    db = get_db()
    mem = db.execute(
        'SELECT members FROM groups WHERE gname = ?', (gname,)
    ).fetchone()

    if mem[0] is not None:
        members = mem[0].split(',')
        for user_id in members:
            if uid == user_id:
                found = 1
                break
    
    if not(found):
        members.append(str(uid))
        newstring = ','.join(members)
        db.execute(
            'UPDATE groups SET members = (?) WHERE gname = ?', (newstring, gname)
        )
        db.commit()

def unsubscribe_user(gname, uid):
    found = 0
    members = []
    newmem = []
    db = get_db()
    mem = db.execute(
        'SELECT members FROM groups WHERE gname = ?', (gname,)
    ).fetchone()

    if mem[0] is not None:
        members = mem[0].split(',')
        for user_id in members:
            if uid != user_id:
                newmem.append(user_id)
        newstring = ','.join(newmem)
        db.execute(
            'UPDATE groups SET members = (?) WHERE gname = ?', (newstring, gname)
        )
        db.commit()

def get_groupname(gid):
    db = get_db()
    return db.execute('SELECT gname FROM groups WHERE id = ?', (gid,)).fetchone()[0]

def get_subscribed_groups(uid):
    group_list = []
    db = get_db()
    garray = db.execute('SELECT * FROM groups WHERE members IS NOT NULL ORDER BY gname').fetchall()

    for row in garray:
        if str(uid) in row[2]:
            group_list.append(row[1])
    return group_list

def get_subscribed_group_ids(uid):
    group_list = []
    db = get_db()
    garray = db.execute('SELECT * FROM groups WHERE members IS NOT NULL ORDER BY gname').fetchall()

    for row in garray:
        if uid in row[2]:
            group_list.append(row[0])
    return group_list

def get_subscribed_members(gname):
    member_list = []
    id_list = []
    members = []
    db = get_db()
    marray = db.execute('SELECT members FROM groups WHERE gname = ?', (gname,)).fetchone()

    if marray[0] is not None:
        members = marray[0].split(',')
        for user_id in members:
            member = db.execute('SELECT fname, lname FROM user WHERE id = ?', (user_id,)).fetchone()
            if member is not None:
                name = member[0] + ' ' + member[1]
                member_list.append(name)
                id_list.append(user_id)

    return member_list, id_list

@bp.route('/group', methods=('GET', 'POST'))
def load_group():
    db = get_db()

    comment = request.args.get('comment', None)
    pid = request.args.get('p', None)
    gname = request.args.get('gname', None)
    ids_a, usern_a = get_admins(gname)

    if comment is not None:
        db.execute(
            'INSERT INTO comments (userid, username, pid, body) VALUES (?, ?, ?, ?)', (g.user['id'], g.user['username'], pid, comment)
        )
        groupid = db.execute(
            'SELECT gid FROM post WHERE id = ?',(pid,)
        ).fetchone()[0]

        creatorid = db.execute(
            'SELECT author_id FROM post WHERE id = ?',(pid,)
        ).fetchone()[0]
        db.commit()

        sub_user(g.user['id'], pid)
        new_notif(None, creatorid, pid, groupid, 'comment')

        return redirect(url_for('groups.load_group', gname=gname))

    gid = db.execute(
        'SELECT id FROM groups WHERE gname = ?', (gname,)
    ).fetchone()

    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username, gid'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE gid = ?'
        ' ORDER BY created DESC', (gid[0],)
    ).fetchall()

    idlist = []
    for row in posts:
        idlist.append((row[0]))

    comments = db.execute(
        'SELECT pid, username, body, userid FROM comments WHERE pid in (' + ','.join(map(str, idlist)) + ')'''
    ).fetchall()

    likes_list = []
    ulikes = []
    temp = []
    for row in posts:
        likes_list.append(get_likes(row[0], None, "post"))

    for row in likes_list:
        for uid in row:
            temp.append(db.execute('SELECT username FROM user WHERE id = ?', (uid,)).fetchone()[0])
        ulikes.append(temp)
        temp = []

    uid = session.get('user_id')
    subg = get_subscribed_groups(uid)

    nonadmins = []
    placeholder = '?'
    placeholders = ','.join([placeholder] * len(ids_a))
    query = 'SELECT id, username, fname, lname FROM user WHERE id NOT IN (%s)' % placeholders
    nonadmins = db.execute(query, ids_a).fetchall()

    members, ids = get_subscribed_members(gname)
    return render_template('groups/group.html', gname=gname, members=members, ids = ids, active="groups", posts=posts,
        subg=subg, comments=comments, ulikes=ulikes, idlikes=likes_list, ids_a=ids_a, usern_a=usern_a, nonadmins=nonadmins)

@bp.route('/groups', methods=('GET', 'POST'))
def load_groups():
    user_id = session.get('user_id')
    g.grouplist = get_subscribed_groups(format(int(user_id), '05'))
    return render_template('groups/groups.html', active="groups")

@bp.route('/post', methods=('GET', 'POST'))
def load_post():
    db = get_db()

    comment = request.args.get('comment', None)
    pid = request.args.get('p', None)
    gname = request.args['gname']

    if comment is not None:
        db.execute(
            'INSERT INTO comments (userid, username, pid, body) VALUES (?, ?, ?, ?)', (g.user['id'], g.user['username'], pid, comment)
        )
        groupid = db.execute(
            'SELECT gid FROM post WHERE id = ?',(pid,)
        ).fetchone()[0]

        creatorid = db.execute(
            'SELECT author_id FROM post WHERE id = ?',(pid,)
        ).fetchone()[0]
        db.commit()

        return redirect(url_for('group.load_post', p=pid, gname=gname))

    post = db.execute(
        'SELECT p.id, title, body, gid, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?', (pid,)
    ).fetchone()

    gid = db.execute(
        'SELECT id FROM groups WHERE gname = ?', (gname,)
    ).fetchone()

    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username, gid'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE gid = ?'
        ' ORDER BY created DESC', (gid[0],)
    ).fetchall()

    idlist = []
    likes_list = []
    ulikes = []
    temp = []
    li = []
    lu = []
    for row in posts:
        idlist.append((row[0]))
        likes_list.append(get_likes(row[0], None, "post"))
        if row[0] == post['id']:
            li.append(get_likes(row[0], None, "post"))

    for row in likes_list:
        for uid in row:
            temp.append(db.execute('SELECT username FROM user WHERE id = ?', (uid,)).fetchone()[0])
        ulikes.append(temp)
        temp = []

    for row in li:
        for uid in row:
            temp.append(db.execute('SELECT username FROM user WHERE id = ?', (uid,)).fetchone()[0])
        lu.append(temp)
        temp = []

    comments = db.execute(
        'SELECT pid, username, body, userid FROM comments WHERE pid in (' + ','.join(map(str, idlist)) + ')'''
    ).fetchall()

    members, ids = get_subscribed_members(gname)
    return render_template('groups/post.html', gname=gname, members=members, ids = ids, active="groups", posts=posts, p=post, comments=comments, idlikes=likes_list, ulikes=ulikes, li=li, lu=lu, pid=pid)

@bp.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        name = request.form['name'].title()
        univ = request.form['colleges']
        gname = univ+'-'+name
        db = get_db()
        error = None

        if not name:
            error = "Group name is required."
        elif not univ:
            error = 'School name is required.'
        elif db.execute(
            'SELECT id FROM colleges WHERE cname = ?', (univ,)
        ).fetchone() is None:
            error = 'School name \'{0}\' is invalid. Select a school from the drop-down list.'.format(univ)
        elif db.execute(
            'SELECT id FROM groups WHERE gname = ?', (gname,)
        ).fetchone() is not None:
            error = 'Group {0} is already registered.'.format(gname)
        
        if error is None:
            uid = session.get('user_id')

            create_group(gname)
            subscribe_user(gname, uid)
            db.commit()

            return redirect(url_for('groups.load_group', gname=gname))

    college_list = []
    db = get_db()
    clist = db.execute('SELECT cname FROM colleges').fetchall()
    
    for row in clist:
        college_list.append(row[0])

    return render_template('groups/create.html', college_list=college_list, active="groups")

@bp.route('/subscribe')
def subscribe():
    gname = request.args.get('g', None)
    subscribe_user(gname, session.get('user_id'))
    return redirect(url_for('groups.load_group', gname=gname))

@bp.route('/unsubscribe')
def unsubscribe():
    gname = request.args.get('g', None)
    unsubscribe_user(gname, session.get('user_id'))
    remove_admin(gname)
    return redirect(url_for('groups.load_group', gname=gname))

def get_likes(pid, cid, t):
    db = get_db()
    idlikes = []

    if t == "post":
        likes_list = db.execute(
            'SELECT userid FROM likes WHERE pid = ?', (pid,)
        ).fetchall()

        for row in likes_list:
            idlikes.append(row[0])

    return idlikes

def get_admins(gname):
    usern_a = []
    ids_a = []

    db = get_db()
    aarray = db.execute('SELECT administrators FROM groups WHERE gname = ?', (gname,)).fetchone()

    if aarray is not None:
        try:
            admins = aarray[0].split(',')
        except:
            admins = []
        for user_id in admins:
            admin = db.execute('SELECT username FROM user WHERE id = ?', (user_id,)).fetchone()
            if admin is not None:
                usern_a.append(admin)
                ids_a.append(int(user_id))

    return ids_a, usern_a

def remove_admin(gname):
    db = get_db()

    aarray = db.execute('SELECT administrators FROM groups WHERE gname = ?', (gname,)).fetchone()[0]
    if aarray is not None:
        try:
            admins = aarray.split(',')
        except:
            admins = []

    if str(g.user['id']) in admins:
        admins.remove(str(g.user['id']))

    admins = ','.join(admins)

    db.execute(
        'UPDATE groups SET administrators = ? WHERE gname = ?', (admins, gname)
    )

    db.commit()
    return redirect(url_for('groups.load_group', gname=gname))

@bp.route('/subadmin', methods=('GET','POST'))
def register_admin():
    db = get_db()
    if request.method == 'POST':
        gname = request.args.get('g', "")
        uid = request.form['newAdmin']

        aarray = db.execute('SELECT administrators FROM groups WHERE gname = ?', (gname,)).fetchone()[0]
        if aarray is not None:
            try:
                admins = aarray.split(',')
            except:
                admins = []

        if uid not in admins:        
            admins.append(uid)
            admins = ','.join(admins)

            db.execute(
                'UPDATE groups SET administrators = ? WHERE gname = ?', (admins, gname)
            )
            db.commit()
    return redirect(url_for('groups.load_group', gname=gname))

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