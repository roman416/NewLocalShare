import os
import sqlite3
import cv2
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify, abort, send_file

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"          # общая папка для всех файлов
THUMB_FOLDER = "thumbnails"
TEMP_FOLDER = "temp_chunks"
DB = "database.db"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(THUMB_FOLDER, exist_ok=True)
os.makedirs(TEMP_FOLDER, exist_ok=True)

# ------------------ БАЗА ------------------

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with sqlite3.connect(DB) as conn:
        c = conn.cursor()
        # Удаляем старые таблицы, если они есть (для чистоты, можно закомментировать)
        c.execute("DROP TABLE IF EXISTS videos")
        c.execute("DROP TABLE IF EXISTS video_category")
        # Создаём новые таблицы
        c.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE,
            title TEXT,
            description TEXT,
            file_type TEXT,          -- 'video', 'audio', 'other'
            views INTEGER DEFAULT 0,
            length REAL,              -- для видео/аудио, иначе NULL
            filesize INTEGER,         -- размер в байтах
            upload_date TEXT
        )
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS file_category (
            file_id INTEGER,
            category_id INTEGER
        )
        """)
init_db()

# ------------------ ВСПОМОГАТЕЛЬНЫЕ ------------------

def get_file_type(filename):
    ext = filename.lower().split('.')[-1]
    video_ext = {'mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv', 'webm'}
    audio_ext = {'mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a'}
    if ext in video_ext:
        return 'video'
    elif ext in audio_ext:
        return 'audio'
    else:
        return 'other'

def get_video_length(path):
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        return None
    fps = cap.get(cv2.CAP_PROP_FPS)
    frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    cap.release()
    if fps and fps > 0:
        return round(frames / fps, 2)
    return None

def generate_thumbnail(path, file_id, time_sec=10):
    # Только для видео
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        return
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps and fps > 0:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(fps * time_sec))
    success, frame = cap.read()
    if success:
        cv2.imwrite(f"{THUMB_FOLDER}/{file_id}.jpg", frame)
    cap.release()

# ------------------ ГЛАВНАЯ ------------------

@app.route("/")
def index():
    sort = request.args.get("sort", "date")
    category = request.args.get("category")

    conn = get_db()
    c = conn.cursor()

    if category:
        query = """
        SELECT f.* FROM files f
        JOIN file_category fc ON f.id = fc.file_id
        WHERE fc.category_id = ?
        """
        params = (category,)
    else:
        query = "SELECT * FROM files"
        params = ()

    if sort == "views":
        query += " ORDER BY views DESC"
    elif sort == "length":
        query += " ORDER BY length DESC NULLS LAST"
    else:
        query += " ORDER BY upload_date DESC"

    c.execute(query, params)
    files = c.fetchall()

    c.execute("SELECT * FROM categories")
    categories = c.fetchall()

    c.execute("SELECT * FROM file_category")
    file_categories = c.fetchall()

    conn.close()

    return render_template("index.html",
                           files=files,
                           categories=categories,
                           file_categories=file_categories)

# ------------------ ДОБАВИТЬ КАТЕГОРИЮ ------------------

@app.route("/add_category", methods=["POST"])
def add_category():
    name = request.form["name"]
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        conn.commit()
        category_id = c.lastrowid
    except:
        category_id = None
    conn.close()
    return jsonify({"id": category_id, "name": name})

# ------------------ СКАН ПАПКИ ------------------

@app.route("/scan_files")
def scan_files():
    conn = get_db()
    c = conn.cursor()
    existing = c.execute("SELECT filename FROM files").fetchall()
    existing_files = {row["filename"] for row in existing}

    for file in os.listdir(UPLOAD_FOLDER):
        path = os.path.join(UPLOAD_FOLDER, file)
        if os.path.isfile(path) and file not in existing_files:
            ftype = get_file_type(file)
            filesize = os.path.getsize(path)
            length = None
            if ftype == 'video':
                length = get_video_length(path)
            # Вставляем запись
            c.execute("""
            INSERT INTO files (filename, title, description, file_type, length, filesize, upload_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (file, file, "Автоматически добавлено", ftype, length, filesize, datetime.utcnow().isoformat()))
            file_id = c.lastrowid
            if ftype == 'video':
                generate_thumbnail(path, file_id, 10)
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

# ------------------ СТРАНИЦА ФАЙЛА ------------------

