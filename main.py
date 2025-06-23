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
import utils.DatabaseInit

# Innit Database

configs = json.loads(open("config.json").read())

def Log(content,logfile=configs["logfile"]):
    if logfile == True:
        f = open("forums.log","a")
        f.write(content + "\n")
        f.close()
    else:
        print(content)

utils.DatabaseInit.InitializeDbStruct()

Log("The Anti-furry forums are running!")
Log("This project was created by anti-furries!")
Log("Version is: " + configs["version"])

# App

App = flask.Flask(__name__,static_url_path="/static")

# Cooldown and shit
addr_list = {}

# Webpages

@App.route("/")
@utils.Wrappers.logdata()
def LandingPage():
    if utils.GeneralUtils.IsIpBlocked(request.remote_addr):
        return open("pages/blocked.html").read(),403
    return open("pages/landing.html", encoding="utf-8").read()

@App.route("/login")
@utils.Wrappers.logdata()
def LoginPage():
    if utils.GeneralUtils.IsIpBlocked(request.remote_addr):
        return open("pages/blocked.html").read(),403
    return open("pages/login.html", encoding="utf-8").read()

@App.route("/search")
@utils.Wrappers.logdata()
def SearchPage():
    if utils.GeneralUtils.IsIpBlocked(request.remote_addr):
        return open("pages/blocked.html").read(),403

    return open("pages/search.html", encoding="utf-8").read()

@App.route("/view/users/<username>")
@utils.Wrappers.logdata()
def ViewUserPage(username):
    if utils.GeneralUtils.IsIpBlocked(request.remote_addr):
        return open("pages/blocked.html").read(),403
    return flask.render_template_string(open("pages/view_username.html", encoding="utf-8").read(),username=username)

@App.route("/view/@me")
@utils.Wrappers.logdata()
def ViewMyselfPage():
    if utils.GeneralUtils.IsIpBlocked(request.remote_addr):
        return open("pages/blocked.html").read(),403
    return open("pages/view_me.html", encoding="utf-8").read()

@App.route("/view/threads/<thread>")
@utils.Wrappers.logdata()
def ViewThreadPage(thread):
    if utils.GeneralUtils.IsIpBlocked(request.remote_addr):
        return open("pages/blocked.html", encoding="utf-8").read(),403
    return flask.render_template_string(open("pages/view_thread.html", encoding="utf-8").read(),thread=thread)

@App.route("/threads/create/")
@utils.Wrappers.logdata()
def CreateThread():
    if utils.GeneralUtils.IsIpBlocked(request.remote_addr):
        return open("pages/blocked.html").read(),403

    return open("pages/make_thread.html", encoding="utf-8").read()

@App.route("/app")
@utils.Wrappers.logdata()
def AppPage():
    if utils.GeneralUtils.IsIpBlocked(request.remote_addr):
        return open("pages/blocked.html").read(),403

    return flask.render_template_string(open("pages/app.html", encoding="utf-8").read(),version=configs["version"])

@App.route("/posts/create/<post>")
@utils.Wrappers.logdata()
def CreatePost(post):
    if utils.GeneralUtils.IsIpBlocked(request.remote_addr):
        return open("pages/blocked.html").read(),403
    return flask.render_template_string(open("pages/make_post.html", encoding="utf-8").read(),post=post)

@App.route("/view/post/<post>")
@utils.Wrappers.logdata()
def ViewPostPage(post):
    if utils.GeneralUtils.IsIpBlocked(request.remote_addr):
        return open("pages/blocked.html").read(),403
    return flask.render_template_string(open("pages/view_post.html", encoding="utf-8").read(),post=post)

@App.route("/privacy-policy")
@utils.Wrappers.logdata()
def Policy():
    if utils.GeneralUtils.IsIpBlocked(request.remote_addr):
        return open("pages/blocked.html").read(),403

    return open("pages/policy.html", encoding="utf-8").read()

@App.route("/guidlines")
@utils.Wrappers.logdata()
def Guidlines():
    if utils.GeneralUtils.IsIpBlocked(request.remote_addr):
        return open("pages/blocked.html").read(),403

    return open("pages/guidlines.html", encoding="utf-8").read()

@App.route("/report/<id>")
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

@App.route(f"/admin-{str(randadmin)}")
@utils.Wrappers.logdata()
def AdminPage():
    if utils.GeneralUtils.IsIpBlocked(request.remote_addr):
        return open("pages/blocked.html").read(),403
    return open("pages/admin.html", encoding="utf-8").read()

# Users api

# Check if ip is blocked
# Check if request is json
# Check if it has all parameters needed
# Check if there is already a user with that username
# Check if the given username respects all constraints: lenght of 25 , no spaces , no special char like 'forbidden_chars'
@App.route("/api/signup",methods=["POST"])
@utils.Wrappers.guard_api(addr_list)
@utils.Wrappers.logdata()
@utils.Wrappers.require_json_with_fields(["username","password"])
def SignupApi():
    forbidden_chars = {" ", "#", "@", "$", "%", "^", "&", "*", "(", ")", "-", "=", "+", "<", ">", "[", "]"}

    if not request.is_json:

        return jsonify({"Error":"This request is not identified as JSON"}),400
    
    cursor,conn = utils.GeneralUtils.InnitDB()

    if not (cursor.execute("SELECT username FROM users WHERE username=?",(request.json.get("username"),)).fetchone() == None):

        return jsonify({"Error":"Username already used"}),400
    
    if not request.json.get("username") or len(request.json.get("username")) >= 25 or any(char in forbidden_chars for char in request.json.get("username")):

        return jsonify({"Error":"Username dosen't repsect constrains"}),400

    hash_pass = hashlib.sha256()
    hash_pass.update(request.json.get("password").encode())
    hashed_password = hash_pass.hexdigest()

    token = utils.GeneralUtils.GenerateToken(request.json.get("username"),request.json.get("password"))
    cursor.execute("INSERT INTO users(username,display_name,encrypted_password,timestamp,token) VALUES (?,?,?,?,?)",(
        request.json.get("username").lower(),
        request.json.get("username"),
        hashed_password,
        str(time.time()),
        token
    ))
    
    conn.commit()
    cursor.close()
    conn.close()

    if configs["webhook"] == True:
        requests.post(configs["webhook_url"], json={"content": f"Someone created an account '{request.json.get('username')}'"})

    return jsonify({"Message":"Success","Token":token}),200

