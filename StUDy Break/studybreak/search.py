import unicodedata
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

def normalize_caseless(text):
    return unicodedata.normalize("NFKD", text.casefold())

from studybreak.db import get_db

bp = Blueprint('search', __name__, url_prefix='/search')

@bp.route('/search', methods=('GET', 'POST'))
def search():
    searchtext = request.args.get('s', None)

    group_list = []
    db = get_db()
    array = db.execute('SELECT gname FROM groups ORDER BY gname').fetchall()
    for row in array:
        if searchtext in normalize_caseless(row[0]):
            group_list.append(row[0])

    username_list = []
    name_list = []
    uid = []
    nid = []
    array = db.execute('SELECT fname, lname, id FROM user ORDER BY lname').fetchall()
    for row in array:
        name = row[0]+' '+row[1]
        if searchtext in normalize_caseless(name):
            name_list.append(name)
            nid.append(row[2])

    array = db.execute('SELECT username, id FROM user ORDER BY username').fetchall()
    for row in array:
        if searchtext in normalize_caseless(row[0]):
            username_list.append(row[0])
            uid.append(row[1])


    return render_template('search/search.html', s=searchtext, glist=group_list, nlist=name_list, ulist=username_list, uids=uid, nids=nid)