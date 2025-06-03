# Open source anti-furry forums code made by Andreiplsno
# *idk why i made this open source*

import flask
from flask import request,jsonify

import sqlite3
import hashlib
import time

import utils.Wrappers
import utils.GeneralUtils


# Innit Database

conn = sqlite3.connect("forum.db")

conn.execute("""CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(100) NOT NULL,
    display_name VARCHAR(150) NOT NULL,
    bio TEXT,
    encrypted_password TEXT NOT NULL,
    admin TINYINT(1) NOT NULL DEFAULT 0,
    banned TINYINT(1) NOT NULL DEFAULT 0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    token TEXT NOT NULL
);""")

conn.execute("""CREATE TABLE IF NOT EXISTS ip_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usr_name TEXT,
    success TINYINT(1) NOT NULL DEFAULT 0,
    path TEXT NOT NULL,
    ip TEXT NOT NULL,
    timestamp TEXT NOT NULL
);""")

conn.execute("""CREATE TABLE IF NOT EXISTS blocked_ip (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip TEXT NOT NULL,
    blocked TINYINT(1) NOT NULL DEFAULT 0
);""")

conn.execute("""CREATE TABLE IF NOT EXISTS threads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_username TEXT NOT NULL,
    name VARCHAR(200) NOT NULL,
    identifier VARCHAR(150) NOT NULL,
    description TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    image_url TEXT DEFAULT '/static/AFLOGO.png'
);""")

conn.execute("""CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_username TEXT NOT NULL,
    thread_identifier TEXT NOT NULL,
    title VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    image_attachment TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""")

conn.execute("""CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_username TEXT NOT NULL,
    post_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""")

