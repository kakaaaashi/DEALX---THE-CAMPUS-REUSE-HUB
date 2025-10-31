# DealX - Final ready-to-deploy app.py
import os, sqlite3, time, tempfile
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename

# Optional cloudinary support
try:
    import cloudinary
    import cloudinary.uploader
    CLOUDINARY_AVAILABLE = True
except Exception:
    CLOUDINARY_AVAILABLE = False

APP_NAME = "DealX"
DB_NAME = "items.db"
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {'png','jpg','jpeg','gif'}

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY','dealxsecretkey')
app.config['APP_NAME'] = APP_NAME
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price TEXT NOT NULL,
        description TEXT,
        contact TEXT,
        image TEXT,
        stars REAL DEFAULT 0,
        created_at REAL DEFAULT (strftime('%s','now'))
    )''')
    conn.commit()
    conn.close()

# Configure cloudinary if environment provided
if CLOUDINARY_AVAILABLE:
    cloudinary_url = os.environ.get('CLOUDINARY_URL')
    if cloudinary_url:
        try:
            cloudinary.config(cloudinary_url=cloudinary_url)
        except Exception:
            pass
    else:
        cn = os.environ.get('CLOUD_NAME')
        ck = os.environ.get('CLOUDINARY_API_KEY')
        cs = os.environ.get('CLOUDINARY_API_SECRET')
        if cn and ck and cs:
            try:
                cloudinary.config(cloud_name=cn, api_key=ck, api_secret=cs)
            except Exception:
                pass

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

def upload_to_cloudinary(file_storage):
    if not CLOUDINARY_AVAILABLE:
        raise RuntimeError('cloudinary library not available')
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        file_storage.save(tmp.name)
        tmp.flush()
        tmp_path = tmp.name
    try:
        res = cloudinary.uploader.upload(tmp_path, folder='dealx_uploads', use_filename=True, unique_filename=False, resource_type='image')
        return res.get('secure_url')
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass

@app.before_first_request
def startup():
    # initialize DB before handling requests
    init_db()

@app.route('/')
def home():
    conn = get_db_connection()
    items = conn.execute("SELECT * FROM items ORDER BY created_at DESC LIMIT 6").fetchall()
    conn.close()
    return render_template('home.html', items=items, config=app.config)

@app.route('/items')
def items():
    conn = get_db_connection()
    items = conn.execute("SELECT * FROM items ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template('items.html', items=items, config=app.config)

@app.route('/about')
def about():
    return render_template('about.html', config=app.config)

@app.route('/add', methods=['GET','POST'])
def add_item():
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        price = request.form.get('price','').strip()
        desc = request.form.get('desc','').strip()
        contact = request.form.get('contact','').strip()
        stars = request.form.get('stars') or 0
        try:
            stars = float(stars)
        except:
            stars = 0.0
        image_path = None
        image_file = request.files.get('image')
        if image_file and image_file.filename and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            filename = f"{int(time.time())}_{filename}"
            cloudinary_url_env = os.environ.get('CLOUDINARY_URL')
            if CLOUDINARY_AVAILABLE and cloudinary_url_env:
                try:
                    image_path = upload_to_cloudinary(image_file)
                except Exception:
                    # fallback to local save
                    local_path = os.path.join(UPLOAD_FOLDER, filename)
                    image_file.save(local_path)
                    image_path = os.path.join('uploads', filename)
            else:
                local_path = os.path.join(UPLOAD_FOLDER, filename)
                image_file.save(local_path)
                image_path = os.path.join('uploads', filename)
        conn = get_db_connection()
        conn.execute("INSERT INTO items (name, price, description, contact, image, stars) VALUES (?, ?, ?, ?, ?, ?)", (name, price, desc, contact, image_path, stars))
        conn.commit()
        conn.close()
        flash('Listing added successfully!', 'success')
        return redirect(url_for('items'))
    return render_template('add_item.html', config=app.config)

@app.route('/item/<int:item_id>')
def item(item_id):
    conn = get_db_connection()
    item = conn.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
    conn.close()
    if not item:
        flash('Item not found', 'error')
        return redirect(url_for('items'))
    return render_template('item.html', item=item, config=app.config)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