# Check if ip is blocked
# Check if it has all parameters needed
# Check if there is a user with that username
# Check if the password is correct
# Check if the acc is deleted
# Return token
@App.route("/api/login",methods=["GET"])
@utils.Wrappers.guard_api(addr_list)
@utils.Wrappers.logdata()
@utils.Wrappers.require_query_params(["username","password"])
def LoginApi():
    cursor,conn = utils.GeneralUtils.InnitDB()

    if (cursor.execute("SELECT username FROM users WHERE username=?",(request.args.get("username").lower(),)).fetchone() == None):

        return jsonify({"Error":"No user with such username"}),400
    
    enc_pass = hashlib.sha256()
    enc_pass.update(request.args.get("password").encode())
    enc_pass = enc_pass.hexdigest()

    row = cursor.execute("SELECT encrypted_password FROM users WHERE username=?", (request.args.get("username").lower(),)).fetchone()
    if not row or row[0] != enc_pass:
        
        return jsonify({"Error": "Invalid password"}), 400
    
    row = cursor.execute("SELECT deleted FROM users WHERE username=?", (request.args.get("username").lower(),)).fetchone()
    if not row or row[0] != 0:
        
        return jsonify({"Error": "User is deleted, if you manually deleted this account you can restore it by emailing 'afcommsnet.contact@gmail.com' and stating your intentions!"}), 400

    row = cursor.execute("SELECT banned FROM users WHERE username=?", (request.args.get("username").lower(),)).fetchone()
    if not row or row[0] != 0:
        
        return jsonify({"Error": "Your account has been permanently banned off this website! You may appeal at 'afcommsnet.contact@gmail.com' by emailing set adress and stating your intentions! You may also find the specific ban reason from there."}), 400
    
    token = cursor.execute("SELECT token FROM users WHERE username=?", (request.args.get("username").lower(),)).fetchone()[0]
    
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"Message":"Success","Token":token}),200

# Check if ip is blocked
# Check if it has all parameters needed
# Check if the token is valid
# Get user parameters from given user and if it returns None then display No user found
@App.route("/api/users/view",methods=["GET"])
@utils.Wrappers.guard_api(addr_list)
@utils.Wrappers.logdata()
@utils.Wrappers.require_query_params(["username","token"])
def UserViewApi():
    cursor,conn = utils.GeneralUtils.InnitDB()

    if (cursor.execute("SELECT token FROM users WHERE token=?",(request.args.get("token"),)).fetchone() == None):
        # OPTIMIZATION TODO: Make this get the username from token then check token validity

        return jsonify({"Error":"Token is invalid"}),400
    
    user = cursor.execute("SELECT username,display_name,bio,timestamp,admin,id,deleted FROM users WHERE username=?",(request.args.get("username").lower(),)).fetchone()
    user_obj = {}

    if user == None:
        user_obj = {"Message":"No user found!"}
    else:
        is_admin = lambda val:False if val == 0 else True
        is_deleted = lambda val:False if val == 0 else True

        if not is_deleted(user[6]):
            user_obj = {
                "Message":"User was found!",
                "username":user[0].lower(),
                "display_name":user[1],
                "bio":user[2],
                "created_on":user[3],
                "is_admin":  is_admin(user[4]),
                "user_id":user[5],
            }
        else:
            user_obj = {"Message":"No user found!","deleted":True}
    
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"User":user_obj}),200

# Check if ip is blocked
# Check if it has all parameters needed
# Check if the token is valid
# Get user parameters from given user and if it returns None then display No user found
@App.route("/api/users/viewall",methods=["GET"])
@utils.Wrappers.guard_api(addr_list)
@utils.Wrappers.logdata()
@utils.Wrappers.require_query_params(["token"])
def UserViewallApi():
    cursor,conn = utils.GeneralUtils.InnitDB()

    if (cursor.execute("SELECT token FROM users WHERE token=?",(request.args.get("token"),)).fetchone() == None):
        # OPTIMIZATION TODO: Make this get the username from token then check token validity

        return jsonify({"Error":"Token is invalid"}),400
    
    users = cursor.execute("SELECT username,id FROM users").fetchall()
    user_obj = {}

    if users == None:
        user_obj = {"Message":"No users found!"}
    else:
        user_obj = users
    
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"Users":user_obj}),200

# Check if ip is blocked
# Check if it has all parameters needed
# Check if the token is valid
# Get params from user with set token
@App.route("/api/users/tokendata",methods=["GET"])
@utils.Wrappers.guard_api(addr_list)
@utils.Wrappers.logdata()
@utils.Wrappers.require_query_params(["token"])
def TokenViewApi():
    
    cursor,conn = utils.GeneralUtils.InnitDB()

    if (cursor.execute("SELECT token FROM users WHERE token=?",(request.args.get("token"),)).fetchone() == None):
        # OPTIMIZATION TODO: Make this get the username from token then check token validity

        return jsonify({"Error":"Token is invalid"}),400
    
    user = cursor.execute("SELECT username,display_name,bio,timestamp,admin,id FROM users WHERE token=?",(request.args.get("token"),)).fetchone()
    user_obj = {}

    if user == None:
        user_obj = {"Message":"No user with set token found!"}
    else:
        is_admin = lambda val:False if val == 0 else True
        user_obj = {
            "Message":"User was found!",
            "username":user[0].lower(),
            "display_name":user[1],
            "bio":user[2],
            "created_on":user[3],
            "is_admin":  is_admin(user[4]),
            "user_id":user[5],
        }
    
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"User":user_obj}),200