conn.execute("""
CREATE TABLE IF NOT EXISTS subscribed_threads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    thread_identifier TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

conn.execute("""
CREATE TABLE IF NOT EXISTS liked_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    post_id TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

conn.execute("""
CREATE TABLE IF NOT EXISTS liked_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    comment_id TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

conn.commit()
conn.close()

# App

# TODO make frontend for all ts
# TODO add functions for reporting
# TODO add functions for ban/moderation (admin only)
# TODO add a feed page (or more)
# TODO add an algorithm for showing posts you may like
# TODO add a search page for posts

App = flask.Flask(__name__,static_url_path="/static")

# Cooldown and shit
addr_list = {}

# Webpages

@App.route("/")
def LandingPage():
    if utils.GeneralUtils.IsIpBlocked(request.remote_addr):
        return open("pages/blocked.html").read(),403

    utils.GeneralUtils.TrackIp(None,True,request.path,request.remote_addr)
    return open("pages/landing.html").read()

@App.route("/login")
def LoginPage():
    if utils.GeneralUtils.IsIpBlocked(request.remote_addr):
        return open("pages/blocked.html").read(),403

    utils.GeneralUtils.TrackIp(None,True,request.path,request.remote_addr)
    return open("pages/login.html").read()

@App.route("/view/users/<username>")
def ViewUserPage(username):
    if utils.GeneralUtils.IsIpBlocked(request.remote_addr):
        return open("pages/blocked.html").read(),403

    utils.GeneralUtils.TrackIp(None,True,request.path,request.remote_addr)
    return flask.render_template_string(open("pages/view_username.html").read(),username=username)

@App.route("/view/@me")
def ViewMyselfPage():
    if utils.GeneralUtils.IsIpBlocked(request.remote_addr):
        return open("pages/blocked.html").read(),403

    utils.GeneralUtils.TrackIp(None,True,request.path,request.remote_addr)
    return open("pages/view_me.html").read()

@App.route("/view/threads/<thread>")
def ViewThreadPage(thread):
    if utils.GeneralUtils.IsIpBlocked(request.remote_addr):
        return open("pages/blocked.html").read(),403

    utils.GeneralUtils.TrackIp(None,True,request.path,request.remote_addr)
    return flask.render_template_string(open("pages/view_thread.html").read(),thread=thread)

# Users api

# Check if ip is blocked
# Check if request is json
# Check if it has all parameters needed
# Check if there is already a user with that username
# Check if the given username respects all constraints: lenght of 25 , no spaces , no special char like 'forbidden_chars'
@App.route("/api/signup",methods=["POST"])
@utils.Wrappers.guard_api(addr_list)
@utils.Wrappers.require_json_with_fields(["username","password"])
def SignupApi():
    forbidden_chars = {" ", "#", "@", "$", "%", "^", "&", "*", "(", ")", "-", "=", "+", "<", ">", "[", "]"}

    if not request.is_json:
        utils.GeneralUtils.TrackIp(None,False,request.path,request.remote_addr)
        return jsonify({"Error":"This request is not identified as JSON"}),400
    
    cursor,conn = utils.GeneralUtils.InnitDB()

    if not (cursor.execute("SELECT username FROM users WHERE username=?",(request.json.get("username"),)).fetchone() == None):
        utils.GeneralUtils.TrackIp(None,False,request.path,request.remote_addr)
        return jsonify({"Error":"Username already used"}),400
    
    if not request.json.get("username") or len(request.json.get("username")) >= 25 or any(char in forbidden_chars for char in request.json.get("username")):
        utils.GeneralUtils.TrackIp(None,False,request.path,request.remote_addr)
        return jsonify({"Error":"Username dosen't repsect constrains"}),400

    utils.GeneralUtils.TrackIp(request.json.get("username"),True,request.path,request.remote_addr)

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

    utils.GeneralUtils.TrackIp(request.args.get("username"),True,request.path,request.remote_addr)

    return jsonify({"Message":"Success","Token":token}),200

# Check if ip is blocked
# Check if it has all parameters needed
# Check if there is a user with that username
# Check if the password is correct
# Return token
@App.route("/api/login",methods=["GET"])
@utils.Wrappers.guard_api(addr_list)
@utils.Wrappers.require_query_params(["username","password"])
def LoginApi():
    cursor,conn = utils.GeneralUtils.InnitDB()

    if (cursor.execute("SELECT username FROM users WHERE username=?",(request.args.get("username").lower(),)).fetchone() == None):
        utils.GeneralUtils.TrackIp(None,False,request.path,request.remote_addr)
        return jsonify({"Error":"No user with such username"}),400
    
    enc_pass = hashlib.sha256()
    enc_pass.update(request.args.get("password").encode())
    enc_pass = enc_pass.hexdigest()

    row = cursor.execute("SELECT encrypted_password FROM users WHERE username=?", (request.args.get("username").lower(),)).fetchone()
    if not row or row[0] != enc_pass:
        utils.GeneralUtils.TrackIp(None, False, request.path, request.remote_addr)
        return jsonify({"Error": "Invalid password"}), 400
    
    token = cursor.execute("SELECT token FROM users WHERE username=?", (request.args.get("username").lower(),)).fetchone()[0]
    
    conn.commit()
    cursor.close()
    conn.close()

    utils.GeneralUtils.TrackIp(request.args.get("username"),True,request.path,request.remote_addr)

    return jsonify({"Message":"Success","Token":token}),200

# Check if ip is blocked
# Check if it has all parameters needed
# Check if the token is valid
# Get user parameters from given user and if it returns None then display No user found
@App.route("/api/users/view",methods=["GET"])
@utils.Wrappers.guard_api(addr_list)
@utils.Wrappers.require_query_params(["username","token"])
def UserViewApi():
    cursor,conn = utils.GeneralUtils.InnitDB()

    if (cursor.execute("SELECT token FROM users WHERE token=?",(request.args.get("token"),)).fetchone() == None):
        # OPTIMIZATION TODO: Make this get the username from token then check token validity
        utils.GeneralUtils.TrackIp(None,False,request.path,request.remote_addr)
        return jsonify({"Error":"Token is invalid"}),400
    
    user = cursor.execute("SELECT username,display_name,bio,timestamp,admin,id FROM users WHERE username=?",(request.args.get("username").lower(),)).fetchone()
    user_obj = {}

    if user == None:
        user_obj = {"Message":"No user found!"}
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

    utils.GeneralUtils.TrackIp(utils.GeneralUtils.GetUsernameFromToken(request.args.get("token")),True,request.path,request.remote_addr)

    return jsonify({"User":user_obj}),200

# Check if ip is blocked
# Check if it has all parameters needed
# Check if the token is valid
# Get params from user with set token
@App.route("/api/users/tokendata",methods=["GET"])
@utils.Wrappers.guard_api(addr_list)
@utils.Wrappers.require_query_params(["token"])
def TokenViewApi():
    
    cursor,conn = utils.GeneralUtils.InnitDB()

    if (cursor.execute("SELECT token FROM users WHERE token=?",(request.args.get("token"),)).fetchone() == None):
        # OPTIMIZATION TODO: Make this get the username from token then check token validity
        utils.GeneralUtils.TrackIp(None,False,request.path,request.remote_addr)
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

    utils.GeneralUtils.TrackIp(utils.GeneralUtils.GetUsernameFromToken(request.args.get("token")),True,request.path,request.remote_addr)

    return jsonify({"User":user_obj}),200

# Check if ip is blocked
# Check if request is json
# Check if it has all parameters needed
# Check if the token is valid
# Delete user with given token
@App.route("/api/users/delete",methods=["DELETE"])
@utils.Wrappers.guard_api(addr_list)
@utils.Wrappers.require_json_with_fields(["token"])
def UserDeleteApi():
    cursor,conn = utils.GeneralUtils.InnitDB()

    if (cursor.execute("SELECT token FROM users WHERE token=?",(request.json.get("token"),)).fetchone() == None):
        # OPTIMIZATION TODO: Make this get the username from token then check token validity
        utils.GeneralUtils.TrackIp(None,False,request.path,request.remote_addr)
        return jsonify({"Error":"Token is invalid"}),400
    
    # OPTIMIZATION TODO: Make this get the username from token to delete easier
    cursor.execute("DELETE FROM users WHERE token=?",(request.json.get("token"),))
    
    conn.commit()
    cursor.close()
    conn.close()

    utils.GeneralUtils.TrackIp(utils.GeneralUtils.GetUsernameFromToken(request.json.get("token")),True,request.path,request.remote_addr)

    return jsonify({"Message":"Success"}),200

# Check if ip is blocked
# Check if request is json
# Check if it has all parameters needed
# Check if the token is valid
# Check constraints
# Patch to all params needed
@App.route("/api/users/modify",methods=["PATCH"])
@utils.Wrappers.guard_api(addr_list)
@utils.Wrappers.require_json_with_fields(["token","display_name","bio"])
def UserModifyApi():
    forbidden_chars = {" ", "#", "@", "$", "%", "^", "&", "*", "(", ")", "-", "=", "+", "<", ">", "[", "]"}
    display_forbidden_chars = {"#", "@", "$", "%", "^", "&", "*", "(", ")", "-", "=", "+", "<", ">"}
    
    if not request.json.get("display_name") or len(request.json.get("display_name")) >= 40 or any(char in display_forbidden_chars for char in request.json.get("display_name")):
        utils.GeneralUtils.TrackIp(None,False,request.path,request.remote_addr)
        return jsonify({"Error":"Display name dosen't repsect constrains"}),400
    
    if not request.json.get("bio") or len(request.json.get("bio")) > 200:
        utils.GeneralUtils.TrackIp(None,False,request.path,request.remote_addr)
        return jsonify({"Error":"Bio dosen't repsect constrains"}),400
    
    cursor,conn = utils.GeneralUtils.InnitDB()

    if (cursor.execute("SELECT token FROM users WHERE token=?",(request.json.get("token"),)).fetchone() == None):
        # OPTIMIZATION TODO: Make this get the username from token then check token validity
        utils.GeneralUtils.TrackIp(None,False,request.path,request.remote_addr)
        return jsonify({"Error":"Token is invalid"}),400
    
    # OPTIMIZATION TODO: Make this get the username from token to delete easier
    cursor.execute("UPDATE users SET display_name=?, bio=? WHERE token=?",(request.json.get("display_name"),request.json.get("bio"),request.json.get("token"),))
    
    conn.commit()
    cursor.close()
    conn.close()

    utils.GeneralUtils.TrackIp(utils.GeneralUtils.GetUsernameFromToken(request.json.get("token")),True,request.path,request.remote_addr)

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
        utils.GeneralUtils.TrackIp(None, False, request.path, request.remote_addr)
        return jsonify({"Error": "Request doesn't respect constraints"}), 400

    cursor, conn = utils.GeneralUtils.InnitDB()

    user = cursor.execute("SELECT id FROM users WHERE token=?", (data["token"],)).fetchone()
    if not user:
        utils.GeneralUtils.TrackIp(None, False, request.path, request.remote_addr)
        return jsonify({"Error": "Token is invalid"}), 401

    if cursor.execute("SELECT identifier FROM threads WHERE identifier=?", (identifier,)).fetchone():
        utils.GeneralUtils.TrackIp(None, False, request.path, request.remote_addr)
        return jsonify({"Error": "Identifier already used"}), 400

    username = utils.GeneralUtils.GetUsernameFromToken(data["token"])
    cursor.execute(
        "INSERT INTO threads(owner_username, name, identifier, description) VALUES (?, ?, ?, ?)",
        (username, name, identifier, description)
    )

    conn.commit()
    cursor.close()
    conn.close()

    utils.GeneralUtils.TrackIp(utils.GeneralUtils.GetUsernameFromToken(data["token"]), True, request.path, request.remote_addr)

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
@utils.Wrappers.require_query_params(["token", "search"])
def ViewThreads():
    data = request.args
    token = data["token"]
    search = data["search"].lower() == "true"

    cursor, conn = utils.GeneralUtils.InnitDB()

    user = cursor.execute("SELECT username FROM users WHERE token=?", (token,)).fetchone()
    if not user:
        utils.GeneralUtils.TrackIp(None, False, request.path, request.remote_addr)
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

    utils.GeneralUtils.TrackIp(utils.GeneralUtils.GetUsernameFromToken(data["token"]), True, request.path, request.remote_addr)

    return jsonify({"Message": "Success", "Threads": thread_list}), 200

# Check if ip is blocked
# Check if request is JSON
# Check if it has all parameters needed
# Validate token and ownership
# Delete thread if it exists and belongs to user
@App.route("/api/thread/delete", methods=["DELETE"])
@utils.Wrappers.guard_api(addr_list)
@utils.Wrappers.require_json_with_fields([["token", "identifier"]])
def DeleteThread():
    data = request.json
    token = data["token"]
    identifier = data["identifier"]

    cursor, conn = utils.GeneralUtils.InnitDB()

    username = utils.GeneralUtils.GetUsernameFromToken(token)
    if not username:
        utils.GeneralUtils.TrackIp(None, False, request.path, request.remote_addr)
        cursor.close()
        conn.close()
        return jsonify({"Error": "Invalid token"}), 401

    thread = cursor.execute(
        "SELECT * FROM threads WHERE identifier=? AND owner_username=?", (identifier, username)
    ).fetchone()

    if not thread:
        utils.GeneralUtils.TrackIp(username, False, request.path, request.remote_addr)
        cursor.close()
        conn.close()
        return jsonify({"Error": "Thread not found or not owned by user"}), 404

    cursor.execute("DELETE FROM threads WHERE identifier=? AND owner_username=?", (identifier, username))

    conn.commit()
    cursor.close()
    conn.close()

    utils.GeneralUtils.TrackIp(username, True, request.path, request.remote_addr)

    return jsonify({"Message": "Thread successfully deleted"}), 200

# Check if IP is blocked
# Check if request is JSON
# Check if all parameters exist
# Validate token and user
# Subscribe or unsubscribe based on action
@App.route("/api/thread/subscribe", methods=["POST"])
@utils.Wrappers.guard_api(addr_list)
@utils.Wrappers.require_json_with_fields(["token", "identifier", "action"])
def SubscribeThread():
    data = request.json
    token = data["token"]
    identifier = data["identifier"]
    action = data["action"].lower()

    username = utils.GeneralUtils.GetUsernameFromToken(token)
    if not username:
        utils.GeneralUtils.TrackIp(None, False, request.path, request.remote_addr)
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
    utils.GeneralUtils.TrackIp(username, True, request.path, request.remote_addr)

    return jsonify({"Message": f"Successfully {action}d to thread"}), 200


# List all threads that the user is subscribed to
# Check if IP is blocked
# Check if token parameter is provided
# Validate token and get username
# Query subscribed threads for the user
# Return the list of subscribed thread identifiers
@App.route("/api/thread/subscriptions", methods=["GET"])
@utils.Wrappers.guard_api(addr_list)
@utils.Wrappers.require_query_params(["token"])
def ListUserSubscriptions():
    data = request.args
    token = data["token"]

    cursor, conn = utils.GeneralUtils.InnitDB()

    user = cursor.execute("SELECT username FROM users WHERE token=?", (token,)).fetchone()
    if not user:
        utils.GeneralUtils.TrackIp(None, False, request.path, request.remote_addr)
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
    
    utils.GeneralUtils.TrackIp(utils.GeneralUtils.GetUsernameFromToken(data["token"]), True, request.path, request.remote_addr)

    return jsonify({"Message": "Success", "SubscribedThreads": subscriptions}), 200

# Post api

# Check if ip is blocked
# Check if request is json
# Check if it has all parameters needed
# Check if the params are all valid
# Insert into db
@App.route("/api/post/post", methods=["POST"])
@utils.Wrappers.guard_api(addr_list)
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
        utils.GeneralUtils.TrackIp(None, False, request.path, request.remote_addr)
        return jsonify({"Error": "Request doesn't respect constraints"}), 400

    cursor, conn = utils.GeneralUtils.InnitDB()

    user = cursor.execute("SELECT id FROM users WHERE token=?", (data["token"],)).fetchone()
    if not user:
        utils.GeneralUtils.TrackIp(None, False, request.path, request.remote_addr)
        return jsonify({"Error": "Token is invalid"}), 401
    
    if not cursor.execute("SELECT identifier FROM threads WHERE identifier=?", (thread_identifier,)).fetchone():
        utils.GeneralUtils.TrackIp(None, False, request.path, request.remote_addr)
        return jsonify({"Error": "No such thread with this identifier!"}), 400

    username = utils.GeneralUtils.GetUsernameFromToken(data["token"])
    cursor.execute(
        "INSERT INTO posts(owner_username,thread_identifier,content,title) VALUES (?, ?, ?, ?)",
        (username,thread_identifier,content,title)
    )

    conn.commit()
    cursor.close()
    conn.close()

    utils.GeneralUtils.TrackIp(utils.GeneralUtils.GetUsernameFromToken(data["token"]), True, request.path, request.remote_addr)

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
@utils.Wrappers.require_query_params(["token", "search"])
def ViewPosts():
    data = request.args
    token = data["token"]
    search = data["search"].lower() == "true"

    cursor, conn = utils.GeneralUtils.InnitDB()

    user = cursor.execute("SELECT username FROM users WHERE token=?", (token,)).fetchone()
    if not user:
        utils.GeneralUtils.TrackIp(None, False, request.path, request.remote_addr)
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
        "SELECT id FROM liked_posts WHERE username = ?", (username,)
    ).fetchall()]

    post_list = []
    for post in posts:
        is_liked = post[0] in liked
        
        post_dict = {
            "id": post[0],
            "owner_username": post[1],
            "post_identifier": post[2],
            "title": post[3],
            "content": post[4],
            "image_attachment": post[5],
            "liked": is_liked,
            "timestamp": post[6],
        }
        post_list.append(post_dict)
    conn.commit()
    cursor.close()
    conn.close()

    utils.GeneralUtils.TrackIp(utils.GeneralUtils.GetUsernameFromToken(data["token"]), True, request.path, request.remote_addr)

    return jsonify({"Message": "Success", "Posts": post_list}), 200

# Check if ip is blocked
# Check if request is JSON
# Check if it has all parameters needed
# Validate token and ownership
# Delete post if it exists and belongs to user
@App.route("/api/posts/delete", methods=["DELETE"])
@utils.Wrappers.guard_api(addr_list)
@utils.Wrappers.require_json_with_fields(["token", "id"])
def DeletePost():
    data = request.json
    token = data["token"]
    id = data["id"]

    cursor, conn = utils.GeneralUtils.InnitDB()

    username = utils.GeneralUtils.GetUsernameFromToken(token)
    if not username:
        utils.GeneralUtils.TrackIp(None, False, request.path, request.remote_addr)
        cursor.close()
        conn.close()
        return jsonify({"Error": "Invalid token"}), 401

    post = cursor.execute(
        "SELECT * FROM posts WHERE id=? AND owner_username=?", (id, username)
    ).fetchone()

    if not post:
        utils.GeneralUtils.TrackIp(username, False, request.path, request.remote_addr)
        cursor.close()
        conn.close()
        return jsonify({"Error": "Post not found or not owned by user"}), 404

    cursor.execute("DELETE FROM posts WHERE id=? AND owner_username=?", (id, username))

    conn.commit()
    cursor.close()
    conn.close()

    utils.GeneralUtils.TrackIp(username, True, request.path, request.remote_addr)

    return jsonify({"Message": "Post successfully deleted"}), 200


# Check if IP is blocked
# Check if request is JSON
# Check if all parameters exist
# Validate token and user
# Like or unlike based on action
@App.route("/api/posts/like", methods=["POST"])
@utils.Wrappers.guard_api(addr_list)
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
        utils.GeneralUtils.TrackIp(None, False, request.path, request.remote_addr)
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
            "DELETE FROM liked_posts WHERE username=? AND id=?",
            (username, id)
        )
        conn.commit()

    else:
        cursor.close()
        conn.close()
        return jsonify({"Error": "Action must be either 'like' or 'unlike'"}), 400

    cursor.close()
    conn.close()
    utils.GeneralUtils.TrackIp(username, True, request.path, request.remote_addr)

    return jsonify({"Message": f"Successfully {action}d the post"}), 200

# Comments api

# Check if ip is blocked
# Check if request is json
# Check if it has all parameters needed
# Check if the params are all valid
# Insert into db
@App.route("/api/comment/post", methods=["POST"])
@utils.Wrappers.guard_api(addr_list)
@utils.Wrappers.require_json_with_fields(["content","token","post_id"])
def MakeComment():
    data = request.json

    content = data["content"]
    post_id = data["post_id"]

    if (
        len(content) >= 100
    ):
        utils.GeneralUtils.TrackIp(None, False, request.path, request.remote_addr)
        return jsonify({"Error": "Request doesn't respect constraints"}), 400

    cursor, conn = utils.GeneralUtils.InnitDB()

    user = cursor.execute("SELECT id FROM users WHERE token=?", (data["token"],)).fetchone()
    if not user:
        utils.GeneralUtils.TrackIp(None, False, request.path, request.remote_addr)
        return jsonify({"Error": "Token is invalid"}), 401
    
    if not cursor.execute("SELECT id FROM posts WHERE id=?", (post_id,)).fetchone():
        utils.GeneralUtils.TrackIp(None, False, request.path, request.remote_addr)
        return jsonify({"Error": "No such post with this id!"}), 400

    username = utils.GeneralUtils.GetUsernameFromToken(data["token"])
    cursor.execute(
        "INSERT INTO comments(owner_username,post_id,content) VALUES (?, ?, ?)",
        (username,post_id,content)
    )

    conn.commit()
    cursor.close()
    conn.close()

    utils.GeneralUtils.TrackIp(utils.GeneralUtils.GetUsernameFromToken(data["token"]), True, request.path, request.remote_addr)

    return jsonify({"Message": "Success"}), 200

# Check if IP is blocked
# Check for cooldown on IP
# Validate required parameters: token, post_id
# Validate token and get username
# Get user's liked comments
# Add 'liked' flag to each comment in response
@App.route("/api/comments/view", methods=["GET"])
@utils.Wrappers.guard_api(addr_list)
@utils.Wrappers.require_query_params(["token","post_id"])
def ViewComments():
    data = request.args
    token = data["token"]
    post_id = data["post_id"]

    cursor, conn = utils.GeneralUtils.InnitDB()

    user = cursor.execute("SELECT username FROM users WHERE token=?", (token,)).fetchone()
    if not user:
        utils.GeneralUtils.TrackIp(None, False, request.path, request.remote_addr)
        cursor.close()
        conn.close()
        return jsonify({"Error": "Token is invalid"}), 400

    username = user[0]

    comments = cursor.execute("SELECT * FROM comments WHERE post_id=?",post_id).fetchall()

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

    utils.GeneralUtils.TrackIp(utils.GeneralUtils.GetUsernameFromToken(data["token"]), True, request.path, request.remote_addr)

    return jsonify({"Message": "Success", "Comments": comments_list}), 200

# Check if ip is blocked
# Check if request is JSON
# Check if it has all parameters needed
# Validate token and ownership
# Delete post if it exists and belongs to user
@App.route("/api/comments/delete", methods=["DELETE"])
@utils.Wrappers.guard_api(addr_list)
@utils.Wrappers.require_json_with_fields(["token", "id"])
def DeleteComment():
    data = request.json
    token = data["token"]
    id = data["id"]

    cursor, conn = utils.GeneralUtils.InnitDB()

    username = utils.GeneralUtils.GetUsernameFromToken(token)
    if not username:
        utils.GeneralUtils.TrackIp(None, False, request.path, request.remote_addr)
        cursor.close()
        conn.close()
        return jsonify({"Error": "Invalid token"}), 401

    post = cursor.execute(
        "SELECT * FROM comments WHERE id=? AND owner_username=?", (id, username)
    ).fetchone()

    if not post:
        utils.GeneralUtils.TrackIp(username, False, request.path, request.remote_addr)
        cursor.close()
        conn.close()
        return jsonify({"Error": "Comment not found or not owned by user"}), 404

    cursor.execute("DELETE FROM comments WHERE id=? AND owner_username=?", (id, username))

    conn.commit()
    cursor.close()
    conn.close()

    utils.GeneralUtils.TrackIp(username, True, request.path, request.remote_addr)

    return jsonify({"Message": "Comment successfully deleted"}), 200


# Check if IP is blocked
# Check if request is JSON
# Check if all parameters exist
# Validate token and user
# Like or unlike based on action
@App.route("/api/comments/like", methods=["POST"])
@utils.Wrappers.guard_api(addr_list)
@utils.Wrappers.require_json_with_fields(["token", "id", "action"])
def LikeComment():
    data = request.json
    token = data["token"]
    id = data["id"]
    action = data["action"].lower()

    username = utils.GeneralUtils.GetUsernameFromToken(token)
    cursor, conn = utils.GeneralUtils.InnitDB()

    user = cursor.execute("SELECT username FROM users WHERE token=?", (token,)).fetchone()
    if not user:
        utils.GeneralUtils.TrackIp(None, False, request.path, request.remote_addr)
        cursor.close()
        conn.close()
        return jsonify({"Error": "Token is invalid"}), 400

    thread_exists = cursor.execute("SELECT 1 FROM comments WHERE id=?", (id,)).fetchone()
    if not thread_exists:
        cursor.close()
        conn.close()
        return jsonify({"Error": "Comment does not exist"}), 404

    if action == "like":
        existing = cursor.execute(
            "SELECT 1 FROM liked_comments WHERE username=? AND comment_id=?",
            (username.lower(), id)
        ).fetchone()

        if existing:
            cursor.close()
            conn.close()
            return jsonify({"Error": "Already liked"}), 400

        cursor.execute(
            "INSERT INTO liked_comments(username, comment_id) VALUES (?, ?)",
            (username, id)
        )
        conn.commit()

    elif action == "unlike":
        cursor.execute(
            "DELETE FROM liked_comments WHERE username=? AND comment_id=?",
            (username, id)
        )
        conn.commit()

    else:
        cursor.close()
        conn.close()
        return jsonify({"Error": "Action must be either 'like' or 'unlike'"}), 400

    cursor.close()
    conn.close()
    utils.GeneralUtils.TrackIp(username, True, request.path, request.remote_addr)

    return jsonify({"Message": f"Successfully {action}d the comment"}), 200

App.run(port=80)
