
# Script to see website traffic
import sqlite3

con = sqlite3.connect("forum.db")
ips = con.execute("SELECT * FROM ip_data").fetchall()
for i in ips:
    print(f"[Ip: {i[4]} | PATH: {i[3]} | Success: {i[2]} | user name: {i[1]} | Timestamp: {i[5]}")
con.commit()
con.close()