# Check if ip is blocked
# Check if request is json
# Check if it has all parameters needed
# Check if the token is valid
# Set account as deleted
@App.route("/api/users/delete",methods=["DELETE"])
@utils.Wrappers.guard_api(addr_list)
@utils.Wrappers.logdata()
@utils.Wrappers.require_query_params(["token"])
def UserDeleteApi():
    cursor, conn = utils.GeneralUtils.InnitDB()

    if cursor.execute("SELECT token FROM users WHERE token=?", (request.args.get("token"),)).fetchone() is None:
        
        return jsonify({"Error": "Token is invalid"}), 400
    
    # BUG Possible vuln where user might keep track of their token before deleting their account and use their deleted account to do stuff

    cursor.execute("UPDATE users SET deleted=1 WHERE token=?", (request.args.get("token"),))
    

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"Message": "Success"}), 200


# Check if ip is blocked
# Check if request is json
# Check if it has all parameters needed
# Check if the token is valid
# Check constraints
# Patch to all params needed
@App.route("/api/users/modify",methods=["PATCH"])
@utils.Wrappers.guard_api(addr_list)
@utils.Wrappers.logdata()
@utils.Wrappers.require_json_with_fields(["token","display_name","bio"])
def UserModifyApi():
    forbidden_chars = {" ", "#", "@", "$", "%", "^", "&", "*", "(", ")", "-", "=", "+", "<", ">", "[", "]"}
    display_forbidden_chars = {"#", "@", "$", "%", "^", "&", "*", "(", ")", "-", "=", "+", "<", ">"}
    
    if not request.json.get("display_name") or len(request.json.get("display_name")) >= 40 or any(char in display_forbidden_chars for char in request.json.get("display_name")):

        return jsonify({"Error":"Display name dosen't repsect constrains"}),400
    
    if not request.json.get("bio") or len(request.json.get("bio")) > 200:

        return jsonify({"Error":"Bio dosen't repsect constrains"}),400
    
    cursor,conn = utils.GeneralUtils.InnitDB()

    if (cursor.execute("SELECT token FROM users WHERE token=?",(request.json.get("token"),)).fetchone() == None):
        # OPTIMIZATION TODO: Make this get the username from token then check token validity

        return jsonify({"Error":"Token is invalid"}),400
    
    # OPTIMIZATION TODO: Make this get the username from token to delete easier
    cursor.execute("UPDATE users SET display_name=?, bio=? WHERE token=?",(request.json.get("display_name"),request.json.get("bio"),request.json.get("token"),))
    
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"Message":"Success"}),200

# Thread api

# Check if ip is blocked
# Check if request is json
# Check if it has all parameters needed
# Check if identifier name is already used
# Check if the params are all valid
# Insert into db
@App.route("/api/thread/post", methods=["POST"])
@utils.Wrappers.guard_api(addr_list)
@utils.Wrappers.logdata()
@utils.Wrappers.require_json_with_fields(["name","description","identifier","token"])
def MakeThread():
    forbidden_chars = {" ", "#", "@", "$", "%", "^", "&", "*", "(", ")", "-", "=", "+", "<", ">", "[", "]"}

    data = request.json

    name = data["name"]
    description = data["description"]
    identifier = data["identifier"]

    if (
        len(identifier) >= 25 or
        any(char in forbidden_chars for char in identifier) or
        len(name) > 50 or
        len(description) > 200
    ):
        
        return jsonify({"Error": "Request doesn't respect constraints"}), 400

    cursor, conn = utils.GeneralUtils.InnitDB()

    user = cursor.execute("SELECT id FROM users WHERE token=?", (data["token"],)).fetchone()
    if not user:
        
        return jsonify({"Error": "Token is invalid"}), 401

    if cursor.execute("SELECT identifier FROM threads WHERE identifier=?", (identifier,)).fetchone():
        
        return jsonify({"Error": "Identifier already used"}), 400

    username = utils.GeneralUtils.GetUsernameFromToken(data["token"])
    cursor.execute(
        "INSERT INTO threads(owner_username, name, identifier, description) VALUES (?, ?, ?, ?)",
        (username, name, identifier, description)
    )

    conn.commit()
    cursor.close()
    conn.close()

    if configs["webhook"] == True:
        requests.post(configs["webhook_url"],json={"content":f"{username} created a thread '{identifier}' with name '{name}' description '{description}'"})

    return jsonify({"Message": "Success"}), 200

# View threads with option to search or filter by identifier
# Check if IP is blocked
# Check for cooldown on IP
# Validate required parameters: token, search
# Validate token and get username
# Search threads or filter by thread_identifier or get all threads
# Get user's subscribed threads
# Add 'subscribed' flag to each thread in the response
@App.route("/api/thread/view", methods=["GET"])
@utils.Wrappers.guard_api(addr_list)
@utils.Wrappers.logdata()
@utils.Wrappers.require_query_params(["token", "search"])
def ViewThreads():
    data = request.args
    token = data["token"]
    search = data["search"].lower() == "true"

    cursor, conn = utils.GeneralUtils.InnitDB()

    user = cursor.execute("SELECT username FROM users WHERE token=?", (token,)).fetchone()
    if not user:
        
        cursor.close()
        conn.close()
        return jsonify({"Error": "Token is invalid"}), 400

    username = user[0]

    if search:
        search_for = data.get("search_for", "")
        query = "SELECT * FROM threads WHERE description LIKE ? OR name LIKE ? OR identifier LIKE ?"
        like_term = f"%{search_for}%"
        threads = cursor.execute(query, (like_term, like_term, like_term)).fetchall()
    elif "thread_identifier" in data:
        thread_identifier = data["thread_identifier"]
        threads = cursor.execute("SELECT * FROM threads WHERE identifier=?", (thread_identifier,)).fetchall()
    elif "filter_by_user" in data:
        fbu = data["filter_by_user"]
        threads = cursor.execute("SELECT * FROM threads WHERE owner_username=?", (fbu,)).fetchall()
    else:
        threads = cursor.execute("SELECT * FROM threads").fetchall()

    subscribed = cursor.execute(
        "SELECT thread_identifier FROM subscribed_threads WHERE username=?", (username,)
    ).fetchall()
    subscribed_set = set(row[0] for row in subscribed)

    thread_list = []
    for thread in threads:
        thread_subs = cursor.execute("SELECT * FROM subscribed_threads WHERE thread_identifier=?",(thread[3],))
        thread_dict = {
            "id": thread[0],
            "owner_username": thread[1],
            "name": thread[2],
            "identifier": thread[3],
            "description": thread[4],
            "subscribed": thread[3] in subscribed_set,
            "subscribed_count": len(thread_subs.fetchall())
        }
        thread_list.append(thread_dict)
        

    conn.commit()
    cursor.close()
    conn.close()


    return jsonify({"Message": "Success", "Threads": thread_list}), 200

