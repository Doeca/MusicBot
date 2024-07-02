import sqlite3
import threading
database_name = './config/adbaner/msgs.db'
conn = sqlite3.connect(database_name)
db_lock = threading.Lock()

def init_db():
    cursor = conn.cursor()
    check_table_query = '''
        SELECT name FROM sqlite_master WHERE type='table' AND name='msglog';
    '''
    with db_lock:
        cursor.execute(check_table_query)
        table_exists = cursor.fetchone()
        if not table_exists:
            create_table_query = '''
                CREATE TABLE msglog (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data TEXT NOT NULL,
                    type TEXT,
                    groupid INTEGER,
                    userid INTEGER,
                    sendtime TEXT DEFAULT (datetime('now', 'localtime'))
                );
            '''
            cursor.execute(create_table_query)
            print("Table 'msglog' created.")
        cursor.close()
        conn.commit()

# type:text,image
# data: the img path when type is image
def insert_data(type: str, data: str, groupid: int, userid: int):
    with db_lock:
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO msglog (data, type, groupid, userid) VALUES (?, ?, ?, ?)
    ''', (data, type, groupid, userid))
        cursor.close()
        conn.commit()
