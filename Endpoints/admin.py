

from flask import Blueprint, request, jsonify , current_app
import hashlib, time, requests

import json
import utils

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
@admin_bp.route("/api/users/unban",methods=["POST"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
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
@admin_bp.route("/api/admin/tokenact", methods=["GET"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
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
