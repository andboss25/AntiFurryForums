
from flask import Blueprint, request, jsonify , current_app
import hashlib, time, requests

import json
import utils

thread_bp = Blueprint('thread', __name__)

configs = json.loads(open("config.json").read())

# Thread api

# Check if ip is blocked
# Check if request is json
# Check if it has all parameters needed
# Check if identifier name is already used
# Check if the params are all valid
# Insert into db
@thread_bp.route("/post", methods=["POST"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
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

    user = cursor.execute("SELECT admin FROM users WHERE token=?", (data["token"],)).fetchone()
    if not user:
        
        return jsonify({"Error": "Token is invalid"}), 401
    
    if configs["ThreadAdminOnly"]:
        is_admin = user[0]
        if is_admin == 0:
            return jsonify({"Error": "Thread creation is disabled for non-Admin users in this version of the forums , please use already existing threads and post your posts in there!"}), 400
    else:
        pass

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
@thread_bp.route("/view", methods=["GET"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
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
@thread_bp.route("/delete", methods=["DELETE"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
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
@thread_bp.route("/subscribe", methods=["POST"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
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
@thread_bp.route("/subscriptions", methods=["GET"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
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
