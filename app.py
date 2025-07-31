from flask import Flask, request, render_template, redirect, url_for, Markup, send_file
import os
import sqlite3
import json
import pandas as pd

app = Flask(__name__)
DB_FILE = 'results/labels.db'
IMAGE_FOLDER = 'static/images'
USERS_FILE = 'users.json'
BACKUP_CSV = 'results/backup.csv'

# Load users
with open(USERS_FILE, 'r') as f:
    USERS = json.load(f)

# Get images
IMAGES = sorted([img for img in os.listdir(IMAGE_FOLDER) if img.lower().endswith(('.jpg', '.jpeg', '.png'))])

# Ensure DB and table exists
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS labels (
            image TEXT,
            expert TEXT,
            label TEXT,
            PRIMARY KEY (image, expert)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Save label and backup
def save_label(image, expert, label):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('REPLACE INTO labels (image, expert, label) VALUES (?, ?, ?)', (image, expert, label))
    conn.commit()
    conn.close()
    backup_csv()

# Create backup.csv on each label submission
def backup_csv():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM labels", conn)
    df_pivot = df.pivot(index='image', columns='expert', values='label')
    df_pivot = df_pivot.reindex(IMAGES)  # maintain image order
    df_pivot.to_csv(BACKUP_CSV)
    conn.close()

# Get label for expert and image
def get_label(image, expert):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT label FROM labels WHERE image=? AND expert=?", (image, expert))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

# Count labeled images for an expert
def get_progress(expert):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM labels WHERE expert=?", (expert,))
    count = c.fetchone()[0]
    conn.close()
    return count

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if USERS.get(username) == password:
            return redirect(url_for('label', username=username, idx=0))
        else:
            return "Invalid credentials"
    return render_template('login.html')

@app.route('/label/<username>/<int:idx>', methods=['GET', 'POST'])
def label(username, idx):
    if username not in USERS or username == 'admin':
        return redirect(url_for('login'))

    # Skip already labeled images
    while idx < len(IMAGES) and get_label(IMAGES[idx], username) is not None:
        idx += 1

    if idx >= len(IMAGES):
        return render_template('done.html', username=username)

    if request.method == 'POST':
        choice = request.form['choice']
        save_label(IMAGES[idx], username, choice)
        return redirect(url_for('label', username=username, idx=idx + 1))

    labeled = get_progress(username)
    total = len(IMAGES)

    image_name = IMAGES[idx]
    image_url = os.path.join(IMAGE_FOLDER, image_name)

    # Find PDF with same base name
    base_name = os.path.splitext(image_name)[0]
    pdf_file = f"{base_name}.pdf"
    pdf_path = os.path.join(IMAGE_FOLDER, pdf_file)
    pdf_url = pdf_path if os.path.exists(pdf_path) else None

    return render_template('label.html', image=image_url, pdf=pdf_url,
                           username=username, idx=idx, labeled=labeled, total=total)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and USERS.get(username) == password:
            conn = sqlite3.connect(DB_FILE)
            df = pd.read_sql_query("SELECT * FROM labels", conn)
            df_pivot = df.pivot(index='image', columns='expert', values='label')
            df_pivot = df_pivot.reindex(IMAGES)
            table_html = df_pivot.fillna('').to_html(classes='data', border=1)
            conn.close()
            return render_template('admin.html', table=Markup(table_html))
        else:
            return "Invalid admin credentials"
    return render_template('admin_login.html')

@app.route('/admin/download')
def download_csv():
    return send_file(BACKUP_CSV, as_attachment=True)

if __name__ == '__main__':
    os.makedirs('results', exist_ok=True)
    app.run(debug=True)
