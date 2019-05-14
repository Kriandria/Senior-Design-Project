from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from studybreak.auth import login_required
from studybreak.db import get_db

bp = Blueprint('pm', __name__, url_prefix='/pm')

def send(convid, body):
    db = get_db()
    db.execute(
        'INSERT INTO messages (userid, convid, body) VALUES (?,?,?)', (g.user['id'], convid, body)
    )
    db.execute(
        'UPDATE conv SET edited = CURRENT_TIMESTAMP WHERE id = ?', (convid,)
    )
    db.commit()

@login_required
@bp.route('/conv', methods=('POST', 'GET'))
def getConv():
    convid = request.args.get('id', None)
    mess = request.args.get('mess', None)
    db = get_db()
    
    if mess is not None:
        send(convid, mess)
        return redirect(url_for('pm.getConv', id=convid))

    conversation = db.execute(
        'SELECT id, userid, body, created FROM messages WHERE convid = ?',(convid,)
    ).fetchall()

    members = db.execute(
        'SELECT user1, user2 FROM conv WHERE id = ?',(convid,)
    ).fetchone()

    memnames = []
    name = db.execute('SELECT fname, lname FROM user WHERE id = ?', (members[0],)).fetchone()
    memnames.append(name[0] + ' ' + name[1])
    name = db.execute('SELECT fname, lname FROM user WHERE id = ?', (members[1],)).fetchone()
    memnames.append(name[0] + ' ' + name[1])


    return render_template('pm/message.html', conv=conversation, members=members, membername=memnames, active='messages', convid=convid)

@bp.route('/convs')
def getConvs():
    db = get_db()
    all_relevant_ids = db.execute(
        'SELECT id, user1, user2 FROM conv WHERE user1 = ? or user2 = ? ORDER BY id',(g.user['id'], g.user['id'])
    ).fetchall()

    convid = []
    uidlist = []
    for row in all_relevant_ids:
        convid.append(row[0])
        if row[1] is not g.user['id']:
            uidlist.append(row[1])
        else:
            uidlist.append(row[2])
    
    namelist = []
    for uid in uidlist:
        namelist.append(db.execute(
            'SELECT fname, lname FROM user'
            ' WHERE id = ?',(uid,)
        ).fetchone())

    return render_template('pm/messages.html', convid=convid, namelist=namelist, active='messages')

@bp.route('/try')
def tryConv():
    uid = request.args.get('id', None)

    db = get_db()
    user1 = db.execute(
        'SELECT id FROM conv WHERE user1 = ? and user2 = ?',(uid, g.user['id'])
    ).fetchone()

    user2 = db.execute(
        'SELECT id FROM conv WHERE user2 = ? and user1 = ?',(uid, g.user['id'])
    ).fetchone()

    if user1 is not None:
        return redirect(url_for('pm.getConv', id=user1[0]))
    elif user2 is not None:
        return redirect(url_for('pm.getConv', id=user2[0]))
    else:
        db.execute(
            'INSERT INTO conv (user1, user2) VALUES (?, ?)', (g.user['id'], uid)
        )
        db.commit()
        convid = db.execute(
            'SELECT id FROM conv ORDER BY id DESC'
        ).fetchone()[0]

        return redirect(url_for('pm.getConv', id=convid))
