from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_from_directory
from firebase_admin import credentials, firestore, initialize_app
from dotenv import load_dotenv
from functools import wraps
import os

# Load environment variables
load_dotenv()

app = Flask(__name__, 
            template_folder='src/templates',  # Set the template folder explicitly
            static_folder='src/static')       # Set the static folder explicitly
app.secret_key = os.urandom(24)  # For session management

# Initialize Firebase with fallback
firebase_available = False
db = None

try:
    if os.getenv('FIREBASE_CREDENTIALS_PATH'):
        cred = credentials.Certificate(os.getenv('FIREBASE_CREDENTIALS_PATH'))
        firebase_app = initialize_app(cred)
        db = firestore.client()
        firebase_available = True
    else:
        print("Firebase credentials not found, running in fallback mode")
except Exception as e:
    print(f"Firebase initialization failed: {e}")
    print("Running in fallback mode with root user only")

# Login decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == "root" and password == "root":
            session["logged_in"] = True
            session["username"] = username
            return redirect(url_for("shop"))
        else:
            return render_template("auth/login.html", error="Invalid username or password")
    
    return render_template("/auth/login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        terms = request.form.get("terms")

        # Basic validation
        if not all([username, email, password, confirm_password, terms]):
            return render_template("auth/signup.html", error="All fields are required")
        
        if password != confirm_password:
            return render_template("auth/signup.html", error="Passwords do not match")

        # TODO: Add Firebase user creation
        # For now, just redirect to login
        return redirect(url_for("login"))
    
    return render_template("/auth/signup.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/shop")
@login_required
def shop():
    products = []
    if firebase_available:
        try:
            products_ref = db.collection('products')
            products = [doc.to_dict() for doc in products_ref.stream()]
        except Exception as e:
            print(f"Error fetching products: {e}")
    return render_template("/shop.html", products=products)

@app.route("/sell")
@login_required
def sell():
    return render_template("sell.html")

@app.route("/api/products", methods=["GET"])
@login_required
def get_products():
    if not firebase_available:
        return jsonify({"status": "error", "message": "Database not available"}), 503
    
    try:
        products_ref = db.collection('products')
        products = [doc.to_dict() for doc in products_ref.stream()]
        return jsonify({"status": "success", "products": products})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/products", methods=["POST"])
@login_required
def add_product():
    if not firebase_available:
        return jsonify({"status": "error", "message": "Database not available"}), 503
    
    try:
        data = request.json
        required_fields = ["name", "description", "price", "condition", "category"]
        
        if not all(field in data for field in required_fields):
            return jsonify({"status": "error", "message": "Missing required fields"}), 400

        doc_ref = db.collection('products').document()
        doc_ref.set({
            "id": doc_ref.id,
            "name": data["name"],
            "description": data["description"],
            "price": float(data["price"]),
            "condition": data["condition"],
            "category": data["category"],
            "images": data.get("images", []),
            "created_at": firestore.SERVER_TIMESTAMP
        })

        return jsonify({"status": "success", "product_id": doc_ref.id})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/products/<product_id>", methods=["GET"])
@login_required
def get_product(product_id):
    if not firebase_available:
        return jsonify({"status": "error", "message": "Database not available"}), 503
    
    try:
        doc_ref = db.collection('products').document(product_id)
        product = doc_ref.get()
        
        if product.exists:
            return jsonify({"status": "success", "product": product.to_dict()})
        return jsonify({"status": "error", "message": "Product not found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/src/images/<path:filename>")
def serve_image(filename):
    return send_from_directory("src/images", filename)

@app.route("/src/static/<path:filename>")
def serve_static(filename):
    return send_from_directory("src/static", filename)

@app.route("/src/videos/<path:filename>")
def serve_video(filename):
    return send_from_directory("src/videos", filename)

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == "__main__":
    app.run(debug=True)
