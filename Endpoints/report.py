
from flask import Blueprint, request, jsonify , current_app
import hashlib, time, requests

import json
import utils

report_bp = Blueprint('report', __name__)

configs = json.loads(open("config.json").read())

# Reporting API

@report_bp.route("add", methods=["POST"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
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
@report_bp.route("view", methods=["GET"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
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