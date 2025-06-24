
from flask import Blueprint, request, jsonify , current_app
import hashlib, time, requests

import json
import utils

user_bp = Blueprint('user', __name__)

configs = json.loads(open("config.json").read())

# Users api

# Check if ip is blocked
# Check if request is json
# Check if it has all parameters needed
# Check if there is already a user with that username
# Check if the given username respects all constraints: lenght of 25 , no spaces , no special char like 'forbidden_chars'
@user_bp.route("signup",methods=["POST"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
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
@user_bp.route("login",methods=["GET"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
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
@user_bp.route("view",methods=["GET"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
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
@user_bp.route("viewall",methods=["GET"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
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
@user_bp.route("tokendata",methods=["GET"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
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
@user_bp.route("delete",methods=["DELETE"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
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
@user_bp.route("modify",methods=["PATCH"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
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