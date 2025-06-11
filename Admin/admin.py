
# Script to make an account admin
import sqlite3

username = input("Enter a username to make their account admin: ")
con = sqlite3.connect("forum.db")
con.execute("UPDATE users SET admin=1 WHERE username=?",(username,))
con.commit()
con.close()