# Check if ip is blocked
# Check if request is JSON
# Check if it has all parameters needed
# Validate token and ownership
# Delete thread if it exists and belongs to user
@App.route("/api/thread/delete", methods=["DELETE"])
@utils.Wrappers.guard_api(addr_list)
@utils.Wrappers.logdata()
@utils.Wrappers.require_query_params((["token", "identifier"]))
def DeleteThread():
    data = request.args
    token = data["token"]
    identifier = data["identifier"]

    cursor, conn = utils.GeneralUtils.InnitDB()

    username = utils.GeneralUtils.GetUsernameFromToken(token)
    if not username:
        cursor.close()
        conn.close()
        return jsonify({"Error": "Invalid token"}), 401

    thread = cursor.execute(
        "SELECT * FROM threads WHERE identifier=? AND owner_username=?", (identifier, username)
    ).fetchone()

    if not thread:
        cursor.close()
        conn.close()
        return jsonify({"Error": "Thread not found or not owned by user"}), 404

    cursor.execute("DELETE FROM threads WHERE identifier=? AND owner_username=?", (identifier, username))

    conn.commit()
    cursor.close()
    conn.close()


    return jsonify({"Message": "Thread successfully deleted"}), 200

# Check if IP is blocked
# Check if request is JSON
# Check if all parameters exist
# Validate token and user
# Subscribe or unsubscribe based on action
@App.route("/api/thread/subscribe", methods=["POST"])
@utils.Wrappers.guard_api(addr_list)
@utils.Wrappers.logdata()
@utils.Wrappers.require_json_with_fields(["token", "identifier", "action"])
def SubscribeThread():
    data = request.json
    token = data["token"]
    identifier = data["identifier"]
    action = data["action"].lower()

    username = utils.GeneralUtils.GetUsernameFromToken(token)
    if not username:
        
        return jsonify({"Error": "Invalid token"}), 401

    cursor, conn = utils.GeneralUtils.InnitDB()

    # Check if thread exists
    thread_exists = cursor.execute("SELECT 1 FROM threads WHERE identifier=?", (identifier,)).fetchone()
    if not thread_exists:
        cursor.close()
        conn.close()
        return jsonify({"Error": "Thread does not exist"}), 404

    if action == "subscribe":
        existing = cursor.execute(
            "SELECT 1 FROM subscribed_threads WHERE username=? AND thread_identifier=?",
            (username.lower(), identifier)
        ).fetchone()

        if existing:
            cursor.close()
            conn.close()
            return jsonify({"Error": "Already subscribed"}), 400

        cursor.execute(
            "INSERT INTO subscribed_threads(username, thread_identifier) VALUES (?, ?)",
            (username, identifier)
        )
        conn.commit()

    elif action == "unsubscribe":
        cursor.execute(
            "DELETE FROM subscribed_threads WHERE username=? AND thread_identifier=?",
            (username, identifier)
        )
        conn.commit()

    else:
        cursor.close()
        conn.close()
        return jsonify({"Error": "Action must be either 'subscribe' or 'unsubscribe'"}), 400

    cursor.close()
    conn.close()

    return jsonify({"Message": f"Successfully {action}d to thread"}), 200


# List all threads that the user is subscribed to
# Check if IP is blocked
# Check if token parameter is provided
# Validate token and get username
# Query subscribed threads for the user
# Return the list of subscribed thread identifiers
@App.route("/api/thread/subscriptions", methods=["GET"])
@utils.Wrappers.guard_api(addr_list)
@utils.Wrappers.logdata()
@utils.Wrappers.require_query_params(["token"])
def ListUserSubscriptions():
    data = request.args
    token = data["token"]

    cursor, conn = utils.GeneralUtils.InnitDB()

    user = cursor.execute("SELECT username FROM users WHERE token=?", (token,)).fetchone()
    if not user:
        
        cursor.close()
        conn.close()
        return jsonify({"Error": "Token is invalid"}), 400

    username = user[0]

    subscriptions = cursor.execute(
        "SELECT username,thread_identifier FROM subscribed_threads WHERE username=?", (username.lower(),)
    ).fetchall()

    conn.commit()
    cursor.close()
    conn.close()
    

    return jsonify({"Message": "Success", "SubscribedThreads": subscriptions}), 200

# Post api

# Check if ip is blocked
# Check if request is json
# Check if it has all parameters needed
# Check if the params are all valid
# Insert into db
@App.route("/api/post/post", methods=["POST"])
@utils.Wrappers.guard_api(addr_list)
@utils.Wrappers.logdata()
@utils.Wrappers.require_json_with_fields(["title","content","token","thread_identifier"])
def MakePost():
    forbidden_chars = {" ", "#", "@", "$", "%", "^", "&", "*", "(", ")", "-", "=", "+", "<", ">", "[", "]"}

    data = request.json

    title = data["title"]
    content = data["content"]
    thread_identifier = data["thread_identifier"]

    if (
        len(content) >= 300 or
        len(title) > 50
    ):
        
        return jsonify({"Error": "Request doesn't respect constraints"}), 400
    
        
    try:
        image_attachment = data["image_attachment"]
    except KeyError:
        image_attachment = ""

    # Filter external images for the sake of no zero-click vulns and such
    if image_attachment.startswith("https://") or image_attachment.startswith("http://"):
        image_attachment = ""
    elif image_attachment.startswith("/api/images/view/"):
        pass
    else:
        image_attachment = ""
        
    cursor, conn = utils.GeneralUtils.InnitDB()

    user = cursor.execute("SELECT id FROM users WHERE token=?", (data["token"],)).fetchone()
    if not user:
        
        return jsonify({"Error": "Token is invalid"}), 401
    
    if not cursor.execute("SELECT identifier FROM threads WHERE identifier=?", (thread_identifier,)).fetchone():
        
        return jsonify({"Error": "No such thread with this identifier!"}), 400

    username = utils.GeneralUtils.GetUsernameFromToken(data["token"])
    cursor.execute(
        "INSERT INTO posts(owner_username,thread_identifier,content,title,image_attachment) VALUES (?, ?, ?, ?, ?)",
        (username,thread_identifier,content,title,image_attachment)
    )

    conn.commit()
    cursor.close()
    conn.close()

    
    if configs["webhook"] == True:
        requests.post(configs["webhook_url"],json={"content":f"{username} created a post on '{thread_identifier}' with title '{title}' and content '{content}'"})

    return jsonify({"Message": "Success"}), 200

