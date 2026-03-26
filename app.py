from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from datetime import datetime

app = Flask(__name__)
CORS(app)

DB = "chat.db"
UNIVERSAL_PASSWORD = "1234"  # Change to your password

# ---------- Database Setup ----------
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ---------- Login ----------
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    password = data.get('password')
    username = data.get('username')
    if password != UNIVERSAL_PASSWORD:
        return jsonify({'status':'fail','message':'Wrong password'})
    return jsonify({'status':'ok'})

# ---------- Send Message ----------
@app.route('/send', methods=['POST'])
def send_msg():
    data = request.json
    username = data.get('username')
    message = data.get('message').strip()

    if not message:
        return jsonify({'status':'fail','message':'Empty message'})

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # ---------- Commands ----------
    # /clear
    if message.lower() == '/clear':
        c.execute('DELETE FROM messages')
        conn.commit()
        conn.close()
        return jsonify({'status':'ok','cleared':True})

    # /nick <newname>
    if message.lower().startswith('/nick '):
        newname = message[6:].strip()
        if newname:
            # Update all previous messages for this user
            c.execute('UPDATE messages SET username=? WHERE username=?', (newname, username))
            conn.commit()
            conn.close()
            return jsonify({'status':'ok','newname':newname})

    timestamp = datetime.now().isoformat()
    c.execute('INSERT INTO messages (username, message, timestamp) VALUES (?,?,?)',
              (username, message, timestamp))
    conn.commit()
    conn.close()
    return jsonify({'status':'ok'})

# ---------- Get Messages ----------
@app.route('/messages', methods=['GET'])
def get_messages():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT id, username, message, timestamp FROM messages ORDER BY id ASC')
    rows = c.fetchall()
    conn.close()
    msgs = [{'id':r[0], 'username':r[1], 'message':r[2], 'timestamp':r[3]} for r in rows]
    return jsonify(msgs)

# ---------- Edit Message ----------
@app.route('/edit', methods=['POST'])
def edit_msg():
    data = request.json
    msg_id = data.get('id')
    username = data.get('username')
    new_msg = data.get('message').strip()

    if not new_msg:
        return jsonify({'status': 'fail', 'message': 'Empty message'})

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT username FROM messages WHERE id=?', (msg_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return jsonify({'status':'fail','message':'Message not found'})
    if row[0] != username:
        conn.close()
        return jsonify({'status':'fail','message':'Cannot edit others message'})

    c.execute('UPDATE messages SET message=? WHERE id=?', (new_msg, msg_id))
    conn.commit()
    conn.close()
    return jsonify({'status':'ok'})

# ---------- Delete Message ----------
@app.route('/delete', methods=['POST'])
def delete_msg():
    data = request.json
    msg_id = data.get('id')
    username = data.get('username')

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT username FROM messages WHERE id=?', (msg_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return jsonify({'status':'fail','message':'Message not found'})
    if row[0] != username:
        conn.close()
        return jsonify({'status':'fail','message':'Cannot delete others message'})

    c.execute('DELETE FROM messages WHERE id=?', (msg_id,))
    conn.commit()
    conn.close()
    return jsonify({'status':'ok'})

if __name__ == '__main__':
    app.run(debug=True)