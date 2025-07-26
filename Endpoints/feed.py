from flask import Blueprint, request, jsonify , current_app
import hashlib, time, requests

import json
import utils

feed_bp = Blueprint('feed', __name__)

configs = json.loads(open("config.json").read())


@feed_bp.route("post", methods=["GET"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
@utils.Wrappers.logdata()
def PostsFeed():
    data = request.args

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
        return jsonify({"Error": "User is not verified! Check your email inbox to verify your account."}), 401

    username = user[0]

    # Get pagination params
    try:
        limit = int(data.get("limit", 20))
        last_id = data.get("last_id", None)
    except:
        return jsonify({"Error":"Invalid request"}),400

    # Get timestamp of last_id for pagination (if provided)
    last_timestamp = None
    if last_id:
        last_post = cursor.execute("SELECT timestamp FROM posts WHERE id=?", (last_id,)).fetchone()
        if last_post:
            last_timestamp = last_post[0]

    # Subscribed threads
    subscribed_threads = [row[0] for row in cursor.execute(
        "SELECT thread_identifier FROM subscribed_threads WHERE username = ?", (username,)
    ).fetchall()]

    subscribed_posts = []
    if subscribed_threads:
        placeholders = ','.join('?' for _ in subscribed_threads)
        params = subscribed_threads[:]

        query = f"""
            SELECT * FROM posts 
            WHERE thread_identifier IN ({placeholders})
        """
        if last_timestamp:
            query += " AND timestamp < ?"
            params.append(last_timestamp)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        subscribed_posts = cursor.execute(query, params).fetchall()

    # Track posts already included
    already_included_ids = [post[0] for post in subscribed_posts]

    other_posts = []
    if len(subscribed_posts) < limit:
        remaining_limit = limit - len(subscribed_posts)
        params = []

        query = "SELECT * FROM posts WHERE 1=1"

        if already_included_ids:
            placeholders = ','.join('?' for _ in already_included_ids)
            query += f" AND id NOT IN ({placeholders})"
            params.extend(already_included_ids)

        if last_timestamp:
            query += " AND timestamp < ?"
            params.append(last_timestamp)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(remaining_limit)

        other_posts = cursor.execute(query, params).fetchall()

    posts = subscribed_posts + other_posts

    # Get liked posts for the user
    liked = [str(row[0]) for row in cursor.execute(
        "SELECT post_id FROM liked_posts WHERE username = ?", (username,)
    ).fetchall()]

    post_list = []
    for post in posts:
        is_liked = str(post[0]) in liked
        post_likes = cursor.execute("SELECT COUNT(*) FROM liked_posts WHERE post_id=?", (post[0],)).fetchone()[0]

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

    # Deduplicate by post ID (if needed)
    post_list = list({post["id"]: post for post in post_list}.values())

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"Message": "Success", "Posts": post_list}), 200

@feed_bp.route("thread", methods=["GET"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
@utils.Wrappers.logdata()
def RecomendThreads():
    data = request.args
    if not 'token' in request.cookies:
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
        return jsonify({"Error": "User is not verified! Check the inbox of the email you used to make this account and verify by clicking the recived link!"}), 401

    username = user[0]

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
