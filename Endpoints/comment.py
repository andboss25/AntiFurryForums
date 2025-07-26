from flask import Blueprint, request, jsonify, current_app
import hashlib, time, requests
import json
import utils

comment_bp = Blueprint('comment', __name__)
configs = json.loads(open("config.json").read())

# POST comment
@comment_bp.route("post", methods=["POST"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
@utils.Wrappers.logdata()
@utils.Wrappers.require_json_with_fields(["content", "post_id"])
def MakeComment():
    cursor, conn = utils.GeneralUtils.InnitDB()
    data = request.json

    content = data["content"]
    post_id = data["post_id"]

    if 'token' not in request.cookies:
        return jsonify({"Error": "No token found"}), 403
    token = request.cookies.get('token')

    try:
        reply_to = data["replies_to"]
    except:
        reply_to = None

    if reply_to:
        if cursor.execute("SELECT username FROM users WHERE username=?", (reply_to,)).fetchone() is None:
            return jsonify({"Error": "No user with such username to reply to"}), 400

    if len(content) >= 100:
        return jsonify({"Error": "Request doesn't respect constraints"}), 400

    user = cursor.execute("SELECT id FROM users WHERE token=?", (token,)).fetchone()
    if not user:
        return jsonify({"Error": "Token is invalid"}), 401

    if not cursor.execute("SELECT id FROM users WHERE token=? AND verified=1", (token,)).fetchone():
        return jsonify({"Error": "User is not verified!"}), 401

    if not cursor.execute("SELECT id FROM posts WHERE id=?", (post_id,)).fetchone():
        return jsonify({"Error": "No such post with this id!"}), 400

    username = utils.GeneralUtils.GetUsernameFromToken(token)
    cursor.execute(
        "INSERT INTO comments(owner_username, post_id, content, replies_to) VALUES (?, ?, ?, ?)",
        (username, post_id, content, reply_to)
    )

    conn.commit()
    cursor.close()
    conn.close()

    if configs["webhook"]:
        requests.post(configs["webhook_url"], json={
            "content": f"{username} created a comment on post with id '{post_id}' with content '{content}'"
        })

    return jsonify({"Message": "Success"}), 200

# VIEW comments
@comment_bp.route("view", methods=["GET"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
@utils.Wrappers.logdata()
@utils.Wrappers.require_query_params(["post_id"])
def ViewComments():
    data = request.args
    post_id = data["post_id"]

    if 'token' not in request.cookies:
        return jsonify({"Error": "No token found"}), 403
    token = request.cookies.get('token')

    cursor, conn = utils.GeneralUtils.InnitDB()

    user = cursor.execute("SELECT username FROM users WHERE token=?", (token,)).fetchone()
    if not user:
        cursor.close()
        conn.close()
        return jsonify({"Error": "Token is invalid"}), 400

    if not cursor.execute("SELECT id FROM users WHERE token=? AND verified=1", (token,)).fetchone():
        cursor.close()
        conn.close()
        return jsonify({"Error": "User is not verified!"}), 401

    username = user[0]
    comments = cursor.execute("SELECT * FROM comments WHERE post_id=?", (post_id,)).fetchall()

    liked = [row[0] for row in cursor.execute(
        "SELECT id FROM liked_comments WHERE username = ?", (username,)
    ).fetchall()]

    comments_list = []
    for comment in comments:
        is_liked = comment[0] in liked
        post_dict = {
            "id": comment[0],
            "owner_username": comment[1],
            "post_id": comment[2],
            "content": comment[3],
            "timestamp": comment[4],
            "replies_to": comment[5],
            "liked": is_liked
        }
        comments_list.append(post_dict)

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"Message": "Success", "Comments": comments_list}), 200

# DELETE comment
@comment_bp.route("delete", methods=["DELETE"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
@utils.Wrappers.logdata()
@utils.Wrappers.require_query_params(["id"])
def DeleteComment():
    data = request.args
    comment_id = data["id"]

    if 'token' not in request.cookies:
        return jsonify({"Error": "No token found"}), 403
    token = request.cookies.get('token')

    cursor, conn = utils.GeneralUtils.InnitDB()

    username = utils.GeneralUtils.GetUsernameFromToken(token)
    if not username:
        cursor.close()
        conn.close()
        return jsonify({"Error": "Invalid token"}), 401

    post = cursor.execute(
        "SELECT * FROM comments WHERE id=? AND owner_username=?", (comment_id, username)
    ).fetchone()

    if not post:
        cursor.close()
        conn.close()
        return jsonify({"Error": "Comment not found or not owned by user"}), 404

    cursor.execute("DELETE FROM comments WHERE id=? AND owner_username=?", (comment_id, username))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"Message": "Comment successfully deleted"}), 200
