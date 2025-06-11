
# Script to ban an ip
import sqlite3

ip = input("Enter a ip you want to ban: ")
con = sqlite3.connect("forum.db")
con.execute("UPDATE blocked_ip SET blocked=? WHERE ip=?",(1,ip))
con.execute("INSERT INTO blocked_ip(ip,blocked) VALUES (?,?)",(ip,1))
con.commit()
con.close()