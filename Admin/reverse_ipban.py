
# Script to unban an ip
import sqlite3

ip = input("Enter a ip you want to unban: ")
con = sqlite3.connect("forum.db")
con.execute("UPDATE blocked_ip SET blocked=? WHERE ip=?",(0,ip))
con.commit()
con.close()