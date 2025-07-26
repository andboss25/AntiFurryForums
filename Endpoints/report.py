from flask import Blueprint, request, jsonify, current_app
import json
import utils

report_bp = Blueprint('report', __name__)
configs = json.loads(open("config.json").read())

@report_bp.route("add", methods=["POST"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
@utils.Wrappers.logdata()
@utils.Wrappers.require_json_with_fields(["resource_id", "type_of_report", "type_of_resource", "additional_info"])
def PostReport():
    if 'token' not in request.cookies:
        return jsonify({"Error": "No token found"}), 403
    token = request.cookies.get("token")

    username = utils.GeneralUtils.GetUsernameFromToken(token)
    if not username:
        return jsonify({"Error": "Invalid token"}), 401

    data = request.json
    resource_id = data["resource_id"]
    type_of_report = data["type_of_report"].lower()
    type_of_resource = data["type_of_resource"].lower()
    additional_info = data["additional_info"]

    cursor, conn = utils.GeneralUtils.InnitDB()
    cursor.execute("""
        INSERT INTO reports(username, resource_id, type_of_report, type_of_resource, additional_info)
        VALUES (?, ?, ?, ?, ?)
    """, (username, resource_id, type_of_report, type_of_resource, additional_info))
    
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"Message": "Successfully reported the resource"}), 200

@report_bp.route("view", methods=["GET"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
@utils.Wrappers.logdata()
def ViewReports():
    if 'token' not in request.cookies:
        return not_found_page()
    token = request.cookies.get("token")

    cursor, conn = utils.GeneralUtils.InnitDB()
    user = cursor.execute("SELECT username, admin FROM users WHERE token=?", (token,)).fetchone()

    if not user or user[1] == 0:
        cursor.close()
        conn.close()
        return not_found_page()

    reports = cursor.execute("SELECT * FROM reports").fetchall()
    reports_list = [{
        "id": r[0],
        "username": r[1],
        "resource_id": r[2],
        "type_of_report": r[3],
        "type_of_resource": r[4],
        "additional_info": r[5],
        "timestamp": r[6]
    } for r in reports]

    cursor.close()
    conn.close()

    return jsonify({"Message": "Success", "Reports": reports_list}), 200


def not_found_page():
    return """<html lang="en"><head><title>404 Not Found</title></head>
    <body><h1>Not Found</h1>
    <p>The requested URL was not found on the server.</p></body></html>""", 404
