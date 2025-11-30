# database.py

import sqlite3
import datetime

DB_FILE = "todo.db"

# --- FIXED TAG LIST ---
FIXED_TAGS = ['personal', 'office', 'urgent', 'shopping']
# ----------------------

def init_db():
    """Initializes the database and creates the 'tasks' table with new columns, including due_date and position."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT NOT NULL,
                completed BOOLEAN NOT NULL DEFAULT 0,
                pinned BOOLEAN NOT NULL DEFAULT 0,
                color TEXT DEFAULT '#ffffff',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                due_date TEXT,
                position INTEGER
            )
        """)
        
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS update_tasks_updated_at
            AFTER UPDATE ON tasks
            FOR EACH ROW
            BEGIN
                UPDATE tasks SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
            END;
        """)
        
        # --- Tables for Tags ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_tags (
                task_id INTEGER,
                tag_id INTEGER,
                FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE,
                UNIQUE (task_id, tag_id)
            )
        """)
        # ---------------------------

        conn.commit()
    print("Database initialized with new schema.")

# --- Tag Management Functions (Modified get_all_unique_tags) ---
def _add_tag_to_db(tag_name):
    """Adds a tag name to the tags table if it doesn't exist, returns the ID."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # Insert tag, ignoring if it already exists
        cursor.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name.lower(),))
        # Retrieve the ID of the tag (whether inserted or already existing)
        cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name.lower(),))
        return cursor.fetchone()[0]

def add_tags_to_task(task_id, tags):
    """Adds a list of tags to a specific task. Enforces FIXED_TAGS."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # Enforce fixed tags by checking if the tag exists in the FIXED_TAGS list
        valid_tags = [tag.strip().lower() for tag in tags if tag.strip().lower() in FIXED_TAGS]
        
        for tag_name in valid_tags:
            tag_id = _add_tag_to_db(tag_name)
            try:
                cursor.execute("INSERT INTO task_tags (task_id, tag_id) VALUES (?, ?)", (task_id, tag_id))
            except sqlite3.IntegrityError:
                continue
        conn.commit()

def remove_tag_from_task(task_id, tag_name):
    """Removes a specific tag from a task."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name.lower(),))
        tag_id_data = cursor.fetchone()
        if tag_id_data:
            tag_id = tag_id_data[0]
            cursor.execute("DELETE FROM task_tags WHERE task_id = ? AND tag_id = ?", (task_id, tag_id))
            conn.commit()
            return True
        return False
        
def get_tags_for_task(task_id):
    """Fetches all tags associated with a specific task."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.name FROM tags t
            JOIN task_tags tt ON t.id = tt.tag_id
            WHERE tt.task_id = ?
            ORDER BY t.name
        """, (task_id,))
        return [row[0] for row in cursor.fetchall()]

def get_all_unique_tags():
    """Returns the fixed list of allowable tags for display/filtering."""
    return FIXED_TAGS

# --- Progress Calculation Function ---
def get_completion_stats():
    """Calculates the total number of tasks and the number of completed tasks."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(id) FROM tasks")
        total_tasks = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(id) FROM tasks WHERE completed = 1")
        completed_tasks = cursor.fetchone()[0]
        
        return {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks
        }
# ----------------------------------------

# --- Core Task Functions ---
def get_tasks(filter_by='all', tag_filter=None):
    """Fetches tasks with filtering, and sorting by pinned status and then position."""
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT t.* FROM tasks t"
        where_clauses = []
        params = []
        
        if tag_filter:
            query += " JOIN task_tags tt ON t.id = tt.task_id JOIN tags g ON tt.tag_id = g.id"
            where_clauses.append("g.name = ?")
            params.append(tag_filter.lower())

        if filter_by == 'done':
            where_clauses.append("t.completed = 1")
        elif filter_by == 'undone':
            where_clauses.append("t.completed = 0")
        elif filter_by == 'pinned':
            where_clauses.append("t.pinned = 1")
        
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        query += " ORDER BY t.pinned DESC, t.position ASC, t.updated_at DESC"
        
        cursor.execute(query, params)
        tasks = cursor.fetchall()

        tasks_with_tags = []
        for task in tasks:
            task_dict = dict(task)
            task_dict['tags'] = get_tags_for_task(task['id'])
            tasks_with_tags.append(task_dict)
            
        return tasks_with_tags

def add_task(task_text):
    """Adds a new task without tags, as tags are now added only in the modal."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT MAX(position) FROM tasks")
        max_position = cursor.fetchone()[0]
        new_position = (max_position or 0) + 1

        cursor.execute("INSERT INTO tasks (task, position) VALUES (?, ?)", (task_text, new_position))
        task_id = cursor.lastrowid
        conn.commit()
        
        return task_id

def update_task(task_id, new_text):
    """Updates the text of an existing task."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE tasks SET task = ? WHERE id = ?", (new_text, task_id))
        conn.commit()

def toggle_task_status(task_id):
    """Toggles the 'completed' status of a task."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE tasks SET completed = NOT completed WHERE id = ?", (task_id,))
        conn.commit()

def toggle_pin_status(task_id):
    """Toggles the 'pinned' status of a task."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE tasks SET pinned = NOT pinned WHERE id = ?", (task_id,))
        conn.commit()

def update_task_color(task_id, color):
    """Updates the color of a task."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE tasks SET color = ? WHERE id = ?", (color, task_id))
        conn.commit()

def update_task_duedate(task_id, due_date):
    """Updates the due date of a task."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE tasks SET due_date = ? WHERE id = ?", (due_date, task_id))
        conn.commit()

def update_task_position(task_id, new_position):
    """Updates the position of a single task after drag-and-drop."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE tasks SET position = ? WHERE id = ?", (new_position, task_id))
        conn.commit()

def delete_task(task_id):
    """Deletes a task from the database (Cascades handle tag links)."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()

def clear_completed_tasks():
    """Deletes all tasks marked as completed."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE completed = 1")
        conn.commit()

def get_task_by_id(task_id):
    """Fetches a single task by its ID."""
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        task = cursor.fetchone()
        if task:
            task_dict = dict(task)
            task_dict['tags'] = get_tags_for_task(task['id'])
            return task_dict
        return None