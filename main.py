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
    timestamp TEXT NOT NULL,
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


conn.commit()
conn.close()

# App

App = flask.Flask(__name__,static_url_path="/static")

# Cooldown and shit
addr_list = {}

# Webpages

@App.route("/")
def LandingPage():
    if utils.GeneralUtils.IsIpBlocked(request.remote_addr):
        return "<h1>This ip address is permanently blocked off this site!<h1/>",400

    utils.GeneralUtils.TrackIp(None,True,request.path,request.remote_addr)
    return open("pages/landing.html").read()

# Users api

# Sign-up endpoint

# Check if ip is blocked
# Check if request is json
# Check if it has all parameters needed
# Check if there is already a user with that username
# Check if the given username respects all constraints: lenght of 25 , no spaces , no special char like 'forbidden_chars'

# TODO: Login function with all contstarints , View user function , Delete user function
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
        return jsonify({"Error":"This request idoes not have either a 'username' or 'password'"}),400
    
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
        request.json.get("username"),
        request.json.get("username"),
        hashed_password,
        str(time.time()),
        token
    ))

    
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"Message":"Success","Token":token}),200
    
App.run(port=80)