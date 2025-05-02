from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, abort
from pymongo import MongoClient
from bson.objectid import ObjectId
from functools import wraps
from fpdf import FPDF  # type: ignore
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

client = MongoClient('mongodb://localhost:27017/')
db = client['inventory_db']
products_collection = db['products']
transactions_collection = db['transactions']
orders_collection = db['orders']
admins_collection = db['admins']
clients_collection = db['clients']

# Ensure the admin account exists
if not admins_collection.find_one({"username": "admin"}):
    admins_collection.insert_one({
        "username": "admin",
        "password": "admin123"
    })

# Admin required decorator
def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('You need to log in as an admin first!', 'error')
            return redirect(url_for('login', next=request.url))
        return func(*args, **kwargs)
    return wrapper

# Add Client Management Routes
@app.route('/add_client', methods=['GET', 'POST'])
@admin_required
def add_client():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address')

        if not all([name, email, phone, address]):
            flash('All fields are required!', 'error')
            return redirect(url_for('add_client'))

        client = {
            "name": name,
            "email": email,
            "phone": phone,
            "address": address
        }
        clients_collection.insert_one(client)
        flash('Client added successfully!', 'success')
        return redirect(url_for('view_clients'))

    return render_template('add_client.html')

@app.route('/view_clients')
@admin_required
def view_clients():
    clients = list(clients_collection.find())
    return render_template('view_clients.html', clients=clients)

