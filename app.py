from flask import Flask, render_template, request, redirect, url_for
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import sqlite3

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
DATABASE = os.path.join(os.path.dirname(__file__), 'reports.db')

# Opret databasen hvis den ikke findes
def init_db():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY,
        timestamp TEXT,
        location TEXT,
        subject TEXT
    )''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS entries (
        id INTEGER PRIMARY KEY,
        report_id INTEGER,
        time TEXT,
        description TEXT,
        image TEXT,
        FOREIGN KEY(report_id) REFERENCES reports(id)
    )''')
    conn.commit()
    conn.close()

# Tjek om billede må uploades
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Forside – indtast rapport
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        location = request.form['location']
        subject = request.form['subject']
        timestamp = datetime.now().isoformat()
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        cur.execute("INSERT INTO reports(timestamp, location, subject) VALUES (?, ?, ?)",
                    (timestamp, location, subject))
        report_id = cur.lastrowid

        times = request.form.getlist('entry_time')
        descs = request.form.getlist('entry_desc')
        images = request.files.getlist('entry_image')

        for t, d, f in zip(times, descs, images):
            filename = ''
            if f and allowed_file(f.filename):
                filename = secure_filename(f.filename)
                f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            cur.execute("INSERT INTO entries(report_id, time, description, image) VALUES (?, ?, ?, ?)",
                        (report_id, t, d, filename))

        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    init_db()
    return render_template('index.html')

# Vis alle rapporter
@app.route('/rapporter')
def rapporter():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT id, timestamp, location, subject FROM reports ORDER BY timestamp DESC")
    reports = cur.fetchall()
    conn.close()
    return render_template('rapporter.html', reports=reports)

# Vis detaljer for én rapport
@app.route('/rapport/<int:report_id>')
def vis_rapport(report_id):
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT timestamp, location, subject FROM reports WHERE id=?", (report_id,))
    report = cur.fetchone()
    cur.execute("SELECT time, description, image FROM entries WHERE report_id=?", (report_id,))
    entries = cur.fetchall()
    conn.close()
    return render_template('rapport.html', report=report, entries=entries)

if __name__ == '__main__':
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)