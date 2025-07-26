
import requests
import json
import utils

configs = json.loads(open("config.json").read())

def MakePost(data):
    forbidden_chars = {" ", "#", "@", "$", "%", "^", "&", "*", "(", ")", "-", "=", "+", "<", ">", "[", "]"}

    title = data.get("title")
    content = data.get("content")
    thread_identifier = data.get("thread_identifier")
    recaptcha_token = data.get("recaptcha_token")
    token = data.get("token")

    if not utils.Captcha.VerifyRecaptcha(recaptcha_token):
        return {"status": "error", "message": "Failed reCAPTCHA verification"}

    if len(content) >= 300 or len(title) > 50:
        return {"status": "error", "message": "Constraints violated"}

    image_attachment = data.get("image_attachment", "")
    if image_attachment.startswith("https://") or image_attachment.startswith("http://"):
        image_attachment = ""
    elif not image_attachment.startswith("/api/images/view/"):
        image_attachment = ""

    cursor, conn = utils.GeneralUtils.InnitDB()
    user = cursor.execute("SELECT id FROM users WHERE token=?", (token,)).fetchone()
    if not user:
        return {"status": "error", "message": "Invalid token"}

    if not cursor.execute("SELECT id FROM users WHERE token=? AND verified=1", (token,)).fetchone():
        return {"status": "error", "message": "User not verified"}

    if not cursor.execute("SELECT identifier FROM threads WHERE identifier=?", (thread_identifier,)).fetchone():
        return {"status": "error", "message": "Thread not found"}

    username = utils.GeneralUtils.GetUsernameFromToken(token)
    cursor.execute(
        "INSERT INTO posts(owner_username,thread_identifier,content,title,image_attachment) VALUES (?, ?, ?, ?, ?)",
        (username, thread_identifier, content, title, image_attachment)
    )
    conn.commit()
    cursor.close()
    conn.close()

    if configs.get("webhook"):
        requests.post(configs["webhook_url"], json={
            "content": f"{username} created a post on '{thread_identifier}' with title '{title}' and content '{content}'"
        })

    return {"status": "success", "message": "Post created"}

def ViewPosts(token, search=False, search_for="", post_identifier=None, id=None):
    cursor, conn = utils.GeneralUtils.InnitDB()

    user = cursor.execute("SELECT username FROM users WHERE token=?", (token,)).fetchone()
    if not user:
        cursor.close()
        conn.close()
        return {"status": "error", "message": "Invalid token"}

    if not cursor.execute("SELECT id FROM users WHERE token=? AND verified=1", (token,)).fetchone():
        cursor.close()
        conn.close()
        return {"status": "error", "message": "User not verified"}

    username = user[0]

    if search:
        like_term = f"%{search_for}%"
        posts = cursor.execute("SELECT * FROM posts WHERE content LIKE ? OR title LIKE ?", (like_term, like_term)).fetchall()
    elif post_identifier:
        posts = cursor.execute("SELECT * FROM posts WHERE thread_identifier=?", (post_identifier,)).fetchall()
    elif id:
        posts = cursor.execute("SELECT * FROM posts WHERE id=?", (id,)).fetchall()
    else:
        posts = cursor.execute("SELECT * FROM posts").fetchall()

    liked = [row[0] for row in cursor.execute("SELECT post_id FROM liked_posts WHERE username=?", (username,)).fetchall()]
    post_list = [] 

    for post in posts:
        is_liked = str(post[0]) in liked
        like_count = cursor.execute("SELECT COUNT(*) FROM liked_posts WHERE post_id=?", (post[0],)).fetchone()[0]

        post_dict = {
            "id": post[0],
            "owner_username": post[1],
            "post_identifier": post[2],
            "title": post[3],
            "content": post[4],
            "image_attachment": post[5],
            "liked": is_liked,
            "timestamp": post[6],
            "likes": like_count
        }
        post_list.append(post_dict)

    conn.commit()
    cursor.close()
    conn.close()
    return {"status": "success", "posts": post_list}

def DeletePost(token, post_id):
    cursor, conn = utils.GeneralUtils.InnitDB()

    username = utils.GeneralUtils.GetUsernameFromToken(token)
    if not username:
        cursor.close()
        conn.close()
        return {"status": "error", "message": "Invalid token"}

    post = cursor.execute("SELECT * FROM posts WHERE id=? AND owner_username=?", (post_id, username)).fetchone()
    if not post:
        cursor.close()
        conn.close()
        return {"status": "error", "message": "Post not found or not owned by user"}

    cursor.execute("DELETE FROM posts WHERE id=? AND owner_username=?", (post_id, username))
    conn.commit()
    cursor.close()
    conn.close()

    return {"status": "success", "message": "Post deleted"}

def LikePost(token, post_id, action):
    action = action.lower()
    username = utils.GeneralUtils.GetUsernameFromToken(token)
    cursor, conn = utils.GeneralUtils.InnitDB()

    user = cursor.execute("SELECT username FROM users WHERE token=?", (token,)).fetchone()
    if not user:
        cursor.close()
        conn.close()
        return {"status": "error", "message": "Invalid token"}

    if not cursor.execute("SELECT id FROM users WHERE token=? AND verified=1", (token,)).fetchone():
        cursor.close()
        conn.close()
        return {"status": "error", "message": "User not verified"}

    thread_exists = cursor.execute("SELECT 1 FROM posts WHERE id=?", (post_id,)).fetchone()
    if not thread_exists:
        cursor.close()
        conn.close()
        return {"status": "error", "message": "Post does not exist"}

    if action == "like":
        existing = cursor.execute(
            "SELECT 1 FROM liked_posts WHERE username=? AND post_id=?", (username.lower(), post_id)
        ).fetchone()
        if existing:
            cursor.close()
            conn.close()
            return {"status": "error", "message": "Already liked"}

        cursor.execute("INSERT INTO liked_posts(username, post_id) VALUES (?, ?)", (username, post_id))
        conn.commit()

    elif action == "unlike":
        cursor.execute("DELETE FROM liked_posts WHERE username=? AND post_id=?", (username, post_id))
        conn.commit()

    else:
        cursor.close()
        conn.close()
        return {"status": "error", "message": "Action must be 'like' or 'unlike'"}

    cursor.close()
    conn.close()
    return {"status": "success", "message": f"{action.capitalize()}d the post"}
