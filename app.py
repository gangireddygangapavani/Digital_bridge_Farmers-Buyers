from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

app = Flask(__name__)
app.secret_key = 'your_secret_key'

DATABASE_PATH = 'database/digitalbridge.db'
MODEL_PATH = 'models/price_predictor.pkl'
VECTORIZER_PATH = 'models/tfidf_vectorizer.pkl'

# Ensure the database directory exists
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Function to create tables if they don't exist
def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
       CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('farmer', 'buyer'))
)
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_username TEXT NOT NULL,
            product_name TEXT NOT NULL,
            price REAL NOT NULL CHECK(price > 0),
            description TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

# Call create_tables when the application starts
create_tables()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        
        # Validate role
        if role not in ['farmer', 'buyer']:
            return render_template('register.html', error="Invalid role selected.")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                           (username, password, role))
            conn.commit()
            print(f"Registered user {username} with role: {role} (type: {type(role)})")  # Debugging
        except sqlite3.IntegrityError:
            conn.close()
            return render_template('register.html', error="Username already exists, please choose another one.")
        conn.close()
        
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            # Clear any existing session data to avoid role conflicts
            session.clear()
            session['username'] = user['username']
            session['role'] = user['role']
            print(f"User {username} logged in with role: {user['role']} (type: {type(user['role'])})")  # Debugging
            if user['role'] == 'buyer':
                return redirect(url_for('buyer_dashboard'))
            elif user['role'] == 'farmer':
                return redirect(url_for('farmer_dashboard'))
            else:
                return render_template('login.html', error="Invalid role detected.")
        else:
            return render_template('login.html', error="Invalid credentials, try again.")
    return render_template('login.html')
@app.route('/farmer_dashboard')
def farmer_dashboard():
    if 'username' in session and session['role'] == 'farmer':
        print(f"Accessing farmer dashboard for {session['username']} with role: {session['role']} (type: {type(session['role'])})")  # Debugging
        return render_template('farmer_dashboard.html', username=session['username'])
    print("Unauthorized access to farmer dashboard attempted.")  # Debugging
    return redirect(url_for('login'))

@app.route('/buyer_dashboard')
def buyer_dashboard():
    if 'username' in session and session['role'] == 'buyer':
        print(f"Accessing buyer dashboard for {session['username']} with role: {session['role']} (type: {type(session['role'])})")  # Debugging
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products")
        products = cursor.fetchall()
        conn.close()
        return render_template('buyer_dashboard.html', username=session['username'], products=products)
    print("Unauthorized access to buyer dashboard attempted.")  # Debugging
    return redirect(url_for('login'))

@app.route('/buy_product', methods=['POST'])
def buy_product():
    if 'username' in session and session['role'] == 'buyer':
        try:
            product_name = request.form.get('product_name')

            # Check if product_name exists
            if not product_name:
                return "Error: Invalid product name."

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE product_name = ?", (product_name,))
            product = cursor.fetchone()
            conn.close()

            if product:
                return redirect(url_for('order_success', product_name=product['product_name']))
            else:
                return "Product not found."

        except Exception as e:
            return f"An error occurred: {str(e)}"
    
    return redirect(url_for('buyer_dashboard'))

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if 'username' in session and session['role'] == 'farmer':
        if request.method == 'POST':
            product_name = request.form['product_name']
            price = request.form['price']
            description = request.form['description']

            # Ensure price is a valid float
            try:
                price = float(price)
                if price <= 0:
                    return "Error: Price must be a positive number."
            except ValueError:
                return "Error: Invalid price format."

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO products (farmer_username, product_name, price, description) VALUES (?, ?, ?, ?)", 
                           (session['username'], product_name, price, description))
            conn.commit()
            conn.close()
            return redirect(url_for('farmer_dashboard'))
        return render_template('add_product.html')
    return redirect(url_for('login'))

@app.route('/predict_price', methods=['GET', 'POST'])
def predict_price():
    if 'username' in session and session['role'] == 'farmer':
        predicted_price = None
        if request.method == 'POST':
            product_name = request.form['product_name']
            description = request.form['description']
            
            # Load model and vectorizer
            try:
                model = joblib.load(MODEL_PATH)
                tfidf = joblib.load(VECTORIZER_PATH)
                
                # Prepare input
                text = product_name + ' ' + description
                X_text = tfidf.transform([text]).toarray()
                
                # Add dummy numeric features (since model was trained with them)
                is_organic = 1 if 'organic' in text.lower() else 0
                grade = 2  # Default to Grade B; could parse description for grade
                X_numeric = np.array([[is_organic, grade]])
                X = np.hstack((X_text, X_numeric))
                
                # Predict price (exponentiate since model predicts log-price)
                predicted_price = np.exp(model.predict(X)[0])
            except FileNotFoundError:
                return "Price prediction model not found. Please train the model first."
            
        return render_template('predict_price.html', predicted_price=predicted_price)
    return redirect(url_for('login'))

@app.route('/order_success')
def order_success():
    product_name = request.args.get('product_name', 'Unknown Product')
    return render_template('order_success.html', product_name=product_name)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)