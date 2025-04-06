from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_from_directory
from firebase_admin import credentials, firestore, initialize_app
from dotenv import load_dotenv
from functools import wraps
from google import generativeai as genai
import os

load_dotenv()

# Firebase initialization
firebase_available = False
db = None
FIREBASE_DATABASE_URL = "https://data-retech-80d38-default-rtdb.asia-southeast1.firebasedatabase.app/"

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-key-1234')  # Use environment variable or default key for development

try:
    if os.getenv('FIREBASE_CREDENTIALS_PATH'):
        print("Initializing Firebase...")
        cred = credentials.Certificate(os.getenv('FIREBASE_CREDENTIALS_PATH'))
        firebase_app = initialize_app(cred, {
            'databaseURL': FIREBASE_DATABASE_URL
        })
        db = firestore.client()
        firebase_available = True
        print("Firebase initialized successfully")
    else:
        print("Firebase credentials not found, running in fallback mode")
except Exception as e:
    print(f"Firebase initialization failed: {e}")
    print("Running in fallback mode with root user only")

# Gemini initialization
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    raise ValueError("Gemini API key not found in environment variables")

genai.configure(api_key=api_key)
try:
    model = genai.GenerativeModel('gemini-2.0-flash')
    print("Successfully initialized Gemini model")
except Exception as e:
    print(f"Error initializing Gemini model: {str(e)}")
    raise

SYSTEM_PROMPT = """You are Wolfie
ReTech's dedicated AI assistant and knowledge base expert. 

Your characteristics:
- Name: Wolfie
- Organization: ReTech (Renewable Energy Technology Hub)
- Core Knowledge: 
  * Renewable energy technologies
  * Solar power systems and installations
  * Wind energy solutions
  * Energy storage systems
  * Green technology innovations
  * ReTech's products and services
  * Sustainability practices

- Personality: Professional, enthusiastic about renewable energy, and dedicated to promoting sustainable solutions
- Communication style: Clear, technical when needed, but able to explain complex concepts simply
- Role: To assist users with:
  * Information about ReTech's renewable energy solutions
  * Technical specifications of products
  * Installation and maintenance guidance
  * Sustainability advice
  * Energy efficiency recommendations

Always maintain a professional tone while sharing your extensive knowledge about renewable energy and ReTech's offerings."""

app.template_folder='src/templates'
app.static_folder='src/static'

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

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # Root user bypass for testing
        if email == "root@netlify.com" and password == "admin":
            session['logged_in'] = True
            session['email'] = email
            session['username'] = 'Admin'
            return redirect(request.args.get('next') or url_for('shop'))

        if firebase_available and db:
            try:
                users_ref = db.collection('users')
                user_query = users_ref.where('email', '==', email.lower()).where('password', '==', password).limit(1).get()
                
                user_exists = False
                for user in user_query:
                    user_exists = True
                    user_data = user.to_dict()
                    session['logged_in'] = True
                    session['email'] = email
                    session['username'] = user_data.get('username', 'User')
                    return redirect(request.args.get('next') or url_for('shop'))
                
                if not user_exists:
                    return render_template("auth/login.html", error="Invalid email or password")
                    
            except Exception as e:
                print(f"Firebase error: {str(e)}")
                return render_template("auth/login.html", error="Error during login. Please try again.")
        else:
            return render_template("auth/login.html", error="Login system is currently unavailable")

    return render_template("auth/login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    print(f"Method: {request.method}")  # Debug log
    print(f"Request headers: {dict(request.headers)}")  # Debug headers
    print(f"Request form data: {request.form}")  # Debug form data
    if request.method == "POST":
        try:
            # Get form data
            form_data = request.form.to_dict()
            print(f"Form data received: {form_data}")  # Debug log
            
            username = request.form.get("username")
            email = request.form.get("email")
            password = request.form.get("password")
            confirm_password = request.form.get("confirm_password")
            terms = request.form.get("terms")

            print(f"Signup attempt - Email: {email}, Username: {username}")
            print(f"Firebase status - Available: {firebase_available}, DB: {db is not None}")

            # Validate all fields are present
            if not all([username, email, password, confirm_password]):
                print("Missing required fields")
                return render_template("auth/signup.html", error="All fields are required")
            
            # Validate terms acceptance
            if not terms:
                print("Terms not accepted")
                return render_template("auth/signup.html", error="Please accept the terms and conditions")

            # Validate password match
            if password != confirm_password:
                print("Password mismatch")
                return render_template("auth/signup.html", error="Passwords do not match")

            # Validate email format
            if '@' not in email or '.' not in email:
                print("Invalid email format")
                return render_template("auth/signup.html", error="Please enter a valid email address")

            if firebase_available and db:
                try:
                    print("Checking for existing user in Firebase...")  # Debug log
                    # Check for existing user
                    users_ref = db.collection('users')
                    existing_user = users_ref.where('email', '==', email.lower()).get()
                    
                    if len(list(existing_user)) > 0:
                        print(f"User already exists: {email}")
                        return render_template("auth/signup.html", error="Email already registered")
                    
                    print("Creating new user document...")  # Debug log
                    # Create user document
                    user_data = {
                        'username': username,
                        'email': email.lower(),  # Store email in lowercase
                        'password': password,  # In production, this should be hashed
                        'created_at': firestore.SERVER_TIMESTAMP,
                        'role': 'user',
                        'active': True
                    }
                    
                    # Add to Firestore
                    users_ref.add(user_data)
                    print(f"User created successfully with email: {email}")
                    
                    return redirect(url_for('login'))
                    
                except Exception as e:
                    print(f"Firebase error: {str(e)}")
                    print(f"Firebase error type: {type(e)}")
                    import traceback
                    print(f"Traceback: {traceback.format_exc()}")
                    return render_template("auth/signup.html", error="Error creating account. Please try again.")
            else:
                print("Firebase unavailable")
                return render_template("auth/signup.html", error="Registration system is currently unavailable")
                
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return render_template("auth/signup.html", error="An unexpected error occurred")

    return render_template("auth/signup.html")

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

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/chat', methods=['POST'])
def chat():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    message = data.get("message")
    username = session.get("username", "Guest")  # Get username from session

    if not message:
        return jsonify({"error": "No message provided"}), 400

    try:
        # Create a personalized system prompt
        personalized_prompt = f"{SYSTEM_PROMPT}\nYou are talking to {username}. Always address them by their name."
        
        # Generate response using the personalized prompt
        response = model.generate_content(
            [
                {"role": "user", "parts": [{"text": personalized_prompt}]},
                {"role": "model", "parts": [{"text": "I understand. I'll address the user by their name and help them with their questions."}]},
                {"role": "user", "parts": [{"text": message}]}
            ]
        )
        
        # Extract the response text
        response_text = response.text
        
        # Add a personal touch if it's not already there
        if username != "Guest" and username not in response_text:
            response_text = f"Hi {username}! {response_text}"

        return jsonify({"response": response_text})

    except Exception as e:
        print(f"Error in chat: {str(e)}")
        return jsonify({"error": "Failed to generate response"}), 500


if __name__ == "__main__":
    app.run(debug=True)