@app.route("/file/<int:file_id>", methods=["GET", "POST"])
def file_page(file_id):
    conn = get_db()
    c = conn.cursor()

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        thumb_time = request.form.get("thumb_time")  # только для видео
        selected_categories = request.form.getlist("categories")

        c.execute("UPDATE files SET title=?, description=? WHERE id=?",
                  (title, description, file_id))

        c.execute("DELETE FROM file_category WHERE file_id=?", (file_id,))
        for cat in selected_categories:
            c.execute("INSERT INTO file_category VALUES (?,?)",
                      (file_id, cat))

        # Если есть thumb_time и это видео, обновляем превью
        if thumb_time and thumb_time.strip():
            c.execute("SELECT filename, file_type FROM files WHERE id=?", (file_id,))
            row = c.fetchone()
            if row and row['file_type'] == 'video':
                path = os.path.join(UPLOAD_FOLDER, row['filename'])
                generate_thumbnail(path, file_id, float(thumb_time))

        conn.commit()
        conn.close()
        return redirect(url_for("file_page", file_id=file_id))

    # Увеличиваем счётчик просмотров
    c.execute("UPDATE files SET views = views + 1 WHERE id=?", (file_id,))
    conn.commit()

    c.execute("SELECT * FROM files WHERE id=?", (file_id,))
    file = c.fetchone()
    if not file:
        abort(404)

    c.execute("SELECT * FROM categories")
    categories = c.fetchall()

    c.execute("SELECT category_id FROM file_category WHERE file_id=?", (file_id,))
    file_cats = [row["category_id"] for row in c.fetchall()]

    conn.close()

    return render_template("file.html",
                           file=file,
                           categories=categories,
                           file_cats=file_cats)

# ------------------ ЗАГРУЗКА ------------------

@app.route("/upload")
def upload_page():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM categories")
    categories = c.fetchall()
    conn.close()
    return render_template("upload.html", categories=categories)

@app.route("/upload_chunk", methods=["POST"])
def upload_chunk():
    file = request.files["file"]
    filename = request.form["filename"]
    chunk_number = int(request.form["chunk"])
    total_chunks = int(request.form["total"])

    chunk_path = os.path.join(TEMP_FOLDER, f"{filename}.part{chunk_number}")
    file.save(chunk_path)

    if chunk_number + 1 == total_chunks:
        final_path = os.path.join(UPLOAD_FOLDER, filename)
        with open(final_path, "wb") as outfile:
            for i in range(total_chunks):
                part_path = os.path.join(TEMP_FOLDER, f"{filename}.part{i}")
                with open(part_path, "rb") as infile:
                    outfile.write(infile.read())
                os.remove(part_path)

    return jsonify({"status": "ok"})

@app.route("/finalize_upload", methods=["POST"])
def finalize_upload():
    filename = request.form["filename"]
    title = request.form["title"]
    desc = request.form["description"]
    thumb_time = request.form.get("thumb_time")
    selected_categories = request.form.getlist("categories")

    path = os.path.join(UPLOAD_FOLDER, filename)
    filesize = os.path.getsize(path)
    ftype = get_file_type(filename)
    length = None
    if ftype == 'video':
        length = get_video_length(path)

    conn = get_db()
    c = conn.cursor()

    c.execute("""
    INSERT INTO files (filename, title, description, file_type, length, filesize, upload_date)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (filename, title, desc, ftype, length, filesize, datetime.utcnow().isoformat()))

    file_id = c.lastrowid

    for cat in selected_categories:
        c.execute("INSERT INTO file_category VALUES (?,?)",
                  (file_id, cat))

    conn.commit()
    conn.close()

    if ftype == 'video' and thumb_time:
        generate_thumbnail(path, file_id, float(thumb_time))

    return redirect(url_for("index"))

# ------------------ СТРАНИЦА КАТЕГОРИЙ ------------------

@app.route("/categories", methods=["GET", "POST"])
def categories_page():
    conn = get_db()
    c = conn.cursor()

    if request.method == "POST":
        name = request.form.get("name")
        if name:
            try:
                c.execute("INSERT INTO categories (name) VALUES (?)", (name,))
                conn.commit()
            except sqlite3.IntegrityError:
                pass

    c.execute("SELECT * FROM categories ORDER BY name ASC")
    categories = c.fetchall()
    conn.close()

    return render_template("categories.html", categories=categories)

# ------------------ СЕРВИНГ ФАЙЛОВ ------------------

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    """Для потокового воспроизведения (без скачивания)"""
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route("/download/<path:filename>")
def download_file(filename):
    """Принудительное скачивание"""
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

@app.route("/thumbnails/<path:filename>")
def thumb_file(filename):
    return send_from_directory(THUMB_FOLDER, filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0")