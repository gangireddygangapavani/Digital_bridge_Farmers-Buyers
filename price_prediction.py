import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import joblib
import os

# Load product data from CSV
def load_product_data():
    try:
        df = pd.read_csv('products_data.csv')
        return df
    except FileNotFoundError:
        print("products_data.csv not found. Please run generate_synthetic_data.py first.")
        return None

# Preprocess data and train models
def train_price_prediction_model():
    # Load data
    df = load_product_data()
    
    if df is None or df.empty:
        print("No data available. Exiting.")
        return
    
    # Combine product_name and description for text features
    df['text'] = df['product_name'] + ' ' + df['description']
    
    # Feature extraction using TF-IDF
    tfidf = TfidfVectorizer(max_features=500, stop_words='english')
    X_text = tfidf.fit_transform(df['text']).toarray()
    
    # Additional features
    X_numeric = df[['is_organic', 'grade_score']].values
    X = np.hstack((X_text, X_numeric))
    
    # Target variable (log-transform to reduce variance)
    y = np.log(df['price'].values)  # Log-transform prices
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train Random Forest with tuned hyperparameters
    rf_model = RandomForestRegressor(n_estimators=300, max_depth=30, min_samples_split=5, random_state=42)
    rf_model.fit(X_train, y_train)
    rf_pred = np.exp(rf_model.predict(X_test))  # Exponentiate to get INR
    rf_mse = mean_squared_error(np.exp(y_test), rf_pred)  # MSE in INR
    
    # Train Linear Regression
    lr_model = LinearRegression()
    lr_model.fit(X_train, y_train)
    lr_pred = np.exp(lr_model.predict(X_test))
    lr_mse = mean_squared_error(np.exp(y_test), lr_pred)
    
    # Select best model
    print(f"Random Forest MSE: {rf_mse:.2f}")
    print(f"Linear Regression MSE: {lr_mse:.2f}")
    best_model = rf_model if rf_mse < lr_mse else lr_model
    model_name = "Random Forest" if rf_mse < lr_mse else "Linear Regression"
    print(f"Selected {model_name} as the best model.")
    
    # Save model and vectorizer
    os.makedirs('models', exist_ok=True)
    joblib.dump(best_model, 'models/price_predictor.pkl')
    joblib.dump(tfidf, 'models/tfidf_vectorizer.pkl')
    print("Model and vectorizer saved successfully.")

if __name__ == "__main__":
    train_price_prediction_model()