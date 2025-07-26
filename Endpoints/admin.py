from flask import Blueprint, request, jsonify, current_app
import hashlib, time, requests

import json
import utils
import os

admin_bp = Blueprint('admin', __name__)

configs = json.loads(open("config.json").read())

# Administration of this website

# Check if ip is blocked
# Check if request is json
# Check if it has all parameters needed
# Check if the token is valid and admin
# Set account as banned
@admin_bp.route("/api/users/ban",methods=["POST"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
@utils.Wrappers.logdata()
@utils.Wrappers.require_json_with_fields(["username"])  # token removed from json fields here
def BanApi():
    cursor, conn = utils.GeneralUtils.InnitDB()

    token = request.cookies.get("token")
    if cursor.execute("SELECT token FROM users WHERE token=? AND admin=1", (token,)).fetchone() is None:
        return jsonify({"Error": "Token is invalid"}), 400

    cursor.execute("UPDATE users SET banned=1 WHERE username=?", (request.json.get("username"),))
    cursor.execute("UPDATE users SET token=? WHERE username=?", (utils.GeneralUtils.GenerateToken("banned-user","QERUDSFKRENDSFMUIJKGRFDYUJRFSJFDSJJSJHFHJDSJSJFDODIOFDOS"),request.json.get("username"),))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"Message": "Success"}), 200

# Set account as unbanned
@admin_bp.route("/api/users/unban",methods=["POST"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
@utils.Wrappers.logdata()
@utils.Wrappers.require_json_with_fields(["username"])  # token removed from json fields here
def UnBanApi():
    cursor, conn = utils.GeneralUtils.InnitDB()

    token = request.cookies.get("token")
    if cursor.execute("SELECT token FROM users WHERE token=? AND admin=1", (token,)).fetchone() is None:
        return jsonify({"Error": "Token is invalid"}), 400

    cursor.execute("UPDATE users SET banned=0 WHERE username=?", (request.json.get("username"),))
    cursor.execute("UPDATE users SET token=? WHERE username=?", (utils.GeneralUtils.GenerateToken(request.json.get("username"),"QERUDSFKRENDSFMUIJKGRFDYUJRFSJFDSJJSJHFHJDSJSJFDODIOFDOS"),request.json.get("username"),))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"Message": "Success"}), 200

