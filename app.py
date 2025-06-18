import json
import secrets
import requests
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import urlencode
from jinja2 import DictLoader
import click

# Create a custom template loader
from jinja2 import DictLoader

# Initialize Flask app
app = Flask(__name__)

# Hardcoded Configuration
app.config['SECRET_KEY'] = 'xK9mN3pQ7rT5wY2zB4dF6hJ8kL1nP3sV5xC7bN9mQ2wE4rT6'
# Use SQLite database - automatically creates file if it doesn't exist
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///valorant_marketplace.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Hardcoded Secrets
SQUARE_APP_ID = 'sq0idp-3lHcPZwip9351EAnAer92A'
SQUARE_APP_SECRET = 'sq0csp-nrd_xRzRYwheZKcKWfnJWbP8Dbsr85SUWcQra6d0utM'
SQUARE_PRODUCTION_ACCESS_TOKEN = 'EAAAl4vy95lvz5ACW3P_SUr-FSeHSGDuEniKxlytApO5jhN-0fcW1LRxcDgxfn7F'
SQUARE_ENVIRONMENT = 'production'
SQUARE_LOCATION_ID = 'LMNMA0HYA66VX'

DISCORD_CLIENT_ID = '1384772758046507099'
DISCORD_CLIENT_SECRET = 'T5-jdB_fYB24v8tL7PNgQZ704EKeWeeN'
APP_BASE_URL = 'https://accountsellers.onrender.com'

# Initialize database
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.BigInteger, primary_key=True)  # Discord ID
    username = db.Column(db.String(80), nullable=False)
    discriminator = db.Column(db.String(10), nullable=False)
    square_merchant_id = db.Column(db.String(100), unique=True, nullable=True)
    square_access_token = db.Column(db.String(255), unique=True, nullable=True)
    listings = db.relationship('Listing', backref='seller', lazy=True)

class Listing(db.Model):
    __tablename__ = 'listings'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(120), nullable=False)
    rank = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)
    seller_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# HTML Templates
BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Valorant Accounts Marketplace{% endblock %}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background-color: #0f1722;
            color: #e2e8f0;
            line-height: 1.6;
            min-height: 100vh;
        }
        
        .navbar {
            background-color: #1d2839;
            padding: 1rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
            position: sticky;
            top: 0;
            z-index: 1000;
        }
        
        .nav-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .nav-brand {
            font-size: 1.5rem;
            font-weight: bold;
            color: #ff4655;
            text-decoration: none;
        }
        
        .nav-links {
            display: flex;
            gap: 2rem;
            align-items: center;
        }
        
        .nav-link {
            color: #e2e8f0;
            text-decoration: none;
            transition: color 0.3s;
        }
        
        .nav-link:hover {
            color: #ff4655;
        }
        
        .btn {
            display: inline-block;
            padding: 0.5rem 1.5rem;
            background-color: #ff4655;
            color: white;
            text-decoration: none;
            border-radius: 0.25rem;
            transition: all 0.3s;
            border: none;
            cursor: pointer;
            font-size: 1rem;
        }
        
        .btn:hover {
            background-color: #e63946;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(255, 70, 85, 0.4);
        }
        
        .btn-secondary {
            background-color: #374151;
        }
        
        .btn-secondary:hover {
            background-color: #4b5563;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 2rem;
            margin-top: 2rem;
        }
        
        .card {
            background-color: #1d2839;
            border-radius: 0.5rem;
            padding: 1.5rem;
            transition: transform 0.3s, box-shadow 0.3s;
            border: 1px solid rgba(255, 70, 85, 0.2);
        }
        
        .card:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 24px rgba(255, 70, 85, 0.2);
        }
        
        .card h3 {
            color: #ff4655;
            margin-bottom: 0.5rem;
        }
        
        .card p {
            color: #9ca3af;
            margin-bottom: 0.5rem;
        }
        
        .price {
            font-size: 1.5rem;
            font-weight: bold;
            color: #10b981;
            margin: 1rem 0;
        }
        
        .form-group {
            margin-bottom: 1.5rem;
        }
        
        .form-label {
            display: block;
            margin-bottom: 0.5rem;
            color: #e2e8f0;
            font-weight: 500;
        }
        
        .form-control {
            width: 100%;
            padding: 0.75rem;
            background-color: #374151;
            border: 1px solid #4b5563;
            border-radius: 0.25rem;
            color: #e2e8f0;
            font-size: 1rem;
            transition: border-color 0.3s;
        }
        
        .form-control:focus {
            outline: none;
            border-color: #ff4655;
        }
        
        .alert {
            padding: 1rem;
            border-radius: 0.25rem;
            margin-bottom: 1rem;
        }
        
        .alert-success {
            background-color: rgba(16, 185, 129, 0.2);
            border: 1px solid #10b981;
            color: #10b981;
        }
        
        .alert-error {
            background-color: rgba(239, 68, 68, 0.2);
            border: 1px solid #ef4444;
            color: #ef4444;
        }
        
        .listing-detail {
            background-color: #1d2839;
            border-radius: 0.5rem;
            padding: 2rem;
            margin-top: 2rem;
        }
        
        .listing-header {
            border-bottom: 1px solid #374151;
            padding-bottom: 1rem;
            margin-bottom: 2rem;
        }
        
        .listing-header h1 {
            color: #ff4655;
            margin-bottom: 0.5rem;
        }
        
        .listing-info {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
            margin-bottom: 2rem;
        }
        
        .payment-section {
            background-color: #374151;
            padding: 2rem;
            border-radius: 0.5rem;
            margin-top: 2rem;
        }
        
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .hero {
            text-align: center;
            padding: 4rem 0 2rem;
        }
        
        .hero h1 {
            font-size: 3rem;
            margin-bottom: 1rem;
            background: linear-gradient(45deg, #ff4655, #e63946);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .hero p {
            font-size: 1.25rem;
            color: #9ca3af;
        }
    </style>
    {% block extra_head %}{% endblock %}
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <a href="{{ url_for('index') }}" class="nav-brand">Valorant Marketplace</a>
            <div class="nav-links">
                {% if session.get('user_id') %}
                    <a href="{{ url_for('sell') }}" class="nav-link">Sell Account</a>
                    <span class="nav-link">{{ session.get('username') }}</span>
                    <a href="{{ url_for('logout') }}" class="btn btn-secondary">Logout</a>
                {% else %}
                    <a href="{{ url_for('login') }}" class="btn">Login with Discord</a>
                {% endif %}
            </div>
        </div>
    </nav>
    
    <div class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        {% block content %}{% endblock %}
    </div>
</body>
</html>
"""

HOME_TEMPLATE = """
{% extends "base.html" %}
{% block content %}
<div class="hero">
    <h1>Valorant Accounts Marketplace</h1>
    <p>Buy and sell premium Valorant accounts securely</p>
</div>

<div class="grid">
    {% for listing in listings %}
    <div class="card">
        <h3>{{ listing.title }}</h3>
        <p><strong>Rank:</strong> {{ listing.rank }}</p>
        <p><strong>Seller:</strong> {{ listing.seller.username }}</p>
        <div class="price">${{ "%.2f"|format(listing.price) }}</div>
        <a href="{{ url_for('listing_detail', listing_id=listing.id) }}" class="btn">View Details</a>
    </div>
    {% endfor %}
</div>

{% if not listings %}
<div style="text-align: center; margin-top: 4rem;">
    <p style="color: #9ca3af; font-size: 1.125rem;">No listings available yet.</p>
    {% if session.get('user_id') %}
        <a href="{{ url_for('sell') }}" class="btn" style="margin-top: 1rem;">Create First Listing</a>
    {% endif %}
</div>
{% endif %}
{% endblock %}
"""

SELL_TEMPLATE = """
{% extends "base.html" %}
{% block content %}
<h1 style="color: #ff4655; margin-bottom: 2rem;">Create New Listing</h1>

<form method="POST" style="max-width: 600px;">
    <div class="form-group">
        <label class="form-label">Title</label>
        <input type="text" name="title" class="form-control" required placeholder="e.g., Radiant Account with All Agents">
    </div>
    
    <div class="form-group">
        <label class="form-label">Rank</label>
        <select name="rank" class="form-control" required>
            <option value="">Select Rank</option>
            <option value="Iron">Iron</option>
            <option value="Bronze">Bronze</option>
            <option value="Silver">Silver</option>
            <option value="Gold">Gold</option>
            <option value="Platinum">Platinum</option>
            <option value="Diamond">Diamond</option>
            <option value="Ascendant">Ascendant</option>
            <option value="Immortal">Immortal</option>
            <option value="Radiant">Radiant</option>
        </select>
    </div>
    
    <div class="form-group">
        <label class="form-label">Price (USD)</label>
        <input type="number" name="price" class="form-control" required min="0.01" step="0.01" placeholder="99.99">
    </div>
    
    <div class="form-group">
        <label class="form-label">Description</label>
        <textarea name="description" class="form-control" rows="6" placeholder="Describe the account details, skins, agents unlocked, etc."></textarea>
    </div>
    
    <button type="submit" class="btn">Create Listing</button>
</form>
{% endblock %}
"""

LISTING_DETAIL_TEMPLATE = """
{% extends "base.html" %}
{% block extra_head %}
{% if can_purchase %}
<script type="text/javascript" src="https://web.squarecdn.com/v1/square.js"></script>
{% endif %}
{% endblock %}

{% block content %}
<div class="listing-detail">
    <div class="listing-header">
        <h1>{{ listing.title }}</h1>
        <p style="color: #9ca3af;">Listed by {{ listing.seller.username }} on {{ listing.created_at.strftime('%B %d, %Y') }}</p>
    </div>
    
    <div class="listing-info">
        <div>
            <h3 style="color: #ff4655; margin-bottom: 1rem;">Account Details</h3>
            <p><strong>Rank:</strong> {{ listing.rank }}</p>
            <p><strong>Price:</strong> <span class="price">${{ "%.2f"|format(listing.price) }}</span></p>
        </div>
        <div>
            <h3 style="color: #ff4655; margin-bottom: 1rem;">Description</h3>
            <p style="white-space: pre-wrap;">{{ listing.description or 'No description provided.' }}</p>
        </div>
    </div>
    
    {% if can_purchase %}
    <div class="payment-section">
        <h3 style="color: #ff4655; margin-bottom: 1rem;">Purchase This Account</h3>
        <p style="margin-bottom: 1rem;">Complete your purchase securely with Square</p>
        <div id="payment-form">
            <div id="card-container"></div>
            <button id="card-button" type="button" class="btn" style="margin-top: 1rem;">
                Pay ${{ "%.2f"|format(listing.price) }}
            </button>
            <div id="payment-status-container" style="margin-top: 1rem;"></div>
        </div>
    </div>
    
    <script>
        const appId = '{{ square_app_id }}';
        const locationId = '{{ square_location_id }}';
        
        async function initializeCard(payments) {
            const card = await payments.card();
            await card.attach('#card-container');
            return card;
        }
        
        async function createPayment(token) {
            const body = JSON.stringify({
                sourceId: token,
                listingId: {{ listing.id }}
            });
            
            const paymentResponse = await fetch('{{ url_for("create_square_payment") }}', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body,
            });
            
            if (paymentResponse.ok) {
                return paymentResponse.json();
            }
            
            const errorBody = await paymentResponse.text();
            throw new Error(errorBody);
        }
        
        async function handlePaymentMethodSubmission(event, paymentMethod) {
            event.preventDefault();
            
            const cardButton = document.getElementById('card-button');
            const statusContainer = document.getElementById('payment-status-container');
            
            try {
                cardButton.disabled = true;
                cardButton.innerHTML = '<span class="loading"></span> Processing...';
                statusContainer.innerHTML = '';
                
                const token = await tokenize(paymentMethod);
                const paymentResults = await createPayment(token);
                
                console.log('Payment Success', paymentResults);
                statusContainer.innerHTML = '<div class="alert alert-success">Payment successful! The seller will contact you with account details.</div>';
                cardButton.style.display = 'none';
                
            } catch (e) {
                cardButton.disabled = false;
                cardButton.innerHTML = 'Pay ${{ "%.2f"|format(listing.price) }}';
                statusContainer.innerHTML = '<div class="alert alert-error">Payment failed. Please try again.</div>';
                console.error(e.message);
            }
        }
        
        async function tokenize(paymentMethod) {
            const tokenResult = await paymentMethod.tokenize();
            if (tokenResult.status === 'OK') {
                return tokenResult.token;
            } else {
                let errorMessage = `Tokenization failed with status: ${tokenResult.status}`;
                if (tokenResult.errors) {
                    errorMessage += ` and errors: ${JSON.stringify(
                        tokenResult.errors
                    )}`;
                }
                
                throw new Error(errorMessage);
            }
        }
        
        document.addEventListener('DOMContentLoaded', async function () {
            if (!window.Square) {
                throw new Error('Square.js failed to load properly');
            }
            
            let payments;
            try {
                payments = window.Square.payments(appId, locationId);
            } catch (e) {
                console.error('Initializing Square Payments failed', e);
                return;
            }
            
            let card;
            try {
                card = await initializeCard(payments);
            } catch (e) {
                console.error('Initializing Card failed', e);
                return;
            }
            
            document.getElementById('card-button').addEventListener('click', async function (event) {
                await handlePaymentMethodSubmission(event, card);
            });
        });
    </script>
    {% endif %}
