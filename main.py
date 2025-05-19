# Open source anti-furry forums code made by Andreiplsno
# *idk why i made this open source*

import flask
import sqlite3

App = flask.Flask(__name__,static_url_path="/static")

@App.route("/")
def LandingPage():
    return open("pages/landing.html").read()

App.run(port=80)