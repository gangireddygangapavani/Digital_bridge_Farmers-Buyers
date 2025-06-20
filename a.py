import pandas as pd
import random
from faker import Faker

# Initialize Faker for realistic text generation
fake = Faker('en_IN')

# Product categories and attributes
PRODUCTS = [
    "Apples", "Tomatoes", "Wheat", "Rice", "Potatoes", "Onions", "Carrots",
    "Cabbage", "Mangoes", "Bananas", "Oranges", "Spinach", "Cauliflower",
    "Green Peas", "Okra"
]
GRADES = ["A", "B", "C"]
REGIONS = ["Punjab", "Maharashtra", "Uttar Pradesh", "Karnataka", "Gujarat", "Tamil Nadu"]
ORGANIC_STATUS = ["Organic", "Conventional"]
DESCRIPTIVE_TERMS = ["freshly harvested", "premium quality", "locally grown", "hand-picked", "farm-fresh"]

# Generate synthetic product data
def generate_product():
    product_name = random.choice(PRODUCTS)
    grade = random.choice(GRADES)
    region = random.choice(REGIONS)
    organic = random.choice(ORGANIC_STATUS)
    descriptive_term = random.choice(DESCRIPTIVE_TERMS)
    
    # Generate description
    description = f"{organic} {product_name}, Grade {grade}, from {region}, {descriptive_term}"
    if random.random() > 0.6:
        description += f", {fake.sentence(nb_words=4)}"
    
    # Calculate price in INR
    base_prices_inr = {
        "Apples": 150, "Tomatoes": 40, "Wheat": 30, "Rice": 60, "Potatoes": 25,
        "Onions": 30, "Carrots": 50, "Cabbage": 35, "Mangoes": 200,
        "Bananas": 50, "Oranges": 80, "Spinach": 20, "Cauliflower": 40,
        "Green Peas": 60, "Okra": 50
    }
    price = base_prices_inr[product_name]
    if organic == "Organic":
        price *= 1.3
    if grade == "A":
        price += 20
    elif grade == "C":
        price -= 10
    price = round(max(10, price + random.uniform(-15, 15)), 2)
    
    # Additional features
    is_organic = 1 if organic == "Organic" else 0
    grade_score = {"A": 3, "B": 2, "C": 1}[grade]
    
    # Generate farmer username
    farmer_username = f"farmer{fake.user_name()}"
    
    return {
        "farmer_username": farmer_username,
        "product_name": product_name,
        "price": price,
        "description": description,
        "is_organic": is_organic,
        "grade_score": grade_score
    }

# Generate and save synthetic data to CSV
def generate_synthetic_data(num_records=10000):
    data = [generate_product() for _ in range(num_records)]
    df = pd.DataFrame(data)
    df.to_csv('products_data.csv', index=False)
    print(f"Generated {num_records} synthetic product records and saved to products_data.csv.")

if __name__ == "__main__":
    generate_synthetic_data()