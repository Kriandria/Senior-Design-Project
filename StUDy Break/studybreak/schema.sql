-- Initialize the database.
-- Drop any existing data and create empty tables.

DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS colleges;
DROP TABLE IF EXISTS majors;
DROP TABLE IF EXISTS groups;
DROP TABLE IF EXISTS post;
DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS old_notifications;
DROP TABLE IF EXISTS likes;
DROP TABLE IF EXISTS comments;
DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS conv;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  fname TEXT NOT NULL,
  lname TEXT NOT NULL,
  school TEXT NOT NULL,
  gradyear INTEGER NOT NULL,
  major TEXT NOT NULL,
  email TEXT NOT NULL,
  notifs INTEGER DEFAULT 0
);

CREATE TABLE colleges (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  cname TEXT NOT NULL
);

CREATE TABLE majors (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  major TEXT NOT NULL
);

CREATE TABLE groups (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  gname TEXT NOT NULL,
  members TEXT,
  administrators TEXT
);

CREATE TABLE post (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  gid INTEGER NOT NULL,
  subbed_users TEXT,
  FOREIGN KEY (author_id) REFERENCES user (id)
);

CREATE TABLE notifications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  userid INTEGER NOT NULL,
  pid INTEGER,
  gid INTEGER,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  body TEXT NOT NULL,
  read INTEGER DEFAULT 0
);

CREATE TABLE old_notifications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  userid INTEGER NOT NULL,
  pid INTEGER,
  gid INTEGER,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  body TEXT NOT NULL,
  read INTEGER DEFAULT 0
);

CREATE TABLE comments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  userid INTEGER NOT NULL,
  username TEXT NOT NULL,
  pid INTEGER NOT NULL,
  body TEXT,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE likes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  userid INTEGER NOT NULL,
  pid INTEGER,
  cid INTEGER
);

CREATE TABLE messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  userid INTEGER NOT NULL,
  convid INTEGER NOT NULL,
  body TEXT NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE conv (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  users TEXT,
  user1 INTEGER,
  user2 INTEGER,
  edited TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);