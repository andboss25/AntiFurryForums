import sqlite3

sqlite3.connect("forum.db").execute(
    "ALTER TABLE comments ADD COLUMN replies_to TEXT DEFAULT NULL;"
).close()
