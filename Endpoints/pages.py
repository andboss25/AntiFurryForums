
import flask
from flask import Blueprint, request, jsonify , current_app
import hashlib, time, requests
from utils.GeneralUtils import Log

import json
import random
import utils

webpages_bp = Blueprint('webpages', __name__)

configs = json.loads(open("config.json").read())

# Webpages

@webpages_bp.route("/")
@utils.Wrappers.logdata()
def LandingPage():
    if utils.GeneralUtils.IsIpBlocked(request.remote_addr):
        return open("pages/blocked.html").read(),403
    return open("pages/landing.html", encoding="utf-8").read()

@webpages_bp.route("/login")
@utils.Wrappers.logdata()
def LoginPage():
    if utils.GeneralUtils.IsIpBlocked(request.remote_addr):
        return open("pages/blocked.html").read(),403
    return open("pages/login.html", encoding="utf-8").read()

@webpages_bp.route("/search")
@utils.Wrappers.logdata()
def SearchPage():
    if utils.GeneralUtils.IsIpBlocked(request.remote_addr):
        return open("pages/blocked.html").read(),403

    return open("pages/search.html", encoding="utf-8").read()

@webpages_bp.route("/view/users/<username>")
@utils.Wrappers.logdata()
def ViewUserPage(username):
    if utils.GeneralUtils.IsIpBlocked(request.remote_addr):
        return open("pages/blocked.html").read(),403
    return flask.render_template_string(open("pages/view_username.html", encoding="utf-8").read(),username=username)

@webpages_bp.route("/view/@me")
@utils.Wrappers.logdata()
def ViewMyselfPage():
    if utils.GeneralUtils.IsIpBlocked(request.remote_addr):
        return open("pages/blocked.html").read(),403
    return open("pages/view_me.html", encoding="utf-8").read()

@webpages_bp.route("/view/threads/<thread>")
@utils.Wrappers.logdata()
def ViewThreadPage(thread):
    if utils.GeneralUtils.IsIpBlocked(request.remote_addr):
        return open("pages/blocked.html", encoding="utf-8").read(),403
    return flask.render_template_string(open("pages/view_thread.html", encoding="utf-8").read(),thread=thread)

@webpages_bp.route("/threads/create/")
@utils.Wrappers.logdata()
def CreateThread():
    if utils.GeneralUtils.IsIpBlocked(request.remote_addr):
        return open("pages/blocked.html").read(),403

    return open("pages/make_thread.html", encoding="utf-8").read()

@webpages_bp.route("/app")
@utils.Wrappers.logdata()
def AppPage():
    if utils.GeneralUtils.IsIpBlocked(request.remote_addr):
        return open("pages/blocked.html").read(),403

    return flask.render_template_string(open("pages/app.html", encoding="utf-8").read(),version=configs["version"])

@webpages_bp.route("/posts/create/")
@utils.Wrappers.logdata()
def CreatePost():
    if utils.GeneralUtils.IsIpBlocked(request.remote_addr):
        return open("pages/blocked.html").read(),403
    return flask.render_template_string(open("pages/make_post.html", encoding="utf-8").read())

@webpages_bp.route("/view/post/<post>")
@utils.Wrappers.logdata()
def ViewPostPage(post):
    if utils.GeneralUtils.IsIpBlocked(request.remote_addr):
        return open("pages/blocked.html").read(),403
    return flask.render_template_string(open("pages/view_post.html", encoding="utf-8").read(),post=post)

@webpages_bp.route("/privacy-policy")
@utils.Wrappers.logdata()
def Policy():
    if utils.GeneralUtils.IsIpBlocked(request.remote_addr):
        return open("pages/blocked.html").read(),403

    return open("pages/policy.html", encoding="utf-8").read()

@webpages_bp.route("/guidlines")
@utils.Wrappers.logdata()
def Guidlines():
    if utils.GeneralUtils.IsIpBlocked(request.remote_addr):
        return open("pages/blocked.html").read(),403

    return open("pages/guidlines.html", encoding="utf-8").read()

@webpages_bp.route("/report/<id>")
@utils.Wrappers.logdata()
def ReportPage(id):
    if utils.GeneralUtils.IsIpBlocked(request.remote_addr):
        return open("pages/blocked.html").read(),403
    return flask.render_template_string(open("pages/report_form.html", encoding="utf-8").read(),id=id)

if configs["admin_pass"] == "":
    randadmin = random.randrange(1000,9999)
else:
    randadmin = configs["admin_pass"]

Log(f"Admin randid is {randadmin}")

@webpages_bp.route(f"/admin-{str(randadmin)}")
@utils.Wrappers.logdata()
def AdminPage():
    if utils.GeneralUtils.IsIpBlocked(request.remote_addr):
        return open("pages/blocked.html").read(),403
    return open("pages/admin.html", encoding="utf-8").read()
