from flask import Flask, render_template, request, redirect, url_for, send_file
import os
import sqlite3
from werkzeug.utils import secure_filename
from datetime import datetime
from io import BytesIO
from fpdf import FPDF
import smtplib
from email.message import EmailMessage

# Konfiguration
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
DATABASE = os.path.join(os.path.dirname(__file__), 'reports.db')

# Opret database hvis den ikke findes
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

# Tjek filtype
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Forside – opret rapport
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
        return redirect(url_for('rapporter'))

    init_db()
    return render_template('index.html')

# Oversigt over rapporter
@app.route('/rapporter')
def rapporter():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT id, timestamp, location, subject FROM reports ORDER BY timestamp DESC")
    reports = cur.fetchall()
    conn.close()
    return render_template('rapporter.html', reports=reports)

# Vis enkelt rapport
@app.route('/rapport/<int:report_id>')
def vis_rapport(report_id):
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT timestamp, location, subject FROM reports WHERE id=?", (report_id,))
    report = cur.fetchone()
    cur.execute("SELECT time, description, image FROM entries WHERE report_id=?", (report_id,))
    entries = cur.fetchall()
    conn.close()
    return render_template('rapport.html', report=report, entries=entries, report_id=report_id)

# Download som PDF
@app.route('/rapport/<int:report_id>/pdf')
def download_pdf(report_id):
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT timestamp, location, subject FROM reports WHERE id=?", (report_id,))
    report = cur.fetchone()
    cur.execute("SELECT time, description FROM entries WHERE report_id=?", (report_id,))
    entries = cur.fetchall()
    conn.close()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Bjærgningsrapport", ln=True, align='C')
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Sted: {report[1]}", ln=True)
    pdf.cell(200, 10, txt=f"Opgave: {report[2]}", ln=True)
    pdf.cell(200, 10, txt=f"Dato: {report[0][:16].replace('T', ' ')}", ln=True)
    pdf.ln(10)
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(200, 10, txt="Hændelsesforløb:", ln=True)
    pdf.set_font("Arial", size=11)

    for time, desc in
