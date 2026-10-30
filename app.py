
from flask import Flask, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import re

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# Models

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock_quantity = db.Column(db.Integer, nullable=False)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)


# Home API

@app.route('/')
def hello():
    return jsonify({"message": "API is running"})


# Register API

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid input"}), 400

    email = data.get("email", "")
    password = data.get("password", "")

    if not isinstance(email, str) or not isinstance(password, str):
        return jsonify({"error": "Email and password must be strings"}), 400

    email = email.strip()

    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not re.fullmatch(email_pattern, email):
        return jsonify({"error": "Invalid email format"}), 400

    password_pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'

    if not re.fullmatch(password_pattern, password):
        return jsonify({
            "error": "Password must be at least 8 characters and contain uppercase, lowercase, digit and special character"
        }), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "User already exists"}), 409

    new_user = User(
        email=email,
        password=generate_password_hash(password)
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "message": "User registered successfully",
        "user": {
            "id": new_user.id,
            "email": new_user.email
        }
    }), 201


# Login API

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid input"}), 400

    email = data.get("email", "")
    password = data.get("password", "")

    if not isinstance(email, str) or not isinstance(password, str):
        return jsonify({"error": "Email and password must be strings"}), 400

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=email.strip()).first()

    if not user or not check_password_hash(user.password, password):
        return jsonify({"error": "Invalid email or password"}), 401

    return jsonify({
        "message": "Login successful",
        "user": {
            "id": user.id,
            "email": user.email
        }
    }), 200


# Add Product API

@app.route("/product", methods=["POST"])
def add_product():
    data = request.get_json()

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid input"}), 400

    name = data.get("name", "")
    description = data.get("description", "")
    price = data.get("price")
    stock_quantity = data.get("stock_quantity")

    if not all(isinstance(value, str) for value in [name, description]):
        return jsonify({"error": "Name and description must be strings"}), 400

    if not isinstance(price, (int, float)) or isinstance(price, bool):
        return jsonify({"error": "Price must be a number"}), 400

    if not isinstance(stock_quantity, int) or isinstance(stock_quantity, bool):
        return jsonify({"error": "Stock quantity must be an integer"}), 400

    if price < 0 or stock_quantity < 0:
        return jsonify({"error": "Price and stock quantity must be non-negative"}), 400

    new_product = Product(
        name=name,
        description=description,
        price=price,
        stock_quantity=stock_quantity
    )

    db.session.add(new_product)
    db.session.commit()

    return jsonify({
        "message": "Product added successfully",
        "product": {
            "id": new_product.id,
            "name": new_product.name,
            "description": new_product.description,
            "price": new_product.price,
            "stock_quantity": new_product.stock_quantity
        }
    }), 201


# Get Product API

@app.route("/product/<int:product_id>", methods=["GET"])
def get_product(product_id):
    product = Product.query.get(product_id)

    if not product:
        return jsonify({"error": "Product not found"}), 404

    return jsonify({
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "stock_quantity": product.stock_quantity
    }), 200


# Update Product API

@app.route("/product/<int:product_id>", methods=["PATCH"])
def update_product(product_id):
    data = request.get_json()

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid input"}), 400

    stock_quantity = data.get("stock_quantity")

    if not isinstance(stock_quantity, int) or isinstance(stock_quantity, bool):
        return jsonify({"error": "Stock quantity must be an integer"}), 400

    if stock_quantity < 0:
        return jsonify({"error": "Stock quantity must be non-negative"}), 400

    product = Product.query.get(product_id)

    if not product:
        return jsonify({"error": "Product not found"}), 404

    product.stock_quantity = stock_quantity
    db.session.commit()

    return jsonify({
        "message": "Product updated successfully",
        "product": {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "stock_quantity": product.stock_quantity
        }
    }), 200


# Create Order API

@app.route("/order", methods=["POST"])
def create_order():
    order_data = request.get_json()

    if not isinstance(order_data, dict):
        return jsonify({"error": "Invalid input"}), 400

    product_id = order_data.get("product_id")
    quantity = order_data.get("quantity")

    if not isinstance(product_id, int) or isinstance(product_id, bool):
        return jsonify({"error": "Product ID must be an integer"}), 400

    if not isinstance(quantity, int) or isinstance(quantity, bool):
        return jsonify({"error": "Quantity must be an integer"}), 400

    if quantity <= 0:
        return jsonify({"error": "Quantity must be a positive integer"}), 400

    product = Product.query.get(product_id)

    if not product:
        return jsonify({"error": "Product not found"}), 404

    if product.stock_quantity < quantity:
        return jsonify({"error": "Insufficient stock"}), 400

    new_order = Order(
        product_id=product_id,
        quantity=quantity
    )

    db.session.add(new_order)

    product.stock_quantity -= quantity

    db.session.commit()

    return jsonify({
        "message": "Order created successfully",
        "order": {
            "id": new_order.id,
            "product_id": product.id,
            "quantity": quantity,
            "remaining_stock": product.stock_quantity
        }
    }), 201


# Get Order API

@app.route("/order/<int:order_id>", methods=["GET"])
def get_order(order_id):
    order = Order.query.get(order_id)

    if not order:
        return jsonify({"error": "Order not found"}), 404

    return jsonify({
        "id": order.id,
        "product_id": order.product_id,
        "quantity": order.quantity
    }), 200


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(debug=True)