@app.route('/edit_client/<client_id>', methods=['GET', 'POST'])
@admin_required
def edit_client(client_id):
    try:
        client_id_obj = ObjectId(client_id)
        client = clients_collection.find_one({"_id": client_id_obj})
    except Exception as e:
        flash('Invalid client ID!', 'error')
        return redirect(url_for('view_clients'))

    if not client:
        flash('Client not found!', 'error')
        return redirect(url_for('view_clients'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address')

        if not all([name, email, phone, address]):
            flash('All fields are required!', 'error')
            return redirect(url_for('edit_client', client_id=client_id))

        clients_collection.update_one(
            {"_id": client_id_obj},
            {"$set": {
                "name": name,
                "email": email,
                "phone": phone,
                "address": address
            }}
        )
        flash('Client updated successfully!', 'success')
        return redirect(url_for('view_clients'))

    return render_template('edit_client.html', client=client)

@app.route('/delete_client/<client_id>')
@admin_required
def delete_client(client_id):
    try:
        client_id_obj = ObjectId(client_id)
        client = clients_collection.find_one({"_id": client_id_obj})
    except Exception as e:
        flash('Invalid client ID!', 'error')
        return redirect(url_for('view_clients'))

    if not client:
        flash('Client not found!', 'error')
        return redirect(url_for('view_clients'))

    clients_collection.delete_one({"_id": client_id_obj})
    flash('Client deleted successfully!', 'success')
    return redirect(url_for('view_clients'))

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        admin = admins_collection.find_one({"username": username, "password": password})
        if admin:
            session['admin_logged_in'] = True
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password!', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/add_order', methods=['GET', 'POST'])
@admin_required
def add_order():
    if request.method == 'POST':
        supplier_name = request.form.get('supplier_name')
        product_id = request.form.get('product_id')
        quantity = request.form.get('quantity')
        order_date = request.form.get('order_date')
        status = request.form.get('status', 'Pending')

        # Validate required fields
        if not all([supplier_name, product_id, quantity, order_date]):
            flash('All fields are required!', 'error')
            return redirect(url_for('add_order'))

        try:
            # Convert quantity to integer and order_date to datetime
            quantity = int(quantity)
            order_date = datetime.strptime(order_date, "%Y-%m-%d")
        except ValueError:
            flash('Invalid quantity or date format!', 'error')
            return redirect(url_for('add_order'))

        # Validate status
        if status not in ["Pending", "Delivered"]:
            flash('Invalid status!', 'error')
            return redirect(url_for('add_order'))

        # Ensure product_id is a valid ObjectId
        try:
            product_id_obj = ObjectId(product_id)
        except Exception as e:
            flash('Invalid product ID!', 'error')
            return redirect(url_for('add_order'))

        # Check if the product exists
        product = products_collection.find_one({"_id": product_id_obj})
        if not product:
            flash('Product not found!', 'error')
            return redirect(url_for('add_order'))

        # Create the order document
        order = {
            "supplier_name": supplier_name,
            "product_id": product_id_obj,
            "quantity": quantity,
            "order_date": order_date,
            "status": status
        }

        # Insert the order into the orders collection
        orders_collection.insert_one(order)

        # Update the product quantity ONLY if the status is "Delivered"
        if status == "Delivered":
            new_quantity = product['quantity'] + quantity
            products_collection.update_one(
                {"_id": product_id_obj},
                {"$set": {"quantity": new_quantity}}
            )
            flash('Order added successfully and product quantity updated!', 'success')
        else:
            flash('Order added successfully with status Pending. Product quantity remains unchanged.', 'success')

        return redirect(url_for('view_orders'))

    # Fetch all products for the dropdown
    products = list(products_collection.find())
    return render_template('add_order.html', products=products)


@app.route('/view_orders')
@admin_required
def view_orders():
    try:
        # Fetch all orders from the orders collection
        orders = list(orders_collection.find())
        return render_template('view_orders.html', orders=orders)
    except Exception as e:
        print(f"Error fetching orders: {e}")
        flash('An error occurred while fetching orders.', 'error')
        return redirect(url_for('index'))
    
@app.route('/edit_order/<order_id>', methods=['GET', 'POST'])
@admin_required
def edit_order(order_id):
    try:
        order_id_obj = ObjectId(order_id)
        order = orders_collection.find_one({"_id": order_id_obj})
    except Exception as e:
        flash('Invalid order ID!', 'error')
        return redirect(url_for('view_orders'))

    if not order:
        flash('Order not found!', 'error')
        return redirect(url_for('view_orders'))

    # Fetch all products for the dropdown
    products = list(products_collection.find())

    if request.method == 'POST':
        supplier_name = request.form.get('supplier_name')
        product_id = request.form.get('product_id')
        quantity = request.form.get('quantity')
        order_date = request.form.get('order_date')
        status = request.form.get('status')

        if not all([supplier_name, product_id, quantity, order_date, status]):
            flash('All fields are required!', 'error')
            return redirect(url_for('edit_order', order_id=order_id))

        try:
            quantity = int(quantity)
            order_date = datetime.strptime(order_date, "%Y-%m-%d")
        except ValueError:
            flash('Invalid quantity or date format!', 'error')
            return redirect(url_for('edit_order', order_id=order_id))

        if status not in ["Pending", "Delivered"]:
            flash('Invalid status!', 'error')
            return redirect(url_for('edit_order', order_id=order_id))

        # Ensure product_id is a valid ObjectId
        try:
            product_id_obj = ObjectId(product_id)
        except Exception as e:
            flash('Invalid product ID!', 'error')
            return redirect(url_for('edit_order', order_id=order_id))

        product = products_collection.find_one({"_id": product_id_obj})
        if not product:
            flash('Product not found!', 'error')
            return redirect(url_for('edit_order', order_id=order_id))

        # Check if the status is changing from Pending to Delivered
        if order['status'] == "Pending" and status == "Delivered":
            # Update the product quantity
            new_quantity = product['quantity'] + quantity
            products_collection.update_one(
                {"_id": product_id_obj},
                {"$set": {"quantity": new_quantity}}
            )
            flash('Order status updated to Delivered and product quantity increased!', 'success')
        elif order['status'] == "Delivered" and status == "Pending":
            # Revert the product quantity (subtract the ordered quantity)
            new_quantity = product['quantity'] - quantity
            products_collection.update_one(
                {"_id": product_id_obj},
                {"$set": {"quantity": new_quantity}}
            )
            flash('Order status updated to Pending and product quantity reverted!', 'success')
        else:
            flash('Order updated successfully!', 'success')

        # Update the order document
        orders_collection.update_one(
            {"_id": order_id_obj},
            {"$set": {
                "supplier_name": supplier_name,
                "product_id": product_id_obj,
                "quantity": quantity,
                "order_date": order_date,
                "status": status
            }}
        )
        return redirect(url_for('view_orders'))

    return render_template('edit_order.html', order=order, products=products)

@app.route('/delete_order/<order_id>')
@admin_required
def delete_order(order_id):
    try:
        order_id_obj = ObjectId(order_id)
        orders_collection.delete_one({"_id": order_id_obj})
        flash('Order deleted successfully!', 'success')
    except Exception as e:
        print(f"Error deleting order: {e}")
        flash('An error occurred while deleting the order.', 'error')
    return redirect(url_for('view_orders'))

@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('landing'))

