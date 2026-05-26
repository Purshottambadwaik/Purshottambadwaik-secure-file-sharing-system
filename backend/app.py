from fileinput import filename
import os

from flask import Flask, render_template
from config.db_config import db
from models.user_model import User
from models.file_model import File
from flask import Flask, render_template, request, redirect, session, send_from_directory , flash
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Max upload size = 10 MB
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

# Absolute database path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
ALLOWED_EXTENSIONS = {
    'pdf',
    'png',
    'jpg',
    'jpeg',
    'txt' ,
    'doc',
    'xlsx'
}

# Check allowed file extensions
def allowed_file(filename):

    return (
        '.' in filename
        and
        filename.rsplit('.', 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )
    
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')

db_path = os.path.join(BASE_DIR, 'database', 'database.db')

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Database
db.init_app(app)

# Home Page
@app.route('/')
def home():
    return render_template("index.html")

# Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        # Find user by email
        user = User.query.filter_by(email=email).first()

        # Check password
        if user and check_password_hash(user.password, password):

            session['user_id'] = user.id
            session['username'] = user.username
            
            return redirect('/dashboard')

        else:
            return "Invalid Email or Password"

    return render_template("login.html")

#Dashboard Page
@app.route('/dashboard')
def dashboard():

    # Check if user logged in
    if 'user_id' in session:

        username = session['username']

       
        # Get current user's files from database
    files = File.query.filter_by(
        user_id=session['user_id']
    ).all()


    return render_template(
            'dashboard.html',
            username=username,
            files=files
        )

    return redirect('/login')

# Logout Route
@app.route('/logout')
def logout():

    # Clear Session
    session.clear()

    return redirect('/login')

# File size error handler
@app.errorhandler(413)
def too_large(e):

    flash("File is too large (Max 10 MB)")
    return redirect('/dashboard')

# Upload Route
@app.route('/upload', methods=['POST'])
def upload_file():

    # Check login
    if 'user_id' not in session:
        return redirect('/login')

    # Get uploaded file
    file = request.files['file']
    
        # Secure filename
    filename = secure_filename(file.filename)
    print(filename)
    # Check if file selected
    if filename == '':
            flash("No file selected")
            return redirect('/dashboard')

    # Validate file type
    if not allowed_file(filename):
        flash("File type not allowed")
        return redirect('/dashboard')
    
    # Create user-specific folder
    user_folder = os.path.join(
        UPLOAD_FOLDER,
        f"user_{session['user_id']}"
    )

    # Create folder if not exists
    os.makedirs(user_folder, exist_ok=True)

    # Save file inside user folder
    file.save(
        os.path.join(user_folder, filename)
    )
    
    # Save file metadata to database
    new_file = File(
        filename=filename,
        user_id=session['user_id']
    )

    db.session.add(new_file)
    db.session.commit()

    flash("File uploaded successfully")
   
    return redirect('/dashboard')

# Download Route
@app.route('/download/<filename>')
def download_file(filename):

    # Check login
    if 'user_id' not in session:
        return redirect('/login')

    # Current user's folder
    user_folder = os.path.join(
        UPLOAD_FOLDER,
        f"user_{session['user_id']}"
    )

    return send_from_directory(
        user_folder,
        filename,
        as_attachment=True
    )

# Delete Route
@app.route('/delete/<filename>')
def delete_file(filename):

    # Check login
    if 'user_id' not in session:
        return redirect('/login')

 # Current user's folder
    user_folder = os.path.join(
        UPLOAD_FOLDER,
        f"user_{session['user_id']}"
    )


    # Full file path
    file_path = os.path.join(user_folder, filename)

        # Delete file if exists
    if os.path.exists(file_path):

        # Delete physical file
        os.remove(file_path)

    # Delete metadata from database
    file_record = File.query.filter_by(
        filename=filename,
        user_id=session['user_id']
    ).first()

    if file_record:

        db.session.delete(file_record)
        db.session.commit()



    flash("File deleted successfully")
    return redirect('/dashboard')

# Register Page
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        # Create User Object
        new_user = User(
            username=username,
            email=email,
            password=hashed_password
        )
         

        # Save to Database
        db.session.add(new_user)
        db.session.commit()

        return "User Registered Successfully"

    return render_template("register.html")

with app.app_context():
    db.create_all()
    
if __name__ == '__main__':
    app.run(debug=True)