# Check if IP is blocked
# Check for cooldown on IP
# Validate required parameters: token, search
# Validate token and get username
# Search posts or filter by post_identifier or get all posts
# Get user's subscribed posts
# Add 'liked' flag to each post in response
@App.route("/api/post/view", methods=["GET"])
@utils.Wrappers.guard_api(addr_list)
@utils.Wrappers.logdata()
@utils.Wrappers.require_query_params(["token", "search"])
def ViewPosts():
    data = request.args
    token = data["token"]
    search = data["search"].lower() == "true"

    cursor, conn = utils.GeneralUtils.InnitDB()

    user = cursor.execute("SELECT username FROM users WHERE token=?", (token,)).fetchone()
    if not user:
        
        cursor.close()
        conn.close()
        return jsonify({"Error": "Token is invalid"}), 400

    username = user[0]

    if search:
        search_for = data.get("search_for", "")
        query = "SELECT * FROM posts WHERE content LIKE ? OR title LIKE ?"
        like_term = f"%{search_for}%"
        posts = cursor.execute(query, (like_term, like_term)).fetchall()
    elif "post_identifier" in data:
        post_identifier = data["post_identifier"]
        posts = cursor.execute("SELECT * FROM posts WHERE thread_identifier=?", (post_identifier,)).fetchall()
    elif "id" in data:
        posts = cursor.execute("SELECT * FROM posts WHERE id=?", (data["id"],)).fetchall()
    else:
        posts = cursor.execute("SELECT * FROM posts").fetchall()
    
    liked = [row[0] for row in cursor.execute(
        "SELECT post_id FROM liked_posts WHERE username = ?", (username,)
    ).fetchall()]

    post_list = []
    for post in posts:
        is_liked = str(post[0]) in liked

        post_likes = cursor.execute("SELECT * FROM liked_posts WHERE post_id=?",(post[0],))
        
        post_dict = {
            "id": post[0],
            "owner_username": post[1],
            "post_identifier": post[2],
            "title": post[3],
            "content": post[4],
            "image_attachment": post[5],
            "liked": is_liked,
            "timestamp": post[6],
            "likes":len(post_likes.fetchall())
        }
        post_list.append(post_dict)
    conn.commit()
    cursor.close()
    conn.close()


    return jsonify({"Message": "Success", "Posts": post_list}), 200

@App.route("/api/post/feed", methods=["GET"])
@utils.Wrappers.guard_api(addr_list)
@utils.Wrappers.logdata()
@utils.Wrappers.require_query_params(["token"])
def PostsFeed():
    data = request.args
    token = data["token"]

    cursor, conn = utils.GeneralUtils.InnitDB()

    user = cursor.execute("SELECT username FROM users WHERE token=?", (token,)).fetchone()
    if not user:
        
        cursor.close()
        conn.close()
        return jsonify({"Error": "Token is invalid"}), 400

    username = user[0]

    # Subscribed threads
    subscribed_threads = [row[0] for row in cursor.execute(
        "SELECT thread_identifier FROM subscribed_threads WHERE username = ?", (username,)
    ).fetchall()]

    # Posts from subscribed threads (random order)
    if subscribed_threads:
        placeholders = ','.join('?' for _ in subscribed_threads)
        subscribed_posts = cursor.execute(
            f"""
            SELECT * FROM posts 
            WHERE thread_identifier IN ({placeholders}) 
            ORDER BY RANDOM() 
            LIMIT 20
            """, 
            subscribed_threads
        ).fetchall()
    else:
        subscribed_posts = []

    # Posts from other threads (also random)
    already_included_ids = [post[0] for post in subscribed_posts]
    if already_included_ids:
        placeholders = ','.join('?' for _ in already_included_ids)
        other_posts = cursor.execute(
            f"""
            SELECT * FROM posts 
            WHERE id NOT IN ({placeholders}) 
            ORDER BY RANDOM()
            """, 
            already_included_ids
        ).fetchall()
    else:
        other_posts = cursor.execute(
            "SELECT * FROM posts ORDER BY RANDOM() LIMIT 10"
        ).fetchall()

    posts = subscribed_posts + other_posts

    # Get liked posts for the user
    liked = [row[0] for row in cursor.execute(
        "SELECT post_id FROM liked_posts WHERE username = ?", (username,)
    ).fetchall()]

    post_list = []
    for post in posts:
        is_liked = str(post[0]) in liked
        post_likes = cursor.execute("SELECT COUNT(*) FROM liked_posts WHERE post_id=?", (post[0],)).fetchone()[0]

        post_dict = {
            "id": post[0],
            "owner_username": post[1],
            "post_identifier": post[2],
            "title": post[3],
            "content": post[4],
            "image_attachment": post[5],
            "liked": is_liked,
            "timestamp": post[6],
            "likes": post_likes
        }
        post_list.append(post_dict)

    # Optionally deduplicate by post ID
    post_list = list({post["id"]: post for post in post_list}.values())

    conn.commit()
    cursor.close()
    conn.close()


    return jsonify({"Message": "Success", "Posts": post_list}), 200

