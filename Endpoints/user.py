from flask import Blueprint, request, jsonify, current_app, render_template, redirect, make_response
import hashlib, time, requests
import json
import utils
import utils.Captcha
import utils.Email
import utils.GeneralUtils

user_bp = Blueprint('user', __name__)

configs = json.loads(open("config.json").read())

IP_ACCOUNT_COUNTER = {}

# Users api

@user_bp.route("signup", methods=["POST"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
@utils.Wrappers.logdata()
@utils.Wrappers.require_form_params(["username", "email" ,"password", "recaptcha_token"])
def SignupApi():
    forbidden_chars = {" ", "#", "@", "$", "%", "^", "&", "*", "(", ")", "-", "=", "+", "<", ">", "[", "]","'",'"',"/","\\"}

    recaptcha_token = request.form.get("recaptcha_token")
    recaptcha_ok = utils.Captcha.VerifyRecaptcha(recaptcha_token)
    if not recaptcha_ok:
        return jsonify({"Error": "Failed reCAPTCHA verification"}), 403

    cursor, conn = utils.GeneralUtils.InnitDB()

    username = request.form.get("username")
    email = request.form.get("email")

    if request.remote_addr == "127.0.0.1":
        ip = request.headers.get("X-Real-IP")
    else:
        ip = request.remote_addr or "localhost"

    ip_account_count = IP_ACCOUNT_COUNTER.get(ip, 0)
    if ip_account_count >= 3:
        return render_template("pages/login.html", re_site=configs['re_captcha_site_key'],error_message='Too many accounts created from this IP address',message_color='red')

    if cursor.execute("SELECT username FROM users WHERE username=?", (username,)).fetchone() is not None:
        return render_template("pages/login.html", re_site=configs['re_captcha_site_key'],error_message='Username already used',message_color='red')

    if cursor.execute("SELECT username FROM users WHERE email=?", (email,)).fetchone() is not None:
        return render_template("pages/login.html", re_site=configs['re_captcha_site_key'],error_message='Email already used',message_color='red')

    if not username or len(username) >= 25 or any(char in forbidden_chars for char in username):
        return render_template("pages/login.html", re_site=configs['re_captcha_site_key'],error_message="Username doesn't respect constraints",message_color='red')

    hash_pass = hashlib.sha256()
    hash_pass.update(request.form.get("password").encode())
    hashed_password = hash_pass.hexdigest()

    if not utils.Email.HasMxRecord(email):
        return render_template("pages/login.html", re_site=configs['re_captcha_site_key'],error_message="Invalid Email Address!",message_color='red')

    if utils.Email.IsBlockedDomain(email):
        return render_template("pages/login.html", re_site=configs['re_captcha_site_key'],error_message="This Email Domain Is Blocked!",message_color='red')

    code = utils.GeneralUtils.GenerateRandomCode(12)

    token = utils.GeneralUtils.GenerateToken(username, request.form.get("password"))
    cursor.execute(
        "INSERT INTO users(username,email, display_name, encrypted_password, timestamp, token, verification_code) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            username.lower(),
            email,
            username,
            hashed_password,
            str(time.time()),
            token,
            code
        )
    )

    conn.commit()
    cursor.close()
    conn.close()

    IP_ACCOUNT_COUNTER[ip] = IP_ACCOUNT_COUNTER.get(ip, 0) + 1

    if configs['test']:
        link = f'http://localhost/api/user/verify?token={token}&code={code}'
    else:
        link = f'http://forums.af-comms.net/api/user/verify?token={token}&code={code}'

    utils.Email.SendEmail(email, "Anti-furry Forums Account Creation",
        f"<p>Your anti-furry forums verification link is <a href='{link}'>here</a>. Do not click if you didn't sign up for anything!</p>")

    if configs["webhook"] == True:
        requests.post(configs["webhook_url"], json={"content": f"Someone created an account '{username}' and email '{email}'"})

    response = make_response(redirect('/app'))
    response.set_cookie('token', token, httponly=True, samesite='Lax')

    return response


@user_bp.route("verify", methods=["GET"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
@utils.Wrappers.logdata()
@utils.Wrappers.require_query_params(["token","code"])
def VerifyApi():
    cursor, conn = utils.GeneralUtils.InnitDB()

    if cursor.execute("SELECT * FROM users WHERE token=? AND verification_code=?",(request.args['token'],request.args['code'],)).fetchone() is None:
        return jsonify({"Error": "Invalid code!"}), 400

    cursor.execute('UPDATE users SET verified=1 WHERE token=? AND verification_code=?',(request.args['token'],request.args['code'],))

    conn.commit()
    cursor.close()
    conn.close()

    if configs["webhook"] == True:
        requests.post(configs["webhook_url"], json={"content": f"Someone verified their account!"})

    response = make_response(redirect('/app'))

    return response


@user_bp.route("login",methods=["POST"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
@utils.Wrappers.logdata()
@utils.Wrappers.require_form_params(["username","password", "recaptcha_token"])
def LoginApi():
    cursor,conn = utils.GeneralUtils.InnitDB()

    recaptcha_token = request.form.get("recaptcha_token")
    if not utils.Captcha.VerifyRecaptcha(recaptcha_token):
        return jsonify({"Error": "Failed reCAPTCHA verification"}), 403

    username = request.form.get("username").lower()
    if (cursor.execute("SELECT username FROM users WHERE username=?",(username,)).fetchone() == None):

        if not configs['custom_message_enabled']:
            return render_template("pages/login.html", re_site=configs['re_captcha_site_key'],error_message="No such user!",message_color='red')
        else:
            return render_template("pages/login.html", re_site=configs['re_captcha_site_key'],error_message=configs['custom_message'],message_color='yellow')

    enc_pass = hashlib.sha256()
    enc_pass.update(request.form.get("password").encode())
    enc_pass = enc_pass.hexdigest()

    row = cursor.execute("SELECT encrypted_password FROM users WHERE username=?", (username,)).fetchone()
    if not row or row[0] != enc_pass:
        return render_template("pages/login.html", re_site=configs['re_captcha_site_key'],error_message="Invalid password",message_color='red')

    row = cursor.execute("SELECT deleted FROM users WHERE username=?", (username,)).fetchone()
    if not row or row[0] != 0:
        return render_template("pages/login.html", re_site=configs['re_captcha_site_key'],error_message="User is deleted, if you manually deleted this account you can restore it by emailing 'afcommsnet.contact@gmail.com' and stating your intentions!",message_color='red')

    row = cursor.execute("SELECT banned FROM users WHERE username=?", (username,)).fetchone()
    if not row or row[0] != 0:
        return render_template("pages/login.html", re_site=configs['re_captcha_site_key'],error_message="Your account has been permanently banned off this website! You may appeal at 'afcommsnet.contact@gmail.com' by emailing set adress and stating your intentions! You may also find the specific ban reason from there.",message_color='red')

    token = cursor.execute("SELECT token FROM users WHERE username=?", (username,)).fetchone()[0]

    conn.commit()
    cursor.close()
    conn.close()

    response = make_response(redirect('/app'))
    response.set_cookie('token', token, httponly=True, samesite='Lax')

    return response


@user_bp.route("view",methods=["GET"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
@utils.Wrappers.logdata()
@utils.Wrappers.require_query_params(["username"])
def UserViewApi():
    cursor,conn = utils.GeneralUtils.InnitDB()

    token = request.cookies.get("token")
    if not token or (cursor.execute("SELECT token FROM users WHERE token=?", (token,)).fetchone() == None):
        return jsonify({"Error":"Token is invalid"}),400

    username = request.args.get("username").lower()
    user = cursor.execute("SELECT username,display_name,bio,timestamp,admin,id,deleted FROM users WHERE username=?", (username,)).fetchone()
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


@user_bp.route("viewall",methods=["GET"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
@utils.Wrappers.logdata()
def UserViewallApi():
    cursor,conn = utils.GeneralUtils.InnitDB()

    token = request.cookies.get("token")
    if not token or (cursor.execute("SELECT token FROM users WHERE token=?", (token,)).fetchone() == None):
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


@user_bp.route("tokendata",methods=["GET"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
@utils.Wrappers.logdata()
def TokenViewApi():
    cursor,conn = utils.GeneralUtils.InnitDB()

    token = request.cookies.get("token")
    if not token or (cursor.execute("SELECT token FROM users WHERE token=?", (token,)).fetchone() == None):
        return jsonify({"Error":"Token is invalid"}),400

    user = cursor.execute("SELECT username,display_name,bio,timestamp,admin,id FROM users WHERE token=?", (token,)).fetchone()
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


@user_bp.route("delete",methods=["DELETE"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
@utils.Wrappers.logdata()
def UserDeleteApi():
    cursor, conn = utils.GeneralUtils.InnitDB()

    token = request.cookies.get("token")
    if not token or cursor.execute("SELECT token FROM users WHERE token=?", (token,)).fetchone() is None:
        return jsonify({"Error": "Token is invalid"}), 400

    # BUG Possible vuln where user might keep track of their token before deleting their account and use their deleted account to do stuff
    cursor.execute("UPDATE users SET deleted=1 WHERE token=?", (token,))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"Message": "Success"}), 200


@user_bp.route("modify",methods=["PATCH"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
@utils.Wrappers.logdata()
@utils.Wrappers.require_json_with_fields(["display_name","bio"])
def UserModifyApi():
    forbidden_chars = {" ", "#", "@", "$", "%", "^", "&", "*", "(", ")", "-", "=", "+", "<", ">", "[", "]"}
    display_forbidden_chars = {"#", "@", "$", "%", "^", "&", "*", "(", ")", "-", "=", "+", "<", ">"}

    display_name = request.json.get("display_name")
    bio = request.json.get("bio")

    if not display_name or len(display_name) >= 40 or any(char in display_forbidden_chars for char in display_name):
        return jsonify({"Error":"Display name dosen't repsect constrains"}),400

    if not bio or len(bio) > 200:
        return jsonify({"Error":"Bio dosen't repsect constrains"}),400

    token = request.cookies.get("token")
    if not token:
        return jsonify({"Error":"Token is invalid"}),400

    cursor,conn = utils.GeneralUtils.InnitDB()

    if cursor.execute("SELECT token FROM users WHERE token=?", (token,)).fetchone() == None:
        return jsonify({"Error":"Token is invalid"}),400

    # OPTIMIZATION TODO: Make this get the username from token to delete easier
    cursor.execute("UPDATE users SET display_name=?, bio=? WHERE token=?", (display_name, bio, token))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"Message":"Success"}),200
