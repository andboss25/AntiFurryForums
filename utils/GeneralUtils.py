# General Utils (yummy)

import sqlite3
import time
import random
import base64
import hashlib
import json

# Innit db
def InnitDB():
    conn = sqlite3.connect("forum.db")
    cursor = conn.cursor()
    return (cursor,conn)

# Don't ask
# This singular pice of code was made while i was chewing on a pice of plastic
# Ts function is purely to see if skidfurs will try to attack me
def TrackIp(usr_name:None,success:bool,path:str,ip):
    cursor,conn = InnitDB()
    if success == True:
        success = 1
    else:
        success = 0

    cursor.execute("INSERT INTO ip_data(usr_name,success,path,ip,timestamp) VALUES (?,?,?,?,?)",(usr_name,success,path,ip,time.time(),))
    conn.commit()
    cursor.close()
    conn.close()

# This checks if an ip is blocked self explanatory
def IsIpBlocked(ip):
    cursor,conn = InnitDB()
    
    for ip2 in cursor.execute("SELECT * FROM blocked_ip").fetchall():
        if ip2[1] == ip:
            if ip2[2] == 1:
                return True
    
    cursor.close()
    conn.close()
    
    return False

# Token generator function
def GenerateToken(username, encrypted_password):
    username = username.lower()
    sha = hashlib.sha256()
    sha.update(encrypted_password.encode())
    part1 = sha.hexdigest()

    timestamp = str(time.time())
    sha2 = hashlib.sha256()
    sha2.update(timestamp.encode())
    part2 = sha2.hexdigest()

    token_str = part1 + timestamp + part2
    token_encoded = base64.b16encode(token_str.encode()).decode()

    token_obj = json.dumps({"username": username, "secret": token_encoded})
    return base64.b64encode(token_obj.encode()).decode()

# Check ip temp-block status and if it overflows a count of requests over 10 secs it will temp block
def CooldownCheck(ip, ips_list , time_frame=10 , request_max_count=40):
    now = time.time()
    cooldown = 15

    if ip in ips_list:
        first_request_time, is_blocked, request_count = ips_list[ip]
        if is_blocked:
            if now - first_request_time > cooldown:
                ips_list[ip] = (now, False, 1)
                return False
            return True
        else:
            if now - first_request_time <= time_frame:
                request_count += 1
                if request_count > request_max_count:
                    ips_list[ip] = (now, True, request_count)
                    return True
                else:
                    ips_list[ip] = (first_request_time, False, request_count)
                    return False
            else:
                ips_list[ip] = (now, False, 1)
                return False
    else:
        ips_list[ip] = (now, False, 1)
        return False

def GetUsernameFromToken(token:str):
    try:
        return json.loads(base64.b64decode(token).decode()).get("username")
    except:
        return None

configs = json.loads(open("config.json").read())

def Log(content,logfile=configs["logfile"]):
    if logfile == True:
        f = open("forums.log","a")
        f.write(content + "\n")
        f.close()
    else:
        print(content)

