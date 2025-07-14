import sqlite3

conn = sqlite3.connect("chat.db")
cur = conn.cursor()
conn.autocommit = True

cur.execute(f"""CREATE TABLE IF NOT EXISTS people (
vk_id PRIMARY KEY,
sec_name VARCHAR(50) NOT NULL,
name VARCHAR(50) NOT NULL
)""")

cur.execute(f"""CREATE TABLE IF NOT EXISTS chat (peer_id PRIMARY KEY)""")

cur.execute(f"""CREATE TABLE IF NOT EXISTS people_chat (
id SERIAL PRIMARY KEY,
vk_id INTEGER NOT NULL REFERENCES people(vk_id),
peer_id INTEGER NOT NULL REFERENCES chat(peer_id),
msg_count INTEGER DEFAULT 0
)""")

def add_user(vk_id, sec_name, name, peer_id):
    cur.execute(f"SELECT * FROM people WHERE vk_id={vk_id}")
    if cur.fetchone() is None:
        cur.execute(f"INSERT INTO people (vk_id, sec_name, name) VALUES (?, ?, ?)", (vk_id, sec_name, name))
    cur.execute(f"SELECT * FROM people_chat WHERE vk_id=? AND peer_id=?", (vk_id, peer_id))
    if cur.fetchone() is None:
        cur.execute(f"INSERT INTO people_chat (vk_id, peer_id) VALUES (?, ?)", (vk_id, peer_id))
    
def get_user(vk_id):
    cur.execute(f"SELECT * FROM people WHERE vk_id={vk_id}")
    return cur.fetchone()

def increment_msg_count(vk_id, peer_id):
    cur.execute(f"UPDATE people_chat SET msg_count = msg_count + 1 WHERE vk_id={vk_id} AND peer_id={peer_id}")

def get_top_members(peer_id):
    cur.execute(f"SELECT * FROM people_chat WHERE peer_id={peer_id} ORDER BY msg_count DESC")
    return cur.fetchall()
