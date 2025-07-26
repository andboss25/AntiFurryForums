import requests, json
import utils

configs = json.loads(open("config.json").read())

def MakeThread(token, identifier, name, description):
    forbidden_chars = {" ", "#", "@", "$", "%", "^", "&", "*", "(", ")", "-", "=", "+", "<", ">", "[", "]"}

    cursor, conn = utils.GeneralUtils.InnitDB()
    user = cursor.execute("SELECT username, admin FROM users WHERE token=?", (token,)).fetchone()
    if not user:
        cursor.close()
        conn.close()
        return {"status": "error", "message": "Invalid token"}

    username, is_admin = user

    if (
        len(identifier) >= 25 or
        any(char in forbidden_chars for char in identifier) or
        len(name) > 50 or
        len(description) > 200
    ):
        cursor.close()
        conn.close()
        return {"status": "error", "message": "Constraints violated"}

    if configs["ThreadAdminOnly"] and is_admin == 0:
        cursor.close()
        conn.close()
        return {"status": "error", "message": "Admins only"}

    if cursor.execute("SELECT identifier FROM threads WHERE identifier=?", (identifier,)).fetchone():
        cursor.close()
        conn.close()
        return {"status": "error", "message": "Identifier already used"}

    cursor.execute(
        "INSERT INTO threads(owner_username, name, identifier, description) VALUES (?, ?, ?, ?)",
        (username, name, identifier, description)
    )
    conn.commit()

    if configs["webhook"]:
        requests.post(configs["webhook_url"], json={"content": f"{username} created a thread '{identifier}' with name '{name}'"})

    cursor.close()
    conn.close()
    return {"status": "success", "message": "Thread created"}

def ViewThreads(token, search=False, search_for="", thread_identifier=None, filter_by_user=None):
    cursor, conn = utils.GeneralUtils.InnitDB()
    user = cursor.execute("SELECT username FROM users WHERE token=?", (token,)).fetchone()
    if not user:
        cursor.close()
        conn.close()
        return {"status": "error", "message": "Invalid token"}

    username = user[0]

    if search:
        like_term = f"%{search_for}%"
        threads = cursor.execute(
            "SELECT * FROM threads WHERE description LIKE ? OR name LIKE ? OR identifier LIKE ?",
            (like_term, like_term, like_term)
        ).fetchall()
    elif thread_identifier:
        threads = cursor.execute(
            "SELECT * FROM threads WHERE identifier=?", (thread_identifier,)
        ).fetchall()
    elif filter_by_user:
        threads = cursor.execute(
            "SELECT * FROM threads WHERE owner_username=?", (filter_by_user,)
        ).fetchall()
    else:
        threads = cursor.execute("SELECT * FROM threads").fetchall()

    subscribed = set(
        row[0] for row in cursor.execute(
            "SELECT thread_identifier FROM subscribed_threads WHERE username=?", (username,)
        ).fetchall()
    )

    thread_list = []
    for thread in threads:
        sub_count = cursor.execute(
            "SELECT COUNT(*) FROM subscribed_threads WHERE thread_identifier=?", (thread[3],)
        ).fetchone()[0]
        thread_list.append({
            "id": thread[0],
            "owner_username": thread[1],
            "name": thread[2],
            "identifier": thread[3],
            "description": thread[4],
            "subscribed": thread[3] in subscribed,
            "subscribed_count": sub_count
        })

    conn.commit()
    cursor.close()
    conn.close()
    return {"status": "success", "threads": thread_list}

def DeleteThread(token, identifier):
    cursor, conn = utils.GeneralUtils.InnitDB()
    user = cursor.execute("SELECT username FROM users WHERE token=?", (token,)).fetchone()
    if not user:
        cursor.close()
        conn.close()
        return {"status": "error", "message": "Invalid token"}

    username = user[0]
    thread = cursor.execute(
        "SELECT * FROM threads WHERE identifier=? AND owner_username=?",
        (identifier, username)
    ).fetchone()

    if not thread:
        cursor.close()
        conn.close()
        return {"status": "error", "message": "Thread not found or not owned"}

    cursor.execute("DELETE FROM threads WHERE identifier=? AND owner_username=?", (identifier, username))
    conn.commit()
    cursor.close()
    conn.close()
    return {"status": "success", "message": "Thread deleted"}

def SubscribeThread(token, identifier, action):
    action = action.lower()

    cursor, conn = utils.GeneralUtils.InnitDB()
    user = cursor.execute("SELECT username FROM users WHERE token=?", (token,)).fetchone()
    if not user:
        cursor.close()
        conn.close()
        return {"status": "error", "message": "Invalid token"}

    username = user[0]
    exists = cursor.execute("SELECT 1 FROM threads WHERE identifier=?", (identifier,)).fetchone()
    if not exists:
        cursor.close()
        conn.close()
        return {"status": "error", "message": "Thread does not exist"}

    if action == "subscribe":
        already = cursor.execute(
            "SELECT 1 FROM subscribed_threads WHERE username=? AND thread_identifier=?",
            (username, identifier)
        ).fetchone()
        if already:
            cursor.close()
            conn.close()
            return {"status": "error", "message": "Already subscribed"}

        cursor.execute(
            "INSERT INTO subscribed_threads(username, thread_identifier) VALUES (?, ?)",
            (username, identifier)
        )
    elif action == "unsubscribe":
        cursor.execute(
            "DELETE FROM subscribed_threads WHERE username=? AND thread_identifier=?",
            (username, identifier)
        )
    else:
        cursor.close()
        conn.close()
        return {"status": "error", "message": "Invalid action"}

    conn.commit()
    cursor.close()
    conn.close()
    return {"status": "success", "message": f"{action.capitalize()}d successfully"}

def ListUserSubscriptions(token):
    cursor, conn = utils.GeneralUtils.InnitDB()
    user = cursor.execute("SELECT username FROM users WHERE token=?", (token,)).fetchone()
    if not user:
        cursor.close()
        conn.close()
        return {"status": "error", "message": "Invalid token"}

    username = user[0]
    subs = cursor.execute(
        "SELECT thread_identifier FROM subscribed_threads WHERE username=?", (username,)
    ).fetchall()

    conn.commit()
    cursor.close()
    conn.close()
    return {"status": "success", "subscriptions": [x[0] for x in subs]}
