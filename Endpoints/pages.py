import flask
from flask import Blueprint, request, render_template, redirect , Response
import json
import random
from utils.GeneralUtils import Log, IsIpBlocked
import utils.Posts
import utils.Threads
from utils.Wrappers import logdata
import utils

webpages_bp = Blueprint('webpages', __name__)

with open("config.json") as f:
    configs = json.load(f)

def check_block():
    if IsIpBlocked(request.remote_addr):
        return render_template("pages/blocked.html"), 403
    return None

@webpages_bp.route("/")
@logdata()
def LandingPage():
    if (resp := check_block()):
        return resp
    return render_template("pages/landing.html")

@webpages_bp.route("/robots.txt")
@logdata()
def Robots():
    if (resp := check_block()):
        return resp
    with open('robots.txt', 'r') as f:
        content = f.read()
    return Response(content, mimetype='text/plain')


@webpages_bp.route("/login")
@logdata()
def LoginPage():
    if (resp := check_block()):
        return resp
    return render_template("pages/login.html", re_site=configs['re_captcha_site_key'],error_message='',message_color='red')

@webpages_bp.route("/search")
@logdata()
def SearchPage():
    if (resp := check_block()):
        return resp
    return render_template("pages/search.html")

@webpages_bp.route("/view/users/<username>")
@logdata()
def ViewUserPage(username):
    if (resp := check_block()):
        return resp
    return render_template("pages/view_username.html", username=username)

@webpages_bp.route("/view/@me")
@logdata()
def ViewMyselfPage():
    if (resp := check_block()):
        return resp
    return render_template("pages/view_me.html")

@webpages_bp.route("/view/threads/<thread>")
@logdata()
def ViewThreadPage(thread):
    if (resp := check_block()):
        return resp

    if 'token' not in request.cookies:
        return redirect('/login')

    return render_template(
        "pages/view_thread.html",
        thread = thread
    )

@webpages_bp.route("/threads/create/")
@logdata()
def CreateThread():
    if (resp := check_block()):
        return resp
    return render_template("pages/make_thread.html")

@webpages_bp.route("/app")
@logdata()
def AppPage():
    if (resp := check_block()):
        return resp

    if 'token' not in request.cookies:
        return redirect('/login')

    token = request.cookies['token']

    cursor, conn = utils.GeneralUtils.InnitDB()
    user = cursor.execute("SELECT username FROM users WHERE token=?", (token,)).fetchone()
    cursor.close()
    conn.close()

    if not user:
        return redirect('/login')

    posts = utils.Posts.ViewPosts(token, False)
    if posts['status'] == 'error':
        post_error = posts['message']
        posts = []
    else:
        post_error = None
        posts = posts['posts']

    threads = utils.Threads.ViewThreads(token, False)
    if threads['status'] == 'error':
        thread_error = threads['message']
        threads = []
    else:
        thread_error = None
        threads = threads['threads']

    return render_template(
        "pages/app.html",
        version=configs["version"],
        posts=posts,
        threads=threads,
        post_error=post_error,
        thread_error=thread_error
    )

@webpages_bp.route("/posts/create/")
@logdata()
def CreatePost():
    if (resp := check_block()):
        return resp
    return render_template("pages/make_post.html", re_site=configs['re_captcha_site_key'])

@webpages_bp.route("/view/post/<post>")
@logdata()
def ViewPostPage(post):
    if (resp := check_block()):
        return resp
    return render_template("pages/view_post.html", post=post)

@webpages_bp.route("/privacy-policy")
@logdata()
def Policy():
    if (resp := check_block()):
        return resp
    return render_template("pages/policy.html")

@webpages_bp.route("/guidlines")
@logdata()
def Guidlines():
    if (resp := check_block()):
        return resp
    return render_template("pages/guidlines.html")

@webpages_bp.route("/report/<id>")
@logdata()
def ReportPage(id):
    if (resp := check_block()):
        return resp
    return render_template("pages/report_form.html", id=id)

# Generate random admin path
randadmin = configs["admin_pass"] if configs["admin_pass"] else str(random.randint(1000, 9999))
Log(f"Admin randid is {randadmin}")

@webpages_bp.route(f"/admin-{randadmin}")
@logdata()
def AdminPage():
    if (resp := check_block()):
        return resp
    return render_template("pages/admin.html")
