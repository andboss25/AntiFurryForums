# Open source anti-furry forums code made by Andreiplsno
# *idk why i made this open source*

import flask
from flask import request,jsonify,send_file
from werkzeug.utils import safe_join


import sqlite3
import hashlib
import time
import random
import json
import requests
import os

import utils.Wrappers
import utils.GeneralUtils
import utils.Init
from utils.GeneralUtils import Log

# Import Blueprints
from Endpoints.user import user_bp
from Endpoints.thread import thread_bp
from Endpoints.post import post_bp
from Endpoints.comment import comment_bp
from Endpoints.feed import feed_bp
from Endpoints.image import image_bp
from Endpoints.report import report_bp
from Endpoints.admin import admin_bp
from Endpoints.pages import webpages_bp

# Innit Database

configs = json.loads(open("config.json").read())

utils.Init.InitializeDbStruct()

Log("The Anti-furry forums are running!")
Log("This project was created by anti-furries!")
Log("Version is: " + configs["version"])

# App

App = flask.Flask(__name__,static_url_path="/static")

# Cooldown and shit
App.config["ADDR_LIST"] = {}

# Webpages
App.register_blueprint(webpages_bp)

# Api Endpoints
App.register_blueprint(user_bp, url_prefix='/api/user')
App.register_blueprint(thread_bp , url_prefix='/api/thread')
App.register_blueprint(post_bp , url_prefix='/api/post')
App.register_blueprint(comment_bp , url_prefix='/api/comment')
App.register_blueprint(feed_bp , url_prefix='/api/feed')
App.register_blueprint(image_bp, url_prefix='/api/images/')
App.register_blueprint(report_bp,url_prefix='/api/reports/')
App.register_blueprint(admin_bp)

# Run app
utils.Init.RunApp(App)