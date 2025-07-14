import sqlite3

conn = sqlite3.connect("chat.db")

class Member:
    def __init__(self):
        self._cur = conn.cursor()
        conn.autocommit = True
        self._cur.execute("""CREATE TABLE IF NOT EXISTS people (
        vk_id PRIMARY KEY,
        sec_name VARCHAR(50) NOT NULL,
        name VARCHAR(50) NOT NULL,
        msg_count INTEGER DEFAULT 0
        )""")
        
    def add_user(self, vk_id, sec_name, name):
        self._cur.execute(f"INSERT INTO people (vk_id, sec_name, name) VALUES (?, ?, ?)", (vk_id, sec_name, name))

    def get_user(self, vk_id):
        self._cur.execute(f"SELECT * FROM people WHERE vk_id={vk_id}")
        return self._cur.fetchone()

    def increment_msg_count(self, vk_id):
        self._cur.execute(f"UPDATE people SET msg_count = msg_count + 1 WHERE vk_id={vk_id}")

