
from flask import Blueprint, request, jsonify , current_app
import hashlib, time, requests

import json
import utils

post_bp = Blueprint('post', __name__)

configs = json.loads(open("config.json").read())

# Post api

# Check if ip is blocked
# Check if request is json
# Check if it has all parameters needed
# Check if the params are all valid
# Insert into db
@post_bp.route("post", methods=["POST"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
@utils.Wrappers.logdata()
@utils.Wrappers.require_json_with_fields(["title","content","thread_identifier","recaptcha_token"])
def MakePost():
    forbidden_chars = {" ", "#", "@", "$", "%", "^", "&", "*", "(", ")", "-", "=", "+", "<", ">", "[", "]"}

    data = request.json

    title = data["title"]
    content = data["content"]
    thread_identifier = data["thread_identifier"]
    recaptcha_token = request.json.get("recaptcha_token")
    if not utils.Captcha.VerifyRecaptcha(recaptcha_token):
        return jsonify({"Error": "Failed reCAPTCHA verification"}), 403

    if (
        len(content) >= 300 or
        len(title) > 50
    ):
        
        return jsonify({"Error": "Request doesn't respect constraints"}), 400
    
        
    try:
        image_attachment = data["image_attachment"]
    except KeyError:
        image_attachment = ""

    # Filter external images for the sake of no zero-click vulns and such
    if image_attachment.startswith("https://") or image_attachment.startswith("http://"):
        image_attachment = ""
    elif image_attachment.startswith("/api/images/view/"):
        pass
    else:
        image_attachment = ""
        
    cursor, conn = utils.GeneralUtils.InnitDB()

    if 'token' not in request.cookies:
        return jsonify({"Error": "No token found"}), 403
    token = request.cookies.get('token')

    user = cursor.execute("SELECT id FROM users WHERE token=?", (token,)).fetchone()
    if not user:
        return jsonify({"Error": "Token is invalid"}), 401
    
    if not cursor.execute("SELECT id FROM users WHERE token=? AND verified=1", (token,)).fetchone():
        return jsonify({"Error": "User is not verified!"}), 401
    
    if not cursor.execute("SELECT identifier FROM threads WHERE identifier=?", (thread_identifier,)).fetchone():
        return jsonify({"Error": "No such thread with this identifier!"}), 400

    username = utils.GeneralUtils.GetUsernameFromToken(token)
    cursor.execute(
        "INSERT INTO posts(owner_username,thread_identifier,content,title,image_attachment) VALUES (?, ?, ?, ?, ?)",
        (username,thread_identifier,content,title,image_attachment)
    )

    conn.commit()
    cursor.close()
    conn.close()

    
    if configs["webhook"] == True:
        requests.post(configs["webhook_url"],json={"content":f"{username} created a post on '{thread_identifier}' with title '{title}' and content '{content}'"})

    return jsonify({"Message": "Success"}), 200

# Check if IP is blocked
# Check for cooldown on IP
# Validate required parameters: token, search
# Validate token and get username
# Search posts or filter by post_identifier or get all posts
# Get user's subscribed posts
# Add 'liked' flag to each post in response
@post_bp.route("view", methods=["GET"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
@utils.Wrappers.logdata()
@utils.Wrappers.require_query_params(["search"])
def ViewPosts():
    data = request.args

    if 'token' not in request.cookies:
        return jsonify({"Error": "No token found"}), 403
    token = request.cookies.get('token')

    search = data["search"].lower() == "true"
    try:
        limit = int(data.get("limit", 20))
        last_id = data.get("last_id", None)
    except:
        return jsonify({"Error":"Invalid request"}),400

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

    # Handle pagination anchor if last_id is present
    last_timestamp = None
    if last_id:
        result = cursor.execute("SELECT timestamp FROM posts WHERE id = ?", (last_id,)).fetchone()
        if result:
            last_timestamp = result[0]

    # Build the base query
    posts = []
    query = ""
    params = []

    if search:
        search_for = data.get("search_for", "")
        like_term = f"%{search_for}%"
        query = "SELECT * FROM posts WHERE (content LIKE ? OR title LIKE ?)"
        params.extend([like_term, like_term])
    elif "post_identifier" in data:
        query = "SELECT * FROM posts WHERE thread_identifier = ?"
        params.append(data["post_identifier"])
    elif "id" in data:
        query = "SELECT * FROM posts WHERE id = ?"
        params.append(data["id"])
    else:
        query = "SELECT * FROM posts WHERE 1=1"

    if last_timestamp:
        query += " AND timestamp < ?"
        params.append(last_timestamp)

    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    posts = cursor.execute(query, params).fetchall()

    # Fetch liked posts for user
    liked = [row[0] for row in cursor.execute(
        "SELECT post_id FROM liked_posts WHERE username = ?", (username,)
    ).fetchall()]

    post_list = []
    for post in posts:
        is_liked = str(post[0]) in liked
        post_likes = cursor.execute("SELECT COUNT(*) FROM liked_posts WHERE post_id = ?", (post[0],)).fetchone()[0]

        post_dict = {
            "id": post[0],
            "owner_username": post[1],
            "post_identifier": post[2],
            "title": post[3],
            "content": post[4],
            "image_attachment": post[5],
            "liked": is_liked,
            "timestamp": post[6],
            "likes": post_likes
        }
        post_list.append(post_dict)

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"Message": "Success", "Posts": post_list}), 200

# Check if ip is blocked
# Check if request is JSON
# Check if it has all parameters needed
# Validate token and ownership
# Delete post if it exists and belongs to user
@post_bp.route("delete", methods=["DELETE"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
@utils.Wrappers.logdata()
@utils.Wrappers.require_query_params((["id"]))
def DeletePost():
    data = request.args
    if 'token' not in request.cookies:
        return jsonify({"Error": "No token found"}), 403
    token = request.cookies.get('token')
    id = data["id"]

    cursor, conn = utils.GeneralUtils.InnitDB()

    username = utils.GeneralUtils.GetUsernameFromToken(token)
    if not username:
        
        cursor.close()
        conn.close()
        return jsonify({"Error": "Invalid token"}), 401

    post = cursor.execute(
        "SELECT * FROM posts WHERE id=? AND owner_username=?", (id, username)
    ).fetchone()

    if not post:
        cursor.close()
        conn.close()
        return jsonify({"Error": "Post not found or not owned by user"}), 404

    cursor.execute("DELETE FROM posts WHERE id=? AND owner_username=?", (id, username))

    conn.commit()
    cursor.close()
    conn.close()


    return jsonify({"Message": "Post successfully deleted"}), 200


# Check if IP is blocked
# Check if request is JSON
# Check if all parameters exist
# Validate token and user
# Like or unlike based on action
@post_bp.route("like", methods=["POST"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
@utils.Wrappers.logdata()
@utils.Wrappers.require_json_with_fields(["id", "action"])
def LikePost():
    data = request.json
    if 'token' not in request.cookies:
        return jsonify({"Error": "No token found"}), 403
    token = request.cookies.get('token')
    id = data["id"]
    action = data["action"].lower()

    username = utils.GeneralUtils.GetUsernameFromToken(token)
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

    thread_exists = cursor.execute("SELECT 1 FROM posts WHERE id=?", (id,)).fetchone()
    if not thread_exists:
        cursor.close()
        conn.close()
        return jsonify({"Error": "Post does not exist"}), 404

    if action == "like":
        existing = cursor.execute(
            "SELECT 1 FROM liked_posts WHERE username=? AND post_id=?",
            (username.lower(), id)
        ).fetchone()

        if existing:
            cursor.close()
            conn.close()
            return jsonify({"Error": "Already liked"}), 400

        cursor.execute(
            "INSERT INTO liked_posts(username, post_id) VALUES (?, ?)",
            (username, id)
        )
        conn.commit()

    elif action == "unlike":
        cursor.execute(
            "DELETE FROM liked_posts WHERE username=? AND post_id=?",
            (username, id)
        )
        conn.commit()

    else:
        cursor.close()
        conn.close()
        return jsonify({"Error": "Action must be either 'like' or 'unlike'"}), 400

    cursor.close()
    conn.close()

    return jsonify({"Message": f"Successfully {action}d the post"}), 200
