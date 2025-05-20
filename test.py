
import sqlite3

conn = sqlite3.connect("forum.db")

conn.execute("INSERT INTO blocked_ip(ip,blocked) VALUES ('127.0.0.1',1)")
conn.commit()

print(sqlite3.connect("forum.db").execute("SELECT * FROM ip_data").fetchall())