# Show tokens for user if requester admin
@admin_bp.route("/api/admin/tokenact", methods=["GET"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
@utils.Wrappers.logdata()
@utils.Wrappers.require_query_params(["username"])  # token removed from query params here
def UsernameToToken():
    data = request.args
    token = request.cookies.get("token")  # from cookie now
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

@admin_bp.route("/api/admin/purge_post", methods=["DELETE"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
@utils.Wrappers.logdata()
@utils.Wrappers.require_json_with_fields(["post_id"])  # token removed from json fields here
def PurgePost():
    cursor, conn = utils.GeneralUtils.InnitDB()
    data = request.json
    token = request.cookies.get("token")

    user = cursor.execute("SELECT username,admin FROM users WHERE token=? AND admin=1", (token,)).fetchone()
    if not user:
        cursor.close()
        conn.close()
        return jsonify({"Message": "Unauthorized"}), 401
    
    cursor.execute("DELETE FROM posts WHERE id=?",(data.get('post_id'),))
    cursor.execute("DELETE FROM comments WHERE post_id=?",(data.get('post_id'),))
    cursor.execute("DELETE FROM liked_posts WHERE post_id=?",(data.get('post_id'),))
    
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"Message": "Success"}), 200

@admin_bp.route("/api/admin/purge_user", methods=["DELETE"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
@utils.Wrappers.logdata()
@utils.Wrappers.require_json_with_fields(["username"])  # token removed here
def PurgeUser():
    cursor, conn = utils.GeneralUtils.InnitDB()
    data = request.json
    token = request.cookies.get("token")

    user = cursor.execute("SELECT username,admin FROM users WHERE token=? AND admin=1", (token,)).fetchone()
    if not user:
        cursor.close()
        conn.close()
        return jsonify({"Message": "Unauthorized"}), 401
    
    user_to_ban = cursor.execute("SELECT username,admin FROM users WHERE username=?", (data.get('username'),)).fetchone()
    if not user_to_ban:
        cursor.close()
        conn.close()
        return jsonify({"Message": "User not found!"}), 401
    
    if user_to_ban[1] == 1:
        cursor.close()
        conn.close()
        return jsonify({"Message": "Cannot purge admin!"}), 401
    
    cursor.execute("DELETE FROM users WHERE username=?",(data.get('username'),))
    cursor.execute("DELETE FROM posts WHERE owner_username=?",(data.get('username'),))
    cursor.execute("DELETE FROM comments WHERE owner_username=?",(data.get('username'),))
    cursor.execute("DELETE FROM threads WHERE owner_username=?",(data.get('username'),))
    cursor.execute("DELETE FROM subscribed_threads WHERE username=?",(data.get('username'),))
    cursor.execute("DELETE FROM liked_posts WHERE username=?",(data.get('username'),))
    cursor.execute("DELETE FROM liked_comments WHERE username=?",(data.get('username'),))
    cursor.execute("DELETE FROM reports WHERE username=?",(data.get('username'),))
    
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"Message": "Success"}), 200

@admin_bp.route("/api/admin/banwave", methods=["DELETE"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
@utils.Wrappers.logdata()
@utils.Wrappers.require_json_with_fields(["keyword"])  # token removed here
def BanWave():
    cursor, conn = utils.GeneralUtils.InnitDB()
    data = request.json
    token = request.cookies.get("token")

    user = cursor.execute("SELECT username,admin FROM users WHERE token=? AND admin=1", (token,)).fetchone()
    if not user:
        cursor.close()
        conn.close()
        return jsonify({"Message": "Unauthorized"}), 401

    
    cursor.execute("DELETE FROM users WHERE username LIKE ?",(data.get('keyword'),))
    cursor.execute("DELETE FROM posts WHERE owner_username LIKE ?",(data.get('keyword'),))
    cursor.execute("DELETE FROM comments WHERE owner_username LIKE ?",(data.get('keyword'),))
    cursor.execute("DELETE FROM threads WHERE owner_username LIKE ?",(data.get('keyword'),))
    cursor.execute("DELETE FROM subscribed_threads WHERE username LIKE ?",(data.get('keyword'),))
    cursor.execute("DELETE FROM liked_posts WHERE username LIKE ?",(data.get('keyword'),))
    cursor.execute("DELETE FROM liked_comments WHERE username LIKE ?",(data.get('keyword'),))
    cursor.execute("DELETE FROM reports WHERE username LIKE ?",(data.get('keyword'),))
    
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"Message": "Success"}), 200


@admin_bp.route("/api/admin/purge_thread", methods=["DELETE"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
@utils.Wrappers.logdata()
@utils.Wrappers.require_json_with_fields(["thread_identifier"])  # token removed here
def PurgeThread():
    cursor, conn = utils.GeneralUtils.InnitDB()
    data = request.json
    token = request.cookies.get("token")

    user = cursor.execute("SELECT username,admin FROM users WHERE token=? AND admin=1", (token,)).fetchone()
    if not user:
        cursor.close()
        conn.close()
        return jsonify({"Message": "Unauthorized"}), 401
    
    cursor.execute("DELETE FROM posts WHERE thread_identifier=?",(data.get('thread_identifier'),))
    cursor.execute("DELETE FROM threads WHERE identifier=?",(data.get('thread_identifier'),))
    
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"Message": "Success"}), 200

@admin_bp.route("/api/admin/shutweb", methods=["POST"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
@utils.Wrappers.logdata()
@utils.Wrappers.require_json_with_fields([])  # no token required in json anymore
def ShutWeb():
    cursor, conn = utils.GeneralUtils.InnitDB()
    token = request.cookies.get("token")

    user = cursor.execute("SELECT username,admin FROM users WHERE token=? AND admin=1", (token,)).fetchone()
    if not user:
        cursor.close()
        conn.close()
        return jsonify({"Message": "Unauthorized"}), 401
    
    conn.commit()
    cursor.close()
    conn.close()

    if configs["webhook"] == True:
        requests.post(configs["webhook_url"], json={"content": f"Emergency Web-Server Shutdown [EWSS] has been triggered and succesfully executed the Anti-furry forums is no longer running! Resolve the issue conduct meintanance checks ASAP as the website is down!!! @everyone"})

    os._exit(0)

    return jsonify({"Message": "Success"}), 200

@admin_bp.route("/api/admin/shutall", methods=["POST"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
@utils.Wrappers.logdata()
@utils.Wrappers.require_json_with_fields([])  # no token required in json anymore
def ShutAll():
    cursor, conn = utils.GeneralUtils.InnitDB()
    token = request.cookies.get("token")

    user = cursor.execute("SELECT username,admin FROM users WHERE token=? AND admin=1", (token,)).fetchone()
    if not user:
        cursor.close()
        conn.close()
        return jsonify({"Message": "Unauthorized"}), 401
    
    conn.commit()
    cursor.close()
    conn.close()

    if configs["webhook"] == True:
        requests.post(configs["webhook_url"], json={"content": f"Emergency Full-Server Shutdown [EFSS] has been triggered and succesfully executed the Anti-furry forums AWS EC2 instance is no longer running! Resolve the issue conduct meintanance checks ASAP as the website is down!!! @everyone"})

    try:
        os.system("sudo shutdown now")
    except:
        try:
            os.system("shutdown /s /t 0")
        except:    
            if configs["webhook"] == True:
                requests.post(configs["webhook_url"], json={"content": f"Emergency Full-Server Shutdown [EFSS] HAS FULLY FAILED | MUST SHUT DOWN THE SERVER MANUALLY! @everyone"})

    return jsonify({"Message": "Success"}), 200

# Show related users for a given username
@admin_bp.route("/api/admin/findrelusers", methods=["GET"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
@utils.Wrappers.logdata()
@utils.Wrappers.require_query_params(["username"])  # token removed here
def UsernameToRelatedUsers():
    data = request.args
    token = request.cookies.get("token")
    username = data["username"]

    cursor, conn = utils.GeneralUtils.InnitDB()

    user = cursor.execute("SELECT username,admin FROM users WHERE token=? AND admin=1", (token,)).fetchone()
    if not user:
        cursor.close()
        conn.close()
        return jsonify({"Message": "Unauthorized"}), 401

    cursor.execute("SELECT DISTINCT ip FROM ip_data WHERE usr_name=?", (username,))
    user_ips = [row[0] for row in cursor.fetchall()]
    related_users = set()

    for ip in user_ips:
        cursor.execute("SELECT DISTINCT usr_name FROM ip_data WHERE ip=? AND usr_name!=?", (ip, username))
        users_for_ip = [row[0] for row in cursor.fetchall()]
        related_users.update(users_for_ip)

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"Message": "Success","Users":list(related_users)}), 200

# IP Ban user
@admin_bp.route("/api/users/ipban",methods=["POST"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
@utils.Wrappers.logdata()
@utils.Wrappers.require_json_with_fields(["username"])  # token removed here
def IpBanApi():
    cursor, conn = utils.GeneralUtils.InnitDB()

    token = request.cookies.get("token")
    if cursor.execute("SELECT token FROM users WHERE token=? AND admin=1", (token,)).fetchone() is None:
        conn.commit()
        cursor.close()
        return jsonify({"Error": "Token is invalid"}), 400
    
    cursor.execute("SELECT DISTINCT ip FROM ip_data WHERE usr_name=?", (request.json['username'],))
    user_ips = [row[0] for row in cursor.fetchall()]

    for ip in user_ips:
        print(ip)
        cursor.execute("UPDATE blocked_ip SET blocked=? WHERE ip=?",(1,ip))
        cursor.execute("INSERT INTO blocked_ip(ip,blocked) VALUES (?,?)",(ip,1))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"Message": "Success"}), 200
