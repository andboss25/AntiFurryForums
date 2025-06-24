from flask import Blueprint, request, jsonify , current_app
import hashlib, time, requests

import json
import utils

feed_bp = Blueprint('feed', __name__)

configs = json.loads(open("config.json").read())


@feed_bp.route("post", methods=["GET"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
@utils.Wrappers.logdata()
@utils.Wrappers.require_query_params(["token"])
def PostsFeed():
    data = request.args
    token = data["token"]

    cursor, conn = utils.GeneralUtils.InnitDB()

    user = cursor.execute("SELECT username FROM users WHERE token=?", (token,)).fetchone()
    if not user:
        
        cursor.close()
        conn.close()
        return jsonify({"Error": "Token is invalid"}), 400

    username = user[0]

    # Subscribed threads
    subscribed_threads = [row[0] for row in cursor.execute(
        "SELECT thread_identifier FROM subscribed_threads WHERE username = ?", (username,)
    ).fetchall()]

    # Posts from subscribed threads (random order)
    if subscribed_threads:
        placeholders = ','.join('?' for _ in subscribed_threads)
        subscribed_posts = cursor.execute(
            f"""
            SELECT * FROM posts 
            WHERE thread_identifier IN ({placeholders}) 
            ORDER BY RANDOM() 
            LIMIT 20
            """, 
            subscribed_threads
        ).fetchall()
    else:
        subscribed_posts = []

    # Posts from other threads (also random)
    already_included_ids = [post[0] for post in subscribed_posts]
    if already_included_ids:
        placeholders = ','.join('?' for _ in already_included_ids)
        other_posts = cursor.execute(
            f"""
            SELECT * FROM posts 
            WHERE id NOT IN ({placeholders}) 
            ORDER BY RANDOM()
            """, 
            already_included_ids
        ).fetchall()
    else:
        other_posts = cursor.execute(
            "SELECT * FROM posts ORDER BY RANDOM() LIMIT 10"
        ).fetchall()

    posts = subscribed_posts + other_posts

    # Get liked posts for the user
    liked = [row[0] for row in cursor.execute(
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

    # Optionally deduplicate by post ID
    post_list = list({post["id"]: post for post in post_list}.values())

    conn.commit()
    cursor.close()
    conn.close()


    return jsonify({"Message": "Success", "Posts": post_list}), 200

@feed_bp.route("thread", methods=["GET"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
@utils.Wrappers.logdata()
@utils.Wrappers.require_query_params(["token"])
def RecomendThreads():
    data = request.args
    token = data["token"]

    cursor, conn = utils.GeneralUtils.InnitDB()

    user = cursor.execute("SELECT username FROM users WHERE token=?", (token,)).fetchone()
    if not user:
        
        cursor.close()
        conn.close()
        return jsonify({"Error": "Token is invalid"}), 400

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
