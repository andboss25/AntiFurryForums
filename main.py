# Open source anti-furry forums code made by Andreiplsno
# *idk why i made this open source*

import flask
import sqlite3

App = flask.Flask(__name__)

@App.route("/")
def LandingPage():
    return "Hello this is a test , If you are seeing this then it means Anti-Furry forums are under development"

App.run(port=80)