import sqlite3
from sqlite3 import Connection
from pathlib import Path
import hashlib
import pandas as pd
from typing import List, Dict, Any, Optional
DB_PATH = Path(__file__).parent.parent / 'data' / 'db.sqlite3'
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def get_conn() -> Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("\n\n        CREATE TABLE IF NOT EXISTS users (\n\n            user_id INTEGER PRIMARY KEY AUTOINCREMENT,\n\n            username TEXT UNIQUE NOT NULL,\n\n            password_hash TEXT NOT NULL,\n\n            role TEXT NOT NULL CHECK(role IN ('student','admin')),\n\n            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n\n        );\n\n        ")
    cur.execute("\n\n        CREATE TABLE IF NOT EXISTS complaints (\n\n            complaint_id INTEGER PRIMARY KEY AUTOINCREMENT,\n\n            student_username TEXT NOT NULL,\n\n            text TEXT NOT NULL,\n\n            predicted_category TEXT,\n\n            confidence REAL,\n\n            status TEXT NOT NULL DEFAULT 'Pending',\n\n            file_path TEXT,\n\n            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n\n            FOREIGN KEY(student_username) REFERENCES users(username)\n\n        );\n\n        ")
    cur.execute("\n\n        CREATE TABLE IF NOT EXISTS results (\n\n            result_id INTEGER PRIMARY KEY AUTOINCREMENT,\n\n            student_username TEXT NOT NULL,\n\n            course_code TEXT NOT NULL,\n\n            course_name TEXT,\n\n            semester TEXT,\n\n            marks TEXT,\n\n            status TEXT CHECK(status IN ('Pass','Fail','Backlog')) DEFAULT 'Pass',\n\n            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n\n            FOREIGN KEY(student_username) REFERENCES users(username)\n\n        );\n\n        ")
    cur.execute('\n        CREATE TABLE IF NOT EXISTS resolution_updates (\n            update_id INTEGER PRIMARY KEY AUTOINCREMENT,\n            complaint_id INTEGER NOT NULL,\n            admin_username TEXT NOT NULL,\n            note_text TEXT,\n            file_paths TEXT,\n            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n            FOREIGN KEY(complaint_id) REFERENCES complaints(complaint_id),\n            FOREIGN KEY(admin_username) REFERENCES users(username)\n        );\n        ')
    cur.execute("\n        CREATE TABLE IF NOT EXISTS complaint_messages (\n            message_id INTEGER PRIMARY KEY AUTOINCREMENT,\n            complaint_id INTEGER NOT NULL,\n            sender_username TEXT NOT NULL,\n            sender_role TEXT NOT NULL CHECK(sender_role IN ('student', 'admin')),\n            message_text TEXT,\n            file_paths TEXT,\n            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n            FOREIGN KEY(complaint_id) REFERENCES complaints(complaint_id),\n            FOREIGN KEY(sender_username) REFERENCES users(username)\n        );\n        ")
    cur.execute('CREATE INDEX IF NOT EXISTS idx_results_student ON results(student_username);')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_complaints_student ON complaints(student_username);')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_resolution_complaint ON resolution_updates(complaint_id);')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_messages_complaint ON complaint_messages(complaint_id);')
    try:
        cur.execute('ALTER TABLE complaints ADD COLUMN file_path TEXT;')
    except Exception:
        pass
    try:
        cur.execute('ALTER TABLE complaints ADD COLUMN course_code TEXT;')
    except Exception:
        pass
    try:
        cur.execute('ALTER TABLE complaints ADD COLUMN semester TEXT;')
    except Exception:
        pass
    try:
        cur.execute('ALTER TABLE complaints ADD COLUMN duplicate_reference INTEGER;')
    except Exception:
        pass
    conn.commit()
    conn.close()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def create_user(username: str, password: str, role: str='student') -> bool:
    conn = get_conn()
    try:
        conn.execute('INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)', (username, hash_password(password), role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.execute('SELECT user_id, username, role, created_at FROM users WHERE username = ?', (username,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def verify_user(username: str, password: str) -> bool:
    conn = get_conn()
    cur = conn.execute('SELECT password_hash FROM users WHERE username = ?', (username,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return False
    return hash_password(password) == row['password_hash']

def add_complaint(student_username: str, text: str, predicted_category: Optional[str]=None, confidence: Optional[float]=None, file_path: Optional[str]=None, course_code: Optional[str]=None, semester: Optional[str]=None, duplicate_reference: Optional[int]=None) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('INSERT INTO complaints (student_username, text, predicted_category, confidence, file_path, course_code, semester, duplicate_reference) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (student_username, text, predicted_category, confidence, file_path, course_code, semester, duplicate_reference))
    complaint_id = cur.lastrowid
    conn.commit()
    conn.close()
    return complaint_id

def get_complaints_by_student(student_username: str) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.execute('SELECT * FROM complaints WHERE student_username = ? ORDER BY created_at DESC', (student_username,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def get_all_complaints(limit: int=100) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.execute('SELECT * FROM complaints ORDER BY created_at DESC LIMIT ?', (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def update_complaint_status(complaint_id: int, status: str):
    conn = get_conn()
    conn.execute('UPDATE complaints SET status = ? WHERE complaint_id = ?', (status, complaint_id))
    conn.commit()
    conn.close()

def delete_complaint(complaint_id: int) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute('DELETE FROM complaint_messages WHERE complaint_id = ?', (complaint_id,))
        cur.execute('DELETE FROM resolution_updates WHERE complaint_id = ?', (complaint_id,))
        cur.execute('DELETE FROM complaints WHERE complaint_id = ?', (complaint_id,))
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        conn.rollback()
        return False
    finally:
        conn.close()

def update_complaint_category(complaint_id: int, category: str, confidence: Optional[float]=None):
    conn = get_conn()
    if confidence is not None:
        conn.execute('UPDATE complaints SET predicted_category = ?, confidence = ? WHERE complaint_id = ?', (category, confidence, complaint_id))
    else:
        conn.execute('UPDATE complaints SET predicted_category = ? WHERE complaint_id = ?', (category, complaint_id))
    conn.commit()
    conn.close()

def add_resolution_update(complaint_id: int, admin_username: str, note_text: Optional[str]=None, file_paths: Optional[str]=None) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('INSERT INTO resolution_updates (complaint_id, admin_username, note_text, file_paths) VALUES (?, ?, ?, ?)', (complaint_id, admin_username, note_text, file_paths))
    update_id = cur.lastrowid
    conn.commit()
    conn.close()
    return update_id

def get_resolution_updates(complaint_id: int) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.execute('SELECT * FROM resolution_updates WHERE complaint_id = ? ORDER BY created_at DESC', (complaint_id,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def add_complaint_message(complaint_id: int, sender_username: str, sender_role: str, message_text: Optional[str]=None, file_paths: Optional[str]=None) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('INSERT INTO complaint_messages (complaint_id, sender_username, sender_role, message_text, file_paths) VALUES (?, ?, ?, ?, ?)', (complaint_id, sender_username, sender_role, message_text, file_paths))
    message_id = cur.lastrowid
    conn.commit()
    conn.close()
    return message_id

def get_complaint_messages(complaint_id: int) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.execute('SELECT * FROM complaint_messages WHERE complaint_id = ? ORDER BY created_at ASC', (complaint_id,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def add_result(student_username: str, course_code: str, course_name: Optional[str], semester: Optional[str], marks: str, status: str='Pass'):
    conn = get_conn()
    conn.execute('INSERT INTO results (student_username, course_code, course_name, semester, marks, status) VALUES (?, ?, ?, ?, ?, ?)', (student_username, course_code, course_name, semester, marks, status))
    conn.commit()
    conn.close()

def get_results_by_student(student_username: str) -> List[Dict[str, Any]]:
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    cleaned_username = str(student_username).replace(',', '').strip()
    cur = conn.execute('SELECT * FROM results WHERE student_username = ? ORDER BY uploaded_at DESC', (cleaned_username,))
    rows = cur.fetchall()
    if not rows:
        cur = conn.execute("SELECT * FROM results WHERE TRIM(REPLACE(student_username, ',', '')) = ? ORDER BY uploaded_at DESC", (cleaned_username,))
        rows = cur.fetchall()
    result = [dict(r) for r in rows]
    conn.close()
    return result

def import_results_from_dataframe(df: pd.DataFrame) -> Dict[str, int]:
    required = {'student_username', 'course_code'}
    if not required.issubset(set(df.columns)):
        raise ValueError(f'CSV must contain columns: {required}')
    conn = get_conn()
    inserted = 0
    errors = []
    try:
        for idx, row in df.iterrows():
            try:
                student_username = str(row.get('student_username')).replace(',', '').strip()
                if not student_username:
                    errors.append(f'Row {idx}: Empty student_username')
                    continue
                course_code = str(row.get('course_code'))
                if not course_code:
                    errors.append(f'Row {idx}: Empty course_code')
                    continue
                course_name = row.get('course_name', None)
                if pd.isna(course_name):
                    course_name = None
                else:
                    course_name = str(course_name)
                semester = row.get('semester', None)
                if pd.isna(semester):
                    semester = None
                else:
                    semester = str(semester)
                marks = str(row.get('marks', '')) if not pd.isna(row.get('marks')) else ''
                status = str(row.get('status', 'Pass')) if not pd.isna(row.get('status')) else 'Pass'
                conn.execute('INSERT INTO results (student_username, course_code, course_name, semester, marks, status) VALUES (?, ?, ?, ?, ?, ?)', (student_username, course_code, course_name, semester, marks, status))
                inserted += 1
            except Exception as e:
                errors.append(f'Row {idx}: {str(e)}')
                continue
        conn.commit()
        if errors:
            import sys
            print(f'Import completed with {len(errors)} errors:', file=sys.stderr)
            for err in errors[:10]:
                print(f'  {err}', file=sys.stderr)
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
    return {'inserted': inserted, 'errors': len(errors)}

def insert_sample_results() -> Dict[str, int]:
    conn = get_conn()
    cur = conn.cursor()
    sample_data = [('12213089', 'ITPC204', 'ML', '4', '56', 'Pass'), ('12213085', 'ITPC604', 'COA', '4', '54', 'Pass'), ('12213003', 'ITPC204', 'ML', '4', '23', 'Fail'), ('12213074', 'ITPC304', 'Java', '4', '36', 'Fail'), ('12213053', 'ITPC604', 'COA', '4', '33', 'Fail'), ('12213050', 'ITPC204', 'ML', '4', '7', 'Fail'), ('12213169', 'ITPC404', 'DSA', '4', '70', 'Pass'), ('12213030', 'ITPC604', 'COA', '4', '3', 'Fail'), ('12213012', 'ITPC604', 'COA', '4', '4', 'Fail'), ('12213169', 'ITPC604', 'COA', '4', '4', 'Fail'), ('12213094', 'ITPC204', 'ML', '4', '65', 'Pass'), ('12213094', 'ITPC304', 'Java', '4', '72', 'Pass'), ('12213095', 'ITPC404', 'DSA', '4', '58', 'Pass'), ('12213095', 'ITPC604', 'COA', '4', '42', 'Fail')]
    inserted = 0
    try:
        for student_username, course_code, course_name, semester, marks, status in sample_data:
            cleaned_username = str(student_username).replace(',', '').strip()
            cur.execute('SELECT COUNT(*) FROM results WHERE student_username = ? AND course_code = ?', (cleaned_username, course_code))
            if cur.fetchone()[0] == 0:
                cur.execute('INSERT INTO results (student_username, course_code, course_name, semester, marks, status) VALUES (?, ?, ?, ?, ?, ?)', (cleaned_username, course_code, course_name, semester, marks, status))
                inserted += 1
        conn.commit()
        return {'inserted': inserted, 'total': len(sample_data)}
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def fix_student_username_commas() -> Dict[str, int]:
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute('SELECT result_id, student_username FROM results')
        rows_to_fix = cur.fetchall()
        updated_count = 0
        for row in rows_to_fix:
            result_id = row['result_id']
            old_username = row['student_username']
            new_username = str(old_username).replace(',', '').strip()
            if new_username != str(old_username):
                cur.execute('UPDATE results SET student_username = ? WHERE result_id = ?', (new_username, result_id))
                updated_count += 1
        conn.commit()
        return {'updated': updated_count, 'checked': len(rows_to_fix)}
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()