@App.route("/api/thread/recomended", methods=["GET"])
@utils.Wrappers.guard_api(addr_list)
@utils.Wrappers.logdata()
@utils.Wrappers.require_query_params(["token"])
def RecomendThreads():
    data = request.args
    token = data["token"]

    cursor, conn = utils.GeneralUtils.InnitDB()

    user = cursor.execute("SELECT username FROM users WHERE token=?", (token,)).fetchone()
    if not user:
        
        cursor.close()
        conn.close()
        return jsonify({"Error": "Token is invalid"}), 400

    username = user[0]

    threads = cursor.execute("SELECT * FROM threads").fetchall()

    subscribed = cursor.execute(
        "SELECT thread_identifier FROM subscribed_threads WHERE username=?", (username,)
    ).fetchall()
    subscribed_set = set(row[0] for row in subscribed)

    thread_list = []
    for thread in threads:
        thread_subs = cursor.execute("SELECT * FROM subscribed_threads WHERE thread_identifier=?",(thread[3],))
        thread_dict = {
            "id": thread[0],
            "owner_username": thread[1],
            "name": thread[2],
            "identifier": thread[3],
            "description": thread[4],
            "subscribed": thread[3] in subscribed_set,
            "subscribed_count": len(thread_subs.fetchall())
        }
        thread_list.append(thread_dict)
        

    conn.commit()
    cursor.close()
    conn.close()


    return jsonify({"Message": "Success", "Threads": thread_list}), 200

# Check if ip is blocked
# Check if request is JSON
# Check if it has all parameters needed
# Validate token and ownership
# Delete post if it exists and belongs to user
@App.route("/api/posts/delete", methods=["DELETE"])
@utils.Wrappers.guard_api(addr_list)
@utils.Wrappers.logdata()
@utils.Wrappers.require_query_params((["token", "id"]))
def DeletePost():
    data = request.args
    token = data["token"]
    id = data["id"]

    cursor, conn = utils.GeneralUtils.InnitDB()

    username = utils.GeneralUtils.GetUsernameFromToken(token)
    if not username:
        
        cursor.close()
        conn.close()
        return jsonify({"Error": "Invalid token"}), 401

    post = cursor.execute(
        "SELECT * FROM posts WHERE id=? AND owner_username=?", (id, username)
    ).fetchone()

    if not post:
        cursor.close()
        conn.close()
        return jsonify({"Error": "Post not found or not owned by user"}), 404

    cursor.execute("DELETE FROM posts WHERE id=? AND owner_username=?", (id, username))

    conn.commit()
    cursor.close()
    conn.close()


    return jsonify({"Message": "Post successfully deleted"}), 200


# Check if IP is blocked
# Check if request is JSON
# Check if all parameters exist
# Validate token and user
# Like or unlike based on action
@App.route("/api/posts/like", methods=["POST"])
@utils.Wrappers.guard_api(addr_list)
@utils.Wrappers.logdata()
@utils.Wrappers.require_json_with_fields(["token", "id", "action"])
def LikePost():
    data = request.json
    token = data["token"]
    id = data["id"]
    action = data["action"].lower()

    username = utils.GeneralUtils.GetUsernameFromToken(token)
    cursor, conn = utils.GeneralUtils.InnitDB()

    user = cursor.execute("SELECT username FROM users WHERE token=?", (token,)).fetchone()
    if not user:
        
        cursor.close()
        conn.close()
        return jsonify({"Error": "Token is invalid"}), 400

    thread_exists = cursor.execute("SELECT 1 FROM posts WHERE id=?", (id,)).fetchone()
    if not thread_exists:
        cursor.close()
        conn.close()
        return jsonify({"Error": "Post does not exist"}), 404

    if action == "like":
        existing = cursor.execute(
            "SELECT 1 FROM liked_posts WHERE username=? AND post_id=?",
            (username.lower(), id)
        ).fetchone()

        if existing:
            cursor.close()
            conn.close()
            return jsonify({"Error": "Already liked"}), 400

        cursor.execute(
            "INSERT INTO liked_posts(username, post_id) VALUES (?, ?)",
            (username, id)
        )
        conn.commit()

    elif action == "unlike":
        cursor.execute(
            "DELETE FROM liked_posts WHERE username=? AND post_id=?",
            (username, id)
        )
        conn.commit()

    else:
        cursor.close()
        conn.close()
        return jsonify({"Error": "Action must be either 'like' or 'unlike'"}), 400

    cursor.close()
    conn.close()

    return jsonify({"Message": f"Successfully {action}d the post"}), 200

# Comments api

# Check if ip is blocked
# Check if request is json
# Check if it has all parameters needed
# Check if the params are all valid
# Insert into db
@App.route("/api/comment/post", methods=["POST"])
@utils.Wrappers.guard_api(addr_list)
@utils.Wrappers.logdata()
@utils.Wrappers.require_json_with_fields(["content","token","post_id"])
def MakeComment():
    data = request.json

    content = data["content"]
    post_id = data["post_id"]

    if (
        len(content) >= 100
    ):
        
        return jsonify({"Error": "Request doesn't respect constraints"}), 400

    cursor, conn = utils.GeneralUtils.InnitDB()

    user = cursor.execute("SELECT id FROM users WHERE token=?", (data["token"],)).fetchone()
    if not user:
        
        return jsonify({"Error": "Token is invalid"}), 401
    
    if not cursor.execute("SELECT id FROM posts WHERE id=?", (post_id,)).fetchone():
        
        return jsonify({"Error": "No such post with this id!"}), 400

    username = utils.GeneralUtils.GetUsernameFromToken(data["token"])
    cursor.execute(
        "INSERT INTO comments(owner_username,post_id,content) VALUES (?, ?, ?)",
        (username,post_id,content)
    )

    conn.commit()
    cursor.close()
    conn.close()

    if configs["webhook"] == True:
        requests.post(configs["webhook_url"],json={"content":f"{username} created a comment on post with id '{post_id}' with content '{content}'"})


    return jsonify({"Message": "Success"}), 200
    

