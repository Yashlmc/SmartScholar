import sqlite3
from datetime import datetime

class SessionManager:
    def __init__(self, db_name='sessions.db'):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                sid INTEGER PRIMARY KEY AUTOINCREMENT,
                docxset TEXT NOT NULL,
                sessionname TEXT NOT NULL,
                ctime TEXT NOT NULL,
                latime TEXT NOT NULL
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                hid INTEGER PRIMARY KEY AUTOINCREMENT,
                sid INTEGER NOT NULL,
                query TEXT NOT NULL,
                response TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY(sid) REFERENCES sessions(sid) ON DELETE CASCADE
            )
        ''')
        self.conn.commit()

    def create_session(self, docxset, sessionname):
        ctime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        latime = ctime
        self.cursor.execute('''
            INSERT INTO sessions (docxset, sessionname, ctime, latime)
            VALUES (?, ?, ?, ?)
        ''', (docxset, sessionname, ctime, latime))
        self.conn.commit()
        return self.cursor.lastrowid

    def update_last_access_time(self, sid):
        now = datetime.now().isoformat()
        self.cursor.execute('''
            UPDATE sessions SET latime = ? WHERE sid = ?
        ''', (now, sid))
        self.conn.commit()

    def add_chat_history(self, sid, query, response):
        now = datetime.now().isoformat()
        self.cursor.execute('''
            INSERT INTO history (sid, query, response, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (sid, query, response, now))
        self.conn.commit()

    def get_chat_history(self, sid):
        self.cursor.execute('''
            SELECT query, response, timestamp FROM history WHERE sid = ?
            ORDER BY hid ASC
        ''', (sid,))
        return self.cursor.fetchall()

    def get_session_by_id(self, sid):
        self.cursor.execute('SELECT * FROM sessions WHERE sid = ?', (sid,))
        return self.cursor.fetchone()

    def get_all_sessions(self):
        self.cursor.execute('SELECT * FROM sessions')
        return self.cursor.fetchall()

    def delete_session(self, sid):
        self.cursor.execute('DELETE FROM sessions WHERE sid = ?', (sid,))
        self.conn.commit()

    def get_all_docxsets(self):
        self.cursor.execute('SELECT DISTINCT docxset FROM sessions')
        result = self.cursor.fetchall()
        return [row[0] for row in result]

    def close(self):
        self.conn.close()

# Example Usage
# if __name__ == "__main__":
#     manager = SessionManager()

#     # Create a session
#     sid = manager.create_session("dataset1", "Session Alpha")
#     print(f"Session Created: SID {sid}")

#     # Add chat history
#     manager.add_chat_history(sid, "What is Python?", "Python is a programming language.")
#     manager.add_chat_history(sid, "What is SQLite?", "SQLite is a lightweight database.")

#     # Retrieve chat history
#     history = manager.get_chat_history(sid)
#     for q, r, t in history:
#         print(f"\n[{t}]\nQuery: {q}\nResponse: {r}")

#     # Close the connection
#     manager.close()
