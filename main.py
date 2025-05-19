# Open source anti-furry forums code made by Andreiplsno
# *idk why i made this open source*

import flask
import sqlite3

from flask import request,jsonify

conn = sqlite3.connect("forum.db")

conn.execute("""CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(100) NOT NULL,
    display_name VARCHAR(150) NOT NULL,
    bio TEXT,
    encrypted_password TEXT NOT NULL,
    admin TINYINT(1) NOT NULL DEFAULT 0,
    token TEXT NOT NULL
);""")

conn.execute("""CREATE TABLE IF NOT EXISTS ip (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usr_id INTEGER NOT NULL,
    ip TEXT NOT NULL
);""")

conn.commit()
conn.close()

App = flask.Flask(__name__,static_url_path="/static")

@App.route("/")
def LandingPage():
    return open("pages/landing.html").read()

App.run(port=80)