# Check if IP is blocked
# Check for cooldown on IP
# Validate required parameters: token, post_id
# Validate token and get username
# Get user's liked comments
# Add 'liked' flag to each comment in response
@App.route("/api/comments/view", methods=["GET"])
@utils.Wrappers.guard_api(addr_list)
@utils.Wrappers.logdata()
@utils.Wrappers.require_query_params(["token","post_id"])
def ViewComments():
    data = request.args
    token = data["token"]
    post_id = data["post_id"]

    cursor, conn = utils.GeneralUtils.InnitDB()

    user = cursor.execute("SELECT username FROM users WHERE token=?", (token,)).fetchone()
    if not user:
        
        cursor.close()
        conn.close()
        return jsonify({"Error": "Token is invalid"}), 400

    username = user[0]

    comments = cursor.execute("SELECT * FROM comments WHERE post_id=?",(post_id,)).fetchall()

    liked = [row[0] for row in cursor.execute(
        "SELECT id FROM liked_comments WHERE username = ?", (username,)
    ).fetchall()]

    comments_list = []
    for comment in comments:
        is_liked = comment[0] in liked
        
        post_dict = {
            "id": comment[0],
            "owner_username": comment[1],
            "post_id":comment[2],
            "content":comment[3],
            "timestamp":comment[4],
            "liked":is_liked
        }
        comments_list.append(post_dict)
    conn.commit()
    cursor.close()
    conn.close()


    return jsonify({"Message": "Success", "Comments": comments_list}), 200

# Check if ip is blocked
# Check if request is JSON
# Check if it has all parameters needed
# Validate token and ownership
# Delete post if it exists and belongs to user
@App.route("/api/comments/delete", methods=["DELETE"])
@utils.Wrappers.guard_api(addr_list)
@utils.Wrappers.logdata()
@utils.Wrappers.require_query_params((["token", "id"]))
def DeleteComment():
    data = request.args
    token = data["token"]
    id = data["id"]

    cursor, conn = utils.GeneralUtils.InnitDB()

    username = utils.GeneralUtils.GetUsernameFromToken(token)
    if not username:
        
        cursor.close()
        conn.close()
        return jsonify({"Error": "Invalid token"}), 401

    post = cursor.execute(
        "SELECT * FROM comments WHERE id=? AND owner_username=?", (id, username)
    ).fetchone()

    if not post:
        cursor.close()
        conn.close()
        return jsonify({"Error": "Comment not found or not owned by user"}), 404

    cursor.execute("DELETE FROM comments WHERE id=? AND owner_username=?", (id, username))

    conn.commit()
    cursor.close()
    conn.close()


    return jsonify({"Message": "Comment successfully deleted"}), 200

# Image API

@App.route("/api/images/add", methods=["POST"])
@utils.Wrappers.guard_api(addr_list)
@utils.Wrappers.logdata()
def UploadImage():
    ALLOWED_MIMETYPES = {"image/png", "image/jpeg", "image/gif", "video/mp4"}

    cursor, conn = utils.GeneralUtils.InnitDB()
    
    token = request.form.get("token")
    if not token:
        return jsonify({"Error": "Missing token"}), 400

    username = utils.GeneralUtils.GetUsernameFromToken(token)

    if not username:
        return jsonify({"Error": "Invalid token"}), 401
    
    user = cursor.execute("SELECT id FROM users WHERE token=?", (token,)).fetchone()
    if not user:
        return jsonify({"Error": "Token is invalid"}), 401

    if 'file' not in request.files:
        return jsonify({"Error": "No image attached"}), 400

    image = request.files['file']
    
    if image.mimetype not in ALLOWED_MIMETYPES:
        return jsonify({"Error": "Invalid file"}), 400

    file_bytes = image.read()
    if len(file_bytes) > configs["MaxUploadSize"] * 1024 * 1024: 
        return jsonify({"Error": "File too large"}), 413
    
    image.seek(0)

    file_type_base = {"image/png":"png", "image/jpeg":"jpeg", "image/gif":"gif", "video/mp4":"mp4"}

    rint = random.randrange(1000,9999)

    filepath = os.path.join("Images", f"{username}-{rint}.{file_type_base[image.mimetype]}")
    image.save(filepath, 2048)

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"Message": "Successfully uploaded file","Url":f"/api/images/view/{username}-{rint}.{file_type_base[image.mimetype]}"}), 200

@App.route("/api/images/view/<image>", methods=["GET"])
@utils.Wrappers.guard_api(addr_list)
@utils.Wrappers.logdata()
def ViewImage(image):

    cursor, conn = utils.GeneralUtils.InnitDB()

    token = request.args.get("token")
    if not token:
        return jsonify({"Error": "Missing token"}), 400

    username = utils.GeneralUtils.GetUsernameFromToken(token)
    if not username:
        return jsonify({"Error": "Invalid token"}), 401
    
    user = cursor.execute("SELECT id FROM users WHERE token=?", (token,)).fetchone()
    if not user:
        return jsonify({"Error": "Token is invalid"}), 401

    image_dir = os.path.abspath("Images")
    image_path = safe_join(image_dir, image)

    if not image_path or not os.path.isfile(image_path):
        return jsonify({"Error": "Image not found!"}), 404
    
    conn.commit()
    cursor.close()
    conn.close()

    try:
        return send_file(image_path)
    except Exception as e:
        return jsonify({"Error": "Failed to send image"}), 500
    

# Reporting API

@App.route("/api/reports/add", methods=["POST"])
@utils.Wrappers.guard_api(addr_list)
@utils.Wrappers.logdata()
@utils.Wrappers.require_json_with_fields(["token", "resource_id", "type_of_report", "type_of_resource","additional_info"])
def PostReport():
    data = request.json
    token = data["token"]
    resource_id = data["resource_id"]
    type_of_report = data["type_of_report"].lower()
    type_of_resource = data["type_of_resource"].lower()
    additional_info = data["additional_info"]

    username = utils.GeneralUtils.GetUsernameFromToken(token)
    if not username:
        
        return jsonify({"Error": "Invalid token"}), 401
    
    cursor, conn = utils.GeneralUtils.InnitDB()

    cursor.execute("INSERT INTO reports(username,resource_id,type_of_report,type_of_resource,additional_info) VALUES (?,?,?,?,?)",(username,resource_id,type_of_report,type_of_resource,additional_info,))
    
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"Message": f"Successfully reported the resource"}), 200

