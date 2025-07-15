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
is_admin BOOLEAN DEFAULT FALSE,
is_owner BOOLEAN DEFAULT FALSE,
msg_count INTEGER DEFAULT 0
)""")

#cur.execute(f"""UPDATE people_chat SET msg_count = 20 WHERE vk_id=766134059""")

def add_user(vk_id, sec_name, name, peer_id, is_admin=False, is_owner=False):
    cur.execute(f"SELECT * FROM people WHERE vk_id={vk_id}")
    if cur.fetchone() is None:
        cur.execute(f"INSERT INTO people (vk_id, sec_name, name) VALUES (?, ?, ?)", (vk_id, sec_name, name))
    cur.execute(f"SELECT * FROM people_chat WHERE vk_id=? AND peer_id=?", (vk_id, peer_id))
    if cur.fetchone() is None:
        cur.execute(f"INSERT INTO people_chat (vk_id, peer_id, is_admin, is_owner) VALUES (?, ?, ?, ?)", (vk_id, peer_id, is_admin, is_owner))
    cur.execute(f"SELECT * FROM chat WHERE peer_id={peer_id}")
    if cur.fetchone() is None:
        cur.execute(f"INSERT INTO chat (peer_id) VALUES ({peer_id})")
    
def get_user(vk_id):
    cur.execute(f"SELECT * FROM people WHERE vk_id={vk_id}")
    return cur.fetchone()

def get_user_chat(vk_id, peer_id):
    cur.execute(f"SELECT * FROM people_chat WHERE vk_id={vk_id} AND peer_id={peer_id}")
    return cur.fetchone()

def add_admin(vk_id, peer_id):
    cur.execute(f"UPDATE people_chat SET is_admin = TRUE WHERE vk_id={vk_id} AND peer_id={peer_id}")

def increment_msg_count(vk_id, peer_id):
    cur.execute(f"UPDATE people_chat SET msg_count = msg_count + 1 WHERE vk_id={vk_id} AND peer_id={peer_id}")

def get_top_members(peer_id):
    cur.execute(f"SELECT * FROM people_chat WHERE peer_id={peer_id} ORDER BY msg_count DESC")
    return cur.fetchall()

def get_admin_members(peer_id):
    cur.execute(f"SELECT * FROM people_chat WHERE peer_id={peer_id} AND is_admin=TRUE")
    return cur.fetchall()

def get_owner(peer_id):
    cur.execute(f"SELECT * FROM people_chat WHERE peer_id={peer_id} AND is_owner=TRUE")
    return cur.fetchall()

def is_chat_existing(peer_id):
    cur.execute(f"SELECT * FROM chat WHERE peer_id={peer_id}")
    return len(cur.fetchall()) > 0

def query(sql):
    cur.execute(sql)
    return cur.fetchall()