@app.route('/add_product', methods=['GET', 'POST'])
@admin_required
def add_product():
    if request.method == 'POST':
        name = request.form.get('name')
        quantity = request.form.get('quantity')
        price = request.form.get('price')
        category = request.form.get('category')

        if not all([name, quantity, price, category]):
            flash('All fields are required!', 'error')
            return redirect(url_for('add_product'))

        try:
            quantity = int(quantity)
            price = float(price)
        except ValueError:
            flash('Invalid quantity or price!', 'error')
            return redirect(url_for('add_product'))

        product = {
            "name": name,
            "quantity": quantity,
            "price": price,
            "category": category
        }
        products_collection.insert_one(product)
        flash('Product added successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('add_product.html')

@app.route('/view_products')
@admin_required
def view_products():
    products = list(products_collection.find())
    return render_template('view_products.html', products=products)

@app.route('/view_product/<product_id>')
@admin_required
def view_product(product_id):
    try:
        product = products_collection.find_one({"_id": ObjectId(product_id)})
        if product:
            return render_template('view_product.html', product=product)
        else:
            flash('Product not found!', 'error')
            return redirect(url_for('view_products'))
    except Exception as e:
        flash('An error occurred while fetching the product.', 'error')
        return redirect(url_for('view_products'))

@app.route('/edit_product/<product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    try:
        product_id_obj = ObjectId(product_id)
        product = products_collection.find_one({"_id": product_id_obj})
    except Exception as e:
        flash('Invalid product ID!', 'error')
        return redirect(url_for('view_products'))

    if not product:
        flash('Product not found!', 'error')
        return redirect(url_for('view_products'))

    if request.method == 'POST':
        name = request.form.get('name')
        quantity = request.form.get('quantity')
        price = request.form.get('price')
        category = request.form.get('category')

        products_collection.update_one(
            {"_id": product_id_obj},
            {"$set": {
                "name": name,
                "quantity": int(quantity),
                "price": float(price),
                "category": category
            }}
        )
        flash('Product updated successfully!', 'success')
        return redirect(url_for('view_products'))

    return render_template('edit_product.html', product=product)

@app.route('/delete_product/<product_id>')
@admin_required
def delete_product(product_id):
    try:
        product_id_obj = ObjectId(product_id)
        product = products_collection.find_one({"_id": product_id_obj})
    except Exception as e:
        flash('Invalid product ID!', 'error')
        return redirect(url_for('view_products'))

    if not product:
        flash('Product not found!', 'error')
        return redirect(url_for('view_products'))

    products_collection.delete_one({"_id": product_id_obj})
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('view_products'))

@app.route('/transactions')
@admin_required
def transactions():
    try:
        transactions = list(transactions_collection.find())
        return render_template('transactions.html', transactions=transactions)
    except Exception as e:
        print(f"Error fetching transactions: {e}")
        flash('An error occurred while fetching transactions.', 'error')
        return redirect(url_for('index'))

@app.route('/add_sample_transaction')
@admin_required
def add_sample_transaction():
    try:
        sample_transaction = {
            "product_id": ObjectId(),
            "transaction_type": "sale",
            "quantity": 10,
            "price": 100.0,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        transactions_collection.insert_one(sample_transaction)
        flash('Sample transaction added successfully!', 'success')
        return redirect(url_for('transactions'))
    except Exception as e:
        flash('An error occurred while adding a sample transaction.', 'error')
        return redirect(url_for('index'))

@app.route('/product_report')
@admin_required
def product_report():
    pdf_output = "product_report.pdf"
    try:
        products = list(products_collection.find())
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Product Report", ln=True, align='C')
        pdf.cell(40, 10, txt="Name", border=1)
        pdf.cell(40, 10, txt="Quantity", border=1)
        pdf.cell(40, 10, txt="Price", border=1)
        pdf.cell(40, 10, txt="Category", border=1)
        pdf.ln()

        for product in products:
            pdf.cell(40, 10, txt=product['name'], border=1)
            pdf.cell(40, 10, txt=str(product['quantity']), border=1)
            pdf.cell(40, 10, txt=str(product['price']), border=1)
            pdf.cell(40, 10, txt=product['category'], border=1)
            pdf.ln()

        pdf.output(pdf_output)
        if not os.path.exists(pdf_output):
            flash('Failed to generate the product report.', 'error')
            return redirect(url_for('index'))

        response = send_file(pdf_output, as_attachment=True)
        flash('Product report generated successfully! Check your downloads.', 'success')
        return response
    except Exception as e:
        flash('An error occurred while generating the product report.', 'error')
        return redirect(url_for('index'))
    finally:
        if os.path.exists(pdf_output):
            try:
                os.remove(pdf_output)
            except Exception as e:
                print(f"Error deleting temporary file: {e}")

@app.route('/index')
@admin_required
def index():
    return render_template('index.html')

@app.route('/search_product', methods=['GET', 'POST'])
@admin_required
def search_product():
    search_query = None
    search_results = []
    if request.method == 'POST':
        search_query = request.form.get('search_query')
        if search_query:
            search_results = list(products_collection.find({"name": {"$regex": search_query, "$options": "i"}}))
    return render_template('search_product.html', search_query=search_query, search_results=search_results)

if __name__ == '__main__':
    app.run(debug=True, port=5002)