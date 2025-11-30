# app.py

from flask import Flask, render_template, request, redirect, url_for, jsonify
import database as db
import datetime

app = Flask(__name__)
db.init_db()

@app.route('/', methods=['GET', 'POST'])
def index():
    tag_filter = request.args.get('tag')
    
    if request.method == 'POST':
        task_text = request.form['task']
        
        if task_text.strip():
            # Tags are no longer added via the main form
            db.add_task(task_text) 
        
        current_filter = request.args.get('filter', 'all')
        if tag_filter:
             return redirect(url_for('index', filter=current_filter, tag=tag_filter))
        return redirect(url_for('index', filter=current_filter))

    current_filter = request.args.get('filter', 'all')
    
    tasks = db.get_tasks(filter_by=current_filter, tag_filter=tag_filter)
    
    # Use the fixed list of tags from the database module
    all_tags = db.get_all_unique_tags() 

    # Calculate Progress
    progress_data = db.get_completion_stats()
    
    total_tasks = progress_data['total_tasks']
    completed_tasks = progress_data['completed_tasks']
    
    if total_tasks > 0:
        completion_percentage = round((completed_tasks / total_tasks) * 100)
    else:
        completion_percentage = 0

    return render_template('index.html', 
        tasks=tasks, 
        current_filter=current_filter,
        all_tags=all_tags,
        tag_filter=tag_filter,
        completion_percentage=completion_percentage,
        completed_tasks=completed_tasks,
        total_tasks=total_tasks
    )

@app.route('/edit/<int:task_id>', methods=['POST'])
def edit(task_id):
    new_text = request.form['new_task_text']
    if new_text.strip():
        db.update_task(task_id, new_text)
    current_filter = request.form.get('current_filter', 'all')
    tag_filter = request.form.get('tag_filter')
    if tag_filter:
        return redirect(url_for('index', filter=current_filter, tag=tag_filter))
    return redirect(url_for('index', filter=current_filter))

@app.route('/toggle/<int:task_id>', methods=['POST'])
def toggle(task_id):
    db.toggle_task_status(task_id)
    current_filter = request.form.get('current_filter', 'all')
    tag_filter = request.form.get('tag_filter')
    if tag_filter:
        return redirect(url_for('index', filter=current_filter, tag=tag_filter))
    return redirect(url_for('index', filter=current_filter))

@app.route('/pin/<int:task_id>', methods=['POST'])
def pin(task_id):
    db.toggle_pin_status(task_id)
    current_filter = request.form.get('current_filter', 'all')
    tag_filter = request.form.get('tag_filter')
    if tag_filter:
        return redirect(url_for('index', filter=current_filter, tag=tag_filter))
    return redirect(url_for('index', filter=current_filter))

@app.route('/color/<int:task_id>', methods=['POST'])
def color(task_id):
    new_color = request.form['color']
    db.update_task_color(task_id, new_color)
    current_filter = request.form.get('current_filter', 'all')
    tag_filter = request.form.get('tag_filter')
    if tag_filter:
        return redirect(url_for('index', filter=current_filter, tag=tag_filter))
    return redirect(url_for('index', filter=current_filter))

@app.route('/delete/<int:task_id>', methods=['POST'])
def delete(task_id):
    db.delete_task(task_id)
    current_filter = request.form.get('current_filter', 'all')
    tag_filter = request.form.get('tag_filter')
    if tag_filter:
        return redirect(url_for('index', filter=current_filter, tag=tag_filter))
    return redirect(url_for('index', filter=current_filter))

@app.route('/clear-completed', methods=['POST'])
def clear_completed():
    db.clear_completed_tasks()
    current_filter = request.form.get('current_filter', 'all')
    tag_filter = request.form.get('tag_filter')
    if tag_filter:
        return redirect(url_for('index', filter=current_filter, tag=tag_filter))
    return redirect(url_for('index', filter=current_filter))

# --- API Routes ---

@app.route('/api/task-details/<int:task_id>', methods=['GET'])
def task_details_api(task_id):
    task = db.get_task_by_id(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404

    task_dict = task

    # --- Time Remaining and Warning Logic ---
    time_remaining_str = None
    warning_message = None
    
    if task_dict['due_date']:
        try:
            due_date_dt = datetime.datetime.strptime(task_dict['due_date'], '%Y-%m-%d')
            now = datetime.datetime.now()
            due_date_end_of_day = due_date_dt.replace(hour=23, minute=59, second=59)

            if task_dict['completed'] == 1 and now > due_date_end_of_day:
                warning_message = "✅ Completed after deadline."
            elif task_dict['completed'] == 1:
                warning_message = "✅ Completed on time."
            elif now > due_date_end_of_day:
                warning_message = "⚠️ Did not complete the task on time"
            else:
                delta = due_date_end_of_day - now
                days = delta.days
                hours = int(delta.seconds / 3600)
                
                if days > 0:
                    time_remaining_str = f"{days} days and {hours} hours remaining"
                else:
                    time_remaining_str = f"{hours} hours remaining"
                    
        except ValueError:
            pass

    task_dict['time_remaining'] = time_remaining_str
    task_dict['warning_message'] = warning_message
    
    # Format timestamps nicely for display
    # Check if timestamps are not None before splitting
    created_at = task_dict.get('created_at')
    updated_at = task_dict.get('updated_at')

    if created_at:
        task_dict['created_at_display'] = datetime.datetime.strptime(created_at.split('.')[0], '%Y-%m-%d %H:%M:%S').strftime('%b %d, %Y at %I:%M %p')
    else:
        task_dict['created_at_display'] = 'N/A'
        
    if updated_at:
        task_dict['updated_at_display'] = datetime.datetime.strptime(updated_at.split('.')[0], '%Y-%m-%d %H:%M:%S').strftime('%b %d, %Y at %I:%M %p')
    else:
        task_dict['updated_at_display'] = 'N/A'

    return jsonify(task_dict)

@app.route('/set-duedate/<int:task_id>', methods=['POST'])
def set_duedate(task_id):
    new_due_date = request.form['due_date']
    db.update_task_duedate(task_id, new_due_date if new_due_date else None)
    return jsonify({'status': 'success'})

@app.route('/api/reorder', methods=['POST'])
def reorder_tasks():
    data = request.json
    task_ids = data.get('task_ids', [])
    
    if not task_ids:
        return jsonify({'status': 'error', 'message': 'No task IDs provided'}), 400

    for index, task_id in enumerate(task_ids):
        db.update_task_position(int(task_id), index + 1)
        
    return jsonify({'status': 'success'}), 200

@app.route('/api/tags/<int:task_id>', methods=['POST', 'DELETE'])
def manage_task_tags(task_id):
    tag_name = request.json.get('tag_name').strip().lower()
    
    if not tag_name:
        return jsonify({'status': 'error', 'message': 'Tag name required'}), 400
    
    # Enforce that only tags from the fixed list can be added/managed
    if tag_name not in db.FIXED_TAGS:
        return jsonify({'status': 'error', 'message': f'Tag "{tag_name}" is not a valid predefined tag.'}), 400

    if request.method == 'POST':
        # Add a single tag
        db.add_tags_to_task(task_id, [tag_name])
        return jsonify({'status': 'added', 'tag': tag_name}), 201
    
    elif request.method == 'DELETE':
        # Remove a single tag
        if db.remove_tag_from_task(task_id, tag_name):
            return jsonify({'status': 'removed', 'tag': tag_name}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Tag not found on task'}), 404


if __name__ == '__main__':
    app.run(debug=True, port=5001)