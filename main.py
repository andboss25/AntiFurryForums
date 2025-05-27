# Open source anti-furry forums code made by Andreiplsno
# *idk why i made this open source*

import flask
import sqlite3
import hashlib
import time
import utils.GeneralUtils

from flask import request,jsonify

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
    owner_id INTEGER NOT NULL,
    name VARCHAR(200) NOT NULL,
    identifier VARCHAR(150) NOT NULL,
    description TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    image_url TEXT DEFAULT '/static/AFLOGO.png'
);""")

conn.execute("""CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL,
    thread_id INTEGER NOT NULL,
    title VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    image_attachment TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""")

conn.execute("""CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL,
    post_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""")

conn.commit()
conn.close()

# App

# TODO add functions for making all
# TODO add functions for reading all
# TODO add functions for deleting all
# TODO add functions for likeing/subscribing to them all
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

# Users api

# Check if ip is blocked
# Check if request is json
# Check if it has all parameters needed
# Check if there is already a user with that username
# Check if the given username respects all constraints: lenght of 25 , no spaces , no special char like 'forbidden_chars'
@App.route("/api/signup",methods=["POST"])
def SignupApi():
    if utils.GeneralUtils.IsIpBlocked(request.remote_addr):
        return jsonify({"Error":"This ip address has been permanently blocked off this site!"}),400
    
    if utils.GeneralUtils.CooldownCheck(request.remote_addr,addr_list):
        return jsonify({"Error":"Temporary cooldown becuse of too many requests!"}),400
    
    forbidden_chars = {" ", "#", "@", "$", "%", "^", "&", "*", "(", ")", "-", "=", "+", "<", ">", "[", "]"}

    if not request.is_json:
        utils.GeneralUtils.TrackIp(None,False,request.path,request.remote_addr)
        return jsonify({"Error":"This request is not identified as JSON"}),400
    
    if not request.json.get("username") or not request.json.get("password"):
        utils.GeneralUtils.TrackIp(None,False,request.path,request.remote_addr)
        return jsonify({"Error":"This request does not have either a 'username' or 'password'"}),400
    
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
def LoginApi():
    if utils.GeneralUtils.IsIpBlocked(request.remote_addr):
        return jsonify({"Error":"This ip address has been permanently blocked off this site!"}),400
    
    if utils.GeneralUtils.CooldownCheck(request.remote_addr,addr_list):
        return jsonify({"Error":"Temporary cooldown becuse of too many requests!"}),400
    
    if not request.args.get("username") or not request.args.get("password"):
        utils.GeneralUtils.TrackIp(None,False,request.path,request.remote_addr)
        return jsonify({"Error":"This request does not have either a 'username' or 'password'"}),400
    
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
def UserViewApi():
    if utils.GeneralUtils.IsIpBlocked(request.remote_addr):
        return jsonify({"Error":"This ip address has been permanently blocked off this site!"}),400
    
    if utils.GeneralUtils.CooldownCheck(request.remote_addr,addr_list):
        return jsonify({"Error":"Temporary cooldown becuse of too many requests!"}),400
    
    if not request.args.get("token") or not request.args.get("username"):
        utils.GeneralUtils.TrackIp(None,False,request.path,request.remote_addr)
        return jsonify({"Error":"This request does not have either a 'token' or 'username'"}),400
    
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
def TokenViewApi():
    if utils.GeneralUtils.IsIpBlocked(request.remote_addr):
        return jsonify({"Error":"This ip address has been permanently blocked off this site!"}),400
    
    if utils.GeneralUtils.CooldownCheck(request.remote_addr,addr_list):
        return jsonify({"Error":"Temporary cooldown becuse of too many requests!"}),400
    
    if not request.args.get("token"):
        utils.GeneralUtils.TrackIp(None,False,request.path,request.remote_addr)
        return jsonify({"Error":"This request does not have a token"}),401
    
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
def UserDeleteApi():
    if utils.GeneralUtils.IsIpBlocked(request.remote_addr):
        return jsonify({"Error":"This ip address has been permanently blocked off this site!"}),400
    
    if utils.GeneralUtils.CooldownCheck(request.remote_addr,addr_list):
        return jsonify({"Error":"Temporary cooldown becuse of too many requests!"}),400
    
    if not request.is_json:
        utils.GeneralUtils.TrackIp(None,False,request.path,request.remote_addr)
        return jsonify({"Error":"This request is not identified as JSON"}),400
    
    if not request.json.get("token"):
        utils.GeneralUtils.TrackIp(None,False,request.path,request.remote_addr)
        return jsonify({"Error":"This request does not have a token"}),401
    
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
def UserModifyApi():
    if utils.GeneralUtils.IsIpBlocked(request.remote_addr):
        return jsonify({"Error":"This ip address has been permanently blocked off this site!"}),400
    
    if utils.GeneralUtils.CooldownCheck(request.remote_addr,addr_list):
        return jsonify({"Error":"Temporary cooldown becuse of too many requests!"}),400
    
    if not request.is_json:
        utils.GeneralUtils.TrackIp(None,False,request.path,request.remote_addr)
        return jsonify({"Error":"This request is not identified as JSON"}),400
    
    if not request.json.get("token") or not request.json.get("display_name") or not request.json.get("bio"):
        utils.GeneralUtils.TrackIp(None,False,request.path,request.remote_addr)
        return jsonify({"Error":"Does not have all params needed!"}),400
    
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

# Thread->Post->Comment api

# Check if ip is blocked
# Check if request is json
# Check if it has all parameters needed
# Check if identifier name is already used
# Check if the params are all valid
@App.route("/api/thread/post", methods=["POST"])
def MakeThread():
    if utils.GeneralUtils.IsIpBlocked(request.remote_addr):
        return jsonify({"Error": "This IP address has been permanently blocked off this site!"}), 400

    if utils.GeneralUtils.CooldownCheck(request.remote_addr, addr_list):
        return jsonify({"Error": "Temporary cooldown because of too many requests!"}), 400

    forbidden_chars = {" ", "#", "@", "$", "%", "^", "&", "*", "(", ")", "-", "=", "+", "<", ">", "[", "]"}

    if not request.is_json:
        utils.GeneralUtils.TrackIp(None, False, request.path, request.remote_addr)
        return jsonify({"Error": "This request is not identified as JSON"}), 400

    data = request.json
    required_fields = ["name", "description", "token", "identifier"]
    if not all(field in data and data[field] for field in required_fields):
        utils.GeneralUtils.TrackIp(None, False, request.path, request.remote_addr)
        return jsonify({"Error": "Missing one or more required fields: name, description, token, identifier"}), 400

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

    user_id = user[0]
    cursor.execute(
        "INSERT INTO threads(owner_id, name, identifier, description) VALUES (?, ?, ?, ?)",
        (user_id, name, identifier, description)
    )

    conn.commit()
    cursor.close()
    conn.close()

    utils.GeneralUtils.TrackIp(utils.GeneralUtils.GetUsernameFromToken(data["token"]), True, request.path, request.remote_addr)

    return jsonify({"Message": "Success"}), 200

App.run(port=80)