# Check if IP is blocked
# Check for cooldown on IP
# Validate required parameters: token
# If user admin show reports else 404
@App.route("/api/reports/view", methods=["GET"])
@utils.Wrappers.guard_api(addr_list)
@utils.Wrappers.logdata()
@utils.Wrappers.require_query_params(["token"])
def ViewReports():
    data = request.args
    token = data["token"]

    cursor, conn = utils.GeneralUtils.InnitDB()

    user = cursor.execute("SELECT username,admin FROM users WHERE token=?", (token,)).fetchone()
    if not user:
        
        cursor.close()
        conn.close()
        return """<html lang="en"><head><title>404 Not Found</title>
<style>
  .imageye-selected {
    outline: 2px solid black !important;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.5) !important;
  }
</style></head><body><h1>Not Found</h1>
<p>The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again.</p>
</body></html>""", 404

    username = user[0]
    is_admin = user[1]
    if is_admin == 0:
        
        cursor.close()
        conn.close()
        return """<html lang="en"><head><title>404 Not Found</title>
<style>
  .imageye-selected {
    outline: 2px solid black !important;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.5) !important;
  }
</style></head><body><h1>Not Found</h1>
<p>The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again.</p>
</body></html>""", 404
    
    reports = cursor.execute("SELECT * FROM reports").fetchall()
    reports_list = []
    for report in reports:
        report_dict = {
            "id":report[0],
            "username":report[1],
            "resource_id":report[2],
            "type_of_report":report[3],
            "type_of_resource":report[4],
            "additional_info":report[5],
            "timestamp":report[6]
        }
        reports_list.append(report_dict)
    conn.commit()
    cursor.close()
    conn.close()


    return jsonify({"Message": "Success", "Reports": reports_list}), 200

# Administration of this website

# Check if ip is blocked
# Check if request is json
# Check if it has all parameters needed
# Check if the token is valid and admin
# Set account as banned
@App.route("/api/users/ban",methods=["POST"])
@utils.Wrappers.guard_api(addr_list)
@utils.Wrappers.logdata()
@utils.Wrappers.require_json_with_fields(["token","username"])
def BanApi():
    cursor, conn = utils.GeneralUtils.InnitDB()

    if cursor.execute("SELECT token FROM users WHERE token=? AND admin=1", (request.json.get("token"),)).fetchone() is None:
        
        return jsonify({"Error": "Token is invalid"}), 400

    cursor.execute("UPDATE users SET banned=1 WHERE username=?", (request.json.get("username"),))
    cursor.execute("UPDATE users SET token=? WHERE username=?", (utils.GeneralUtils.GenerateToken("banned-user","QERUDSFKRENDSFMUIJKGRFDYUJRFSJFDSJJSJHFHJDSJSJFDODIOFDOS"),request.json.get("username"),))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"Message": "Success"}), 200

# Check if ip is blocked
# Check if request is json
# Check if it has all parameters needed
# Check if the token is valid and admin
# Set account as unbanned
@App.route("/api/users/unban",methods=["POST"])
@utils.Wrappers.guard_api(addr_list)
@utils.Wrappers.logdata()
@utils.Wrappers.require_json_with_fields(["token","username"])
def UnBanApi():
    cursor, conn = utils.GeneralUtils.InnitDB()

    if cursor.execute("SELECT token FROM users WHERE token=? AND admin=1", (request.json.get("token"),)).fetchone() is None:
        
        return jsonify({"Error": "Token is invalid"}), 400

    cursor.execute("UPDATE users SET banned=0 WHERE username=?", (request.json.get("username"),))
    cursor.execute(f"UPDATE users SET token=? WHERE username=?", (utils.GeneralUtils.GenerateToken(request.json.get("username"),"QERUDSFKRENDSFMUIJKGRFDYUJRFSJFDSJJSJHFHJDSJSJFDODIOFDOS"),request.json.get("username"),))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"Message": "Success"}), 200


# Check if IP is blocked
# Check for cooldown on IP
# Validate required parameters: token
# If user admin show token else 404
@App.route("/api/admin/tokenact", methods=["GET"])
@utils.Wrappers.guard_api(addr_list)
@utils.Wrappers.logdata()
@utils.Wrappers.require_query_params(["token","username"])
def UsernameToToken():
    data = request.args
    token = data["token"]
    username2 = data["username"]

    cursor, conn = utils.GeneralUtils.InnitDB()

    user = cursor.execute("SELECT username,admin FROM users WHERE token=?", (token,)).fetchone()
    if not user:
        
        cursor.close()
        conn.close()
        return """<html lang="en"><head><title>404 Not Found</title>
<style>
  .imageye-selected {
    outline: 2px solid black !important;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.5) !important;
  }
</style></head><body><h1>Not Found</h1>
<p>The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again.</p>
</body></html>""", 404

    username = user[0]
    is_admin = user[1]
    if is_admin == 0:
        
        cursor.close()
        conn.close()
        return """<html lang="en"><head><title>404 Not Found</title>
<style>
  .imageye-selected {
    outline: 2px solid black !important;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.5) !important;
  }
</style></head><body><h1>Not Found</h1>
<p>The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again.</p>
</body></html>""", 404
    
    reports = cursor.execute("SELECT token FROM users WHERE username=?",(username2,)).fetchall()
    reports_list = []
    for report in reports:
        report_dict = {
            "token":report[0]
        }
        reports_list.append(report_dict)
    conn.commit()
    cursor.close()
    conn.close()


    return jsonify({"Message": "Success", "Tokens": reports_list}), 200

if configs["test"] == True:
    App.run("127.0.0.1",80,True)
else:
    from waitress import serve
    if configs["revproxy_8080"] == True:
        serve(App, host='0.0.0.0', port=8080)
    else:
        serve(App, host='0.0.0.0', port=80)