</div>
{% endblock %}
"""

# Helper function for rendering templates
def render_template(template_name, **kwargs):
    templates = {
        'base.html': BASE_TEMPLATE,
        'home.html': HOME_TEMPLATE,
        'sell.html': SELL_TEMPLATE,
        'listing_detail.html': LISTING_DETAIL_TEMPLATE
    }
    
    if template_name in templates:
        return render_template_string(templates[template_name], **kwargs)
    
    return "Template not found", 404

# Routes
@app.route('/')
def index():
    listings = Listing.query.order_by(Listing.created_at.desc()).all()
    return render_template('home.html', listings=listings)

@app.route('/login')
def login():
    discord_auth_url = f"https://discord.com/api/oauth2/authorize?{urlencode({
        'client_id': DISCORD_CLIENT_ID,
        'redirect_uri': f'{APP_BASE_URL}/callback',
        'response_type': 'code',
        'scope': 'identify'
    })}"
    return redirect(discord_auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        flash('Authorization failed', 'error')
        return redirect(url_for('index'))
    
    # Exchange code for token
    token_url = "https://discord.com/api/oauth2/token"
    data = {
        'client_id': DISCORD_CLIENT_ID,
        'client_secret': DISCORD_CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': f'{APP_BASE_URL}/callback'
    }
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    r = requests.post(token_url, data=data, headers=headers)
    r.raise_for_status()
    tokens = r.json()
    
    # Get user info
    user_url = "https://discord.com/api/users/@me"
    headers = {
        'Authorization': f"Bearer {tokens['access_token']}"
    }
    
    r = requests.get(user_url, headers=headers)
    r.raise_for_status()
    user_data = r.json()
    
    # Create or update user
    user_id = int(user_data['id'])
    user = User.query.get(user_id)
    
    if not user:
        user = User(
            id=user_id,
            username=user_data['username'],
            discriminator=user_data.get('discriminator', '0')
        )
        db.session.add(user)
    else:
        user.username = user_data['username']
        user.discriminator = user_data.get('discriminator', '0')
    
    db.session.commit()
    
    # Store in session
    session['user_id'] = user_id
    session['username'] = user_data['username']
    
    flash('Successfully logged in!', 'success')
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Successfully logged out!', 'success')
    return redirect(url_for('index'))

@app.route('/onboard-seller-square')
def onboard_seller_square():
    if 'user_id' not in session:
        flash('Please login first', 'error')
        return redirect(url_for('login'))
    
    square_auth_url = f"https://connect.squareup.com/oauth2/authorize?{urlencode({
        'client_id': SQUARE_APP_ID,
        'scope': 'PAYMENTS_WRITE',
        'state': str(session['user_id']),
        'redirect_uri': f'{APP_BASE_URL}/square-callback'
    })}"
    
    return redirect(square_auth_url)

@app.route('/square-callback')
def square_callback():
    code = request.args.get('code')
    state = request.args.get('state')
    
    if not code or not state:
        flash('Square authorization failed', 'error')
        return redirect(url_for('index'))
    
    # Exchange code for token
    token_url = "https://connect.squareup.com/oauth2/token"
    data = {
        'client_id': SQUARE_APP_ID,
        'client_secret': SQUARE_APP_SECRET,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': f'{APP_BASE_URL}/square-callback'
    }
    
    r = requests.post(token_url, json=data)
    r.raise_for_status()
    token_data = r.json()
    
    # Update user with Square credentials
    user_id = int(state)
    user = User.query.get(user_id)
    
    if user:
        user.square_merchant_id = token_data['merchant_id']
        user.square_access_token = token_data['access_token']
        db.session.commit()
        flash('Square account connected successfully! You can now create listings.', 'success')
    else:
        flash('User not found', 'error')
    
    return redirect(url_for('sell'))

@app.route('/sell', methods=['GET', 'POST'])
def sell():
    if 'user_id' not in session:
        flash('Please login first', 'error')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    # Check if user has Square connected
    if not user.square_merchant_id:
        return redirect(url_for('onboard_seller_square'))
    
    if request.method == 'POST':
        listing = Listing(
            title=request.form['title'],
            rank=request.form['rank'],
            price=float(request.form['price']),
            description=request.form.get('description'),
            seller_id=user.id
        )
        db.session.add(listing)
        db.session.commit()
        
        flash('Listing created successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('sell.html')

@app.route('/listing/<int:listing_id>')
def listing_detail(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    
    # Check if user can purchase (logged in and not the seller)
    can_purchase = False
    if 'user_id' in session and session['user_id'] != listing.seller_id:
        can_purchase = True
    
    return render_template('listing_detail.html', 
                         listing=listing, 
                         can_purchase=can_purchase,
                         square_app_id=SQUARE_APP_ID,
                         square_location_id=SQUARE_LOCATION_ID)

@app.route('/create-square-payment', methods=['POST'])
def create_square_payment():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    source_id = data.get('sourceId')
    listing_id = data.get('listingId')
    
    if not source_id or not listing_id:
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Get listing and seller info
    listing = Listing.query.get(listing_id)
    if not listing:
        return jsonify({'error': 'Listing not found'}), 404
    
    # Calculate amounts in cents
    total_cents = int(listing.price * 100)
    app_fee_cents = int(total_cents * 0.15)  # 15% fee
    
    # Create payment with Square
    payment_url = f"https://connect.squareup.com/v2/payments"
    headers = {
        'Square-Version': '2024-01-18',
        'Authorization': f'Bearer {listing.seller.square_access_token}',
        'Content-Type': 'application/json'
    }
    
    payment_data = {
        'source_id': source_id,
        'idempotency_key': secrets.token_urlsafe(32),
        'amount_money': {
            'amount': total_cents,
            'currency': 'USD'
        },
        'app_fee_money': {
            'amount': app_fee_cents,
            'currency': 'USD'
        },
        'location_id': SQUARE_LOCATION_ID,
        'reference_id': f'listing_{listing_id}',
        'note': f'Purchase of Valorant account: {listing.title}'
    }
    
    try:
        r = requests.post(payment_url, json=payment_data, headers=headers)
        r.raise_for_status()
        payment_result = r.json()
        
        return jsonify({
            'success': True,
            'payment': payment_result['payment']
        })
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Square payment error: {str(e)}")
        return jsonify({'error': 'Payment processing failed'}), 500

# CLI Commands
@app.cli.command('db-create')
def db_create():
    """Create database tables"""
    with app.app_context():
        db.create_all()
        click.echo('Database tables created successfully!')

# Auto-create database tables on startup
with app.app_context():
    db.create_all()
    print("Database tables created/verified successfully!")

if __name__ == '__main__':
    app.run(debug=False)
