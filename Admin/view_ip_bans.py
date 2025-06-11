
# Script to see ip bans
import sqlite3

con = sqlite3.connect("forum.db")
ips = con.execute("SELECT ip,blocked FROM blocked_ip").fetchall()
for i in ips:
    if i[1] == 1:
        banned = "blocked"
    else:
        banned = "not blocked"
    print(f"[ {i[0]} is {banned}]")
con.commit()
con.close()