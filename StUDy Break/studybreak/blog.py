from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from studybreak.group import get_subscribed_groups, get_subscribed_members, get_subscribed_group_ids, get_groupname, get_likes
from studybreak.auth import login_required
from studybreak.db import get_db
from studybreak.notifications import new_notif, sub_user, delNotif
from studybreak.user import get_user

bp = Blueprint('blog', __name__, url_prefix='/blog')


@bp.route('/feed', methods=('POST', 'GET'))
@login_required
def index():
    db = get_db()

    comment = request.args.get('comment', None)
    pid = request.args.get('p', None)
    pixels = request.args.get('pixels', 0)

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
        new_notif(None, g.user['id'], pid, groupid, 'comment')

        return redirect(url_for('blog.index'))

    """Show all the posts, most recent first."""
    grouplist = get_subscribed_group_ids(format(int(g.user['id']), '05'))
    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username, gid'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE gid in (' + ','.join(map(str, grouplist)) + ')'''
        ' ORDER BY created DESC'
    ).fetchall()

    idlist = []
    for row in posts:
        idlist.append((row[0]))

    comments = db.execute(
        'SELECT pid, username, body, userid FROM comments WHERE pid in (' + ','.join(map(str, idlist)) + ')'''
    ).fetchall()

    glist = []
    likes_list = []
    ulikes = []
    temp = []
    for row in posts:
        glist.append(get_groupname(row[6]))
        likes_list.append(get_likes(row[0], None, "post"))

    for row in likes_list:
        for uid in row:
            temp.append(db.execute('SELECT username FROM user WHERE id = ?', (uid,)).fetchone()[0])
        ulikes.append(temp)
        temp = []

    return render_template('blog/index.html', posts=posts, active='feed', glist=glist, comments=comments, idlikes=likes_list, pixelsset=pixels, ulikes=ulikes)


def get_post(id, check_author=True):
    """Get a post and its author by id.

    Checks that the id exists and optionally that the current user is
    the author.

    :param id: id of post to get
    :param check_author: require the current user to be the author
    :return: the post with author information
    :raise 404: if a post with the given id doesn't exist
    :raise 403: if the current user isn't the author
    """
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, "Post id {0} doesn't exist.".format(id))

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    """Create a new post for the current user."""
    if request.method == 'POST':
        title = request.form['title']
        group = request.form['groups']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            gid = db.execute(
                'SELECT id FROM groups WHERE gname = ?', (group,)
            ).fetchone()
            db.execute(
                'INSERT INTO post (title, body, author_id, gid)'
                ' VALUES (?, ?, ?, ?)',
                (title, body, g.user['id'], gid[0])
            )
            db.commit()

            pid = db.execute(
                'SELECT id FROM post ORDER BY id DESC LIMIT 1'
            ).fetchone()

            sub_user(g.user['id'], pid[0])
            new_notif(title, g.user['id'], pid[0], gid[0], 'post')
            return redirect(url_for('blog.index'))

    glist = (request.args.get('g', None),)
    if glist[0] == None:
        glist = get_subscribed_groups(format(int(g.user['id']), '05'))

    return render_template('blog/create.html', glist=glist, active='feed')


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    """Update a post if the current user is the author."""
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ? WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html', post=post, active='feed')


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    """Delete a post.

    Ensures that the post exists and that the logged in user is the
    author of the post.
    """
    get_post(id)
    db = get_db()
    ulist = db.execute(
        'SELECT userid FROM notifications WHERE pid = ?', (id,)
    ).fetchall()

    for row in ulist:
        count = db.execute(
            'SELECT notifs FROM user WHERE id = ?', (row[0],)
        ).fetchone()[0]
        db.execute(
            'UPDATE user SET notifs = ? WHERE id = ?', (count-1, row[0])
        )

    db.execute(
        'DELETE FROM notifications WHERE pid = ?', (id,)
    )

    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))

@bp.route('/like')
def like():
    db = get_db()
    redir = request.args['r']
    lid = request.args['id']
    gid = request.args['gid']
    gname = request.args.get('gname', None)
    pid = request.args.get('pid', None)
    ltype = request.args['type']
    if ltype == "post":
        db.execute(
            'INSERT INTO likes (userid, pid) VALUES (?,?)', (g.user['id'], lid)
        )

        author = db.execute(
            'SELECT author_id FROM post WHERE id = ?', (lid,)
        ).fetchone()[0]

        if author is not g.user['id']:
            new_notif(None, g.user['id'], lid, gid, "like")

    elif ltype == "comment":
        db.execute(
            'INSERT INTO likes (userid, cid) VALUES (?,?)', (g.user['id'], lid)
        )        
    db.commit()

    if redir == '1':
        return redirect(url_for('blog.index'))
    elif redir == '2':
        return redirect(url_for('groups.load_post', p=pid, gname=gname))
    elif redir == '3':
        return redirect(url_for('groups.load_group', gname=gname))

@bp.route('/unlike')
def unlike():
    db = get_db()
    redir = request.args['r']
    gname = request.args.get('gname', None)
    pid = request.args.get('pid', None)
    pixels = request.args.get('pixels', 0)
    lid = request.args['id']
    ltype = request.args['type']
    if ltype == "post":
        db.execute(
            'DELETE FROM likes WHERE (userid, pid) = (?, ?)', (g.user['id'], lid)
        )
    elif ltype == "comment":
        db.execute(
            'DELETE FROM likes WHERE (userid, cid) = (?, ?)', (g.user['id'], lid)
        )        
    db.commit()

    if redir == '1':
        return redirect(url_for('blog.index', pixels=pixels))
    elif redir == '2':
        return redirect(url_for('groups.load_post', p=pid, gname=gname))
    elif redir == '3':
        return redirect(url_for('groups.load_group', gname=gname))