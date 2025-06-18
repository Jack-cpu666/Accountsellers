import os
import secrets
import requests
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import urlencode
from jinja2 import DictLoader

# ==============================================================================
# 0. HTML TEMPLATE (STORED AS A STRING)
# ==============================================================================

# By storing the HTML here, we eliminate the need for a 'templates' folder.
INDEX_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gamer Accounts Marketplace</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    {% if page_name == 'listing_detail' and can_purchase %}
    <script type="text/javascript" src="https://web.squarecdn.com/v1/square.js"></script>
    {% endif %}
    <style>
        :root {
            --color-bg-darkest: #0a0f18; --color-bg-dark: #111827; --color-bg-medium: #1f2937;
            --color-bg-light: #374151; --color-text-primary: #f9fafb; --color-text-secondary: #9ca3af;
            --color-accent-primary: #ef4444; --color-accent-secondary: #f97316; --color-success: #22c55e;
            --color-info: #3b82f6; --color-warning: #f59e0b;
            --font-family: 'Inter', -apple-system, sans-serif; --border-radius: 0.5rem;
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1);
        }
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        body { background-color: var(--color-bg-darkest); color: var(--color-text-primary); font-family: var(--font-family); line-height: 1.6; font-size: 16px; }
        .container { max-width: 1280px; margin: 0 auto; padding: 2rem; }
        h1, h2, h3 { font-weight: 700; margin-bottom: 1rem; }
        h1 { font-size: 2.25rem; } h2 { font-size: 1.8rem; } h3 { font-size: 1.5rem; }
        a { color: var(--color-accent-secondary); text-decoration: none; }
        /* --- Navbar --- */
        .navbar { background-color: var(--color-bg-dark); padding: 1rem 0; border-bottom: 1px solid var(--color-bg-light); position: sticky; top: 0; z-index: 1000; }
        .nav-container { display: flex; justify-content: space-between; align-items: center; max-width: 1280px; margin: 0 auto; padding: 0 2rem; }
        .nav-brand { font-size: 1.8rem; font-weight: 800; text-decoration: none; background: linear-gradient(45deg, var(--color-accent-primary), var(--color-accent-secondary)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .nav-links { display: flex; gap: 1rem; align-items: center; }
        .user-menu { display: flex; align-items: center; gap: 0.75rem; color: var(--color-text-secondary); }
        .user-menu img { width: 36px; height: 36px; border-radius: 50%; border: 2px solid var(--color-bg-light); }
        .user-menu-balance { font-weight: 600; color: var(--color-success); border: 1px solid var(--color-success); padding: 0.25rem 0.75rem; border-radius: var(--border-radius); }
        /* --- Buttons --- */
        .btn { display: inline-block; padding: 0.75rem 1.5rem; font-weight: 600; text-decoration: none; border-radius: var(--border-radius); transition: all 0.2s ease; border: none; cursor: pointer; font-size: 1rem; text-align: center;}
        .btn-primary { background: linear-gradient(45deg, var(--color-accent-primary), var(--color-accent-secondary)); color: white; box-shadow: 0 4px 15px rgba(239, 68, 68, 0.2); }
        .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(249, 115, 22, 0.3); }
        .btn-secondary { background-color: var(--color-bg-light); color: var(--color-text-primary); }
        .btn-secondary:hover { background-color: #4b5563; }
        .btn-success { background-color: var(--color-success); color: white; }
        .btn-danger { background-color: var(--color-accent-primary); color: white; }
        /* --- Forms --- */
        .form-container { max-width: 600px; margin: 2rem auto; padding: 2rem; background-color: var(--color-bg-dark); border-radius: var(--border-radius); }
        .form-group { margin-bottom: 1.5rem; }
        .form-label { display: block; margin-bottom: 0.5rem; font-weight: 500; }
        .form-control { width: 100%; padding: 0.75rem; background-color: var(--color-bg-light); border: 1px solid #4b5563; border-radius: var(--border-radius); color: var(--color-text-primary); font-size: 1rem; transition: border-color 0.2s; }
        .form-control:focus { outline: none; border-color: var(--color-accent-secondary); }
        textarea.form-control { min-height: 120px; resize: vertical; }
        /* --- Alerts --- */
        .alert { padding: 1rem; border-radius: var(--border-radius); margin-bottom: 1rem; border: 1px solid transparent; }
        .alert-success { background-color: rgba(34, 197, 94, 0.1); border-color: var(--color-success); color: var(--color-success); }
        .alert-error { background-color: rgba(239, 68, 68, 0.1); border-color: var(--color-accent-primary); color: var(--color-accent-primary); }
        .alert-info { background-color: rgba(59, 130, 246, 0.1); border-color: var(--color-info); color: var(--color-info); }
        .alert-warning { background-color: rgba(245, 158, 11, 0.1); border-color: var(--color-warning); color: var(--color-warning); }
        /* --- Listing Grid & Cards --- */
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 2rem; margin-top: 2rem; }
        .card { background-color: var(--color-bg-dark); border-radius: var(--border-radius); overflow: hidden; border: 1px solid var(--color-bg-light); transition: transform 0.2s, box-shadow 0.2s; display: flex; flex-direction: column; }
        .card:hover { transform: translateY(-5px); box-shadow: var(--shadow-lg); }
        .card-body { padding: 1.5rem; flex-grow: 1; display: flex; flex-direction: column; }
        .card-title { font-size: 1.25rem; font-weight: 600; margin-bottom: 0.5rem; color: var(--color-text-primary); }
        .card-seller { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem; font-size: 0.9rem; color: var(--color-text-secondary); }
        .card-seller img { width: 24px; height: 24px; border-radius: 50%; }
        .price { font-size: 1.75rem; font-weight: 700; color: var(--color-success); margin: 1rem 0; }
        .card .btn { margin-top: auto; }
        /* --- Listing Detail Page --- */
        .listing-detail-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 2rem; align-items: start; }
        .listing-content, .listing-sidebar { background-color: var(--color-bg-dark); padding: 2rem; border-radius: var(--border-radius); }
        .listing-header { border-bottom: 1px solid var(--color-bg-light); padding-bottom: 1rem; margin-bottom: 1.5rem; }
        .listing-description { white-space: pre-wrap; color: var(--color-text-secondary); line-height: 1.8; }
        #card-container { background-color: var(--color-bg-darkest); padding: 1rem; border-radius: var(--border-radius); }
        .loading { display: inline-block; width: 20px; height: 20px; border: 3px solid rgba(255, 255, 255, 0.3); border-radius: 50%; border-top-color: white; animation: spin 1s ease-in-out infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }
        /* --- Wallet Page --- */
        .wallet-container { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; align-items: start;}
        .balance-card { background-color: var(--color-bg-dark); padding: 2rem; border-radius: var(--border-radius); text-align: center; }
        .balance-label { font-size: 1.2rem; color: var(--color-text-secondary); }
        .balance-amount { font-size: 3rem; font-weight: 800; color: var(--color-success); margin: 0.5rem 0; }
        /* --- Admin & Tables --- */
        .admin-table { width: 100%; border-collapse: collapse; margin-top: 2rem; background-color: var(--color-bg-dark); border-radius: var(--border-radius); overflow: hidden; }
        .admin-table th, .admin-table td { padding: 1rem; text-align: left; border-bottom: 1px solid var(--color-bg-light); }
        .admin-table th { background-color: var(--color-bg-medium); }
        .admin-table tr:last-child td { border-bottom: none; }
        .admin-table .avatar-small { width: 40px; height: 40px; border-radius: 50%; vertical-align: middle; margin-right: 1rem; }
        .status-banned { color: var(--color-accent-primary); font-weight: 600; }
        .status-active { color: var(--color-success); font-weight: 600; }
        .status-pending { color: var(--color-warning); font-weight: 600; }
        .status-completed { color: var(--color-success); font-weight: 600; }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <a href="{{ url_for('index') }}" class="nav-brand">GamerAccounts</a>
            <div class="nav-links">
                {% if current_user %}
                    <a href="{{ url_for('sell') }}" class="btn btn-secondary">Sell Account</a>
                    <div class="user-menu">
                        <a href="{{ url_for('wallet') }}" class="user-menu-balance" title="My Wallet">
                            ${{ "%.2f"|format(current_user.balance) }}
                        </a>
                        <a href="{{ url_for('my_activity') }}" title="My Activity">
                            <img src="{{ current_user.get_avatar_url() }}" alt="User Avatar">
                        </a>
                        <span>{{ current_user.username }}</span>
                        <a href="{{ url_for('logout') }}" class="btn btn-secondary">Logout</a>
                    </div>
                {% else %}
                    <a href="{{ url_for('login') }}" class="btn btn-primary">Login with Discord</a>
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

        {# =================================== PAGE CONTENT RENDERER =================================== #}

        {% if page_name == 'home' %}
            <h1>Active Listings</h1>
            <div class="grid">
                {% for listing in listings %}
                <div class="card">
                    <div class="card-body">
                        <h3 class="card-title">{{ listing.title }}</h3>
                        <p class="card-seller">
                            <img src="{{ listing.seller.get_avatar_url() }}" alt="">
                            <span>{{ listing.seller.username }}</span>
                        </p>
                        <div class="price">${{ "%.2f"|format(listing.price) }}</div>
                        <a href="{{ url_for('listing_detail', listing_id=listing.id) }}" class="btn btn-primary">View Details</a>
                    </div>
                </div>
                {% else %}
                <div class="alert alert-info">No listings available yet. Be the first to sell!</div>
                {% endfor %}
            </div>

        {% elif page_name == 'listing_detail' %}
            <div class="listing-detail-grid">
                <div class="listing-content">
                    <div class="listing-header"><h1>{{ listing.title }}</h1><p>Listed by {{ listing.seller.username }}</p></div>
                    <h3>Description</h3><p class="listing-description">{{ listing.description or 'No description provided.' }}</p>
                </div>
                <div class="listing-sidebar">
                    <h3>Purchase Account</h3><div class="price">${{ "%.2f"|format(listing.price) }}</div>
                    {% if listing.status == 'sold' %}<div class="alert alert-warning">This account has been sold.</div>
                    {% elif can_purchase %}
                    <div id="payment-form">
                        <div id="card-container"></div>
                        <button id="card-button" type="button" class="btn btn-primary" style="width: 100%; margin-top: 1rem;">Pay ${{ "%.2f"|format(listing.price) }}</button>
                        <div id="payment-status-container" style="margin-top: 1rem;"></div>
                    </div>
                    {% elif current_user and current_user.id == listing.seller_id %}<div class="alert alert-info">This is your own listing.</div>
                    {% else %}<div class="alert alert-info">Please log in to purchase this item.</div>
                    {% endif %}
                </div>
            </div>
            {% if can_purchase %}
            <script>
                const appId = '{{ square_app_id }}'; const locationId = '{{ square_location_id }}';
                async function initializeCard(payments) { const card = await payments.card(); await card.attach('#card-container'); return card; }
                async function createPayment(token) {
                    const r = await fetch('{{ url_for("create_square_payment") }}', {
                        method: 'POST', headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ sourceId: token, listingId: {{ listing.id }} })
                    });
                    if (r.ok) return r.json(); const e = await r.json(); throw new Error(e.error);
                }
                async function tokenize(paymentMethod) { const r = await paymentMethod.tokenize(); if (r.status === 'OK') return r.token; throw new Error(`Tokenization failed: ${r.status}`); }
                document.addEventListener('DOMContentLoaded', async function () {
                    if (!window.Square) return; const payments = window.Square.payments(appId, locationId);
                    const card = await initializeCard(payments);
                    document.getElementById('card-button').addEventListener('click', async function (event) {
                        event.preventDefault();
                        const btn = document.getElementById('card-button'); const status = document.getElementById('payment-status-container');
                        try {
                            btn.disabled = true; btn.innerHTML = '<span class="loading"></span> Processing...';
                            const token = await tokenize(card); const res = await createPayment(token);
                            status.innerHTML = `<div class="alert alert-success">Payment successful! The seller has been credited.</div>`;
                            btn.style.display = 'none';
                            window.location.href = res.redirect_url;
                        } catch (e) {
                            btn.disabled = false; btn.innerHTML = 'Pay ${{ "%.2f"|format(listing.price) }}';
                            status.innerHTML = `<div class="alert alert-error">${e.message}</div>`;
                        }
                    });
                });
            </script>
            {% endif %}

        {% elif page_name == 'sell' %}
            <div class="form-container">
                <h1>Create New Listing</h1>
                <form method="POST">
                    <div class="form-group"><label class="form-label">Title</label><input type="text" name="title" class="form-control" required></div>
                    <div class="form-group"><label class="form-label">Price (USD)</label><input type="number" name="price" class="form-control" required min="1.00" step="0.01"></div>
                    <div class="form-group"><label class="form-label">Description</label><textarea name="description" class="form-control" rows="6"></textarea></div>
                    <button type="submit" class="btn btn-primary" style="width: 100%;">Create Listing</button>
                </form>
            </div>
        
        {% elif page_name == 'my_activity' %}
            <h1>My Activity</h1><h2>My Listings</h2>
            <div class="grid">
                {% for listing in my_listings %}<div class="card"><div class="card-body">
                    <h3>{{ listing.title }}</h3>
                    <p>Status: <span style="font-weight: bold; color: {{ 'var(--color-success)' if listing.status == 'available' else 'var(--color-warning)' }}">{{ listing.status|capitalize }}</span></p>
                    <div class="price">${{ "%.2f"|format(listing.price) }}</div>
                    <a href="{{ url_for('listing_detail', listing_id=listing.id) }}" class="btn btn-secondary">View Listing</a>
                </div></div>{% else %}<p>You have not created any listings yet.</p>{% endfor %}
            </div>

        {% elif page_name == 'wallet' %}
            <h1>My Wallet</h1>
            <div class="wallet-container">
                <div class="balance-card">
                    <p class="balance-label">Available for Withdrawal</p>
                    <p class="balance-amount">${{ "%.2f"|format(current_user.balance) }}</p>
                    <p class="balance-label">A {{ platform_fee }}% fee is applied to each sale.</p>
                </div>
                <div class="form-container" style="margin: 0;">
                    <h2>Request Withdrawal</h2>
                    <form method="POST">
                        <div class="form-group"><label class="form-label">Amount (USD)</label><input type="number" name="amount" class="form-control" required min="1.00" step="0.01" max="{{ current_user.balance }}"></div>
                        <div class="form-group"><label class="form-label">Payout Method</label><select name="method" class="form-control" required><option value="PayPal">PayPal</option><option value="CashApp">CashApp</option></select></div>
                        <div class="form-group"><label class="form-label">Payout Info (PayPal Email or $CashTag)</label><input type="text" name="payout_info" class="form-control" required></div>
                        <button type="submit" class="btn btn-primary" style="width: 100%;">Request Payout</button>
                    </form>
                </div>
            </div>
            <h2 style="margin-top: 3rem;">Withdrawal History</h2>
            <table class="admin-table">
                <thead><tr><th>Date</th><th>Amount</th><th>Method</th><th>Info</th><th>Status</th></tr></thead>
                <tbody>
                {% for w in withdrawals %}<tr><td>{{ w.requested_at.strftime('%Y-%m-%d %H:%M') }}</td><td>${{ "%.2f"|format(w.amount) }}</td><td>{{ w.method }}</td><td>{{ w.payout_info }}</td><td><span class="status-{{ w.status }}">{{ w.status|capitalize }}</span></td></tr>
                {% else %}<tr><td colspan="5" style="text-align: center;">No withdrawal requests yet.</td></tr>{% endfor %}
                </tbody>
            </table>

        {% elif page_name == 'admin_login' %}
            <div class="form-container">
                <h1>Admin Login</h1>
                <form method="POST">
                    <div class="form-group"><label class="form-label">Password</label><input type="password" name="password" class="form-control" required></div>
                    <button type="submit" class="btn btn-primary" style="width: 100%;">Login</button>
                </form>
            </div>

        {% elif page_name == 'admin_dashboard' %}
            <h1>Admin Dashboard</h1>
            <h2>Pending Withdrawals</h2>
            <table class="admin-table">
                 <thead><tr><th>User</th><th>Date</th><th>Amount</th><th>Method</th><th>Info</th><th>Action</th></tr></thead>
                 <tbody>
                    {% for w in pending_withdrawals %}<tr><td>{{ w.user.username }}</td><td>{{ w.requested_at.strftime('%Y-%m-%d') }}</td><td>${{ "%.2f"|format(w.amount) }}</td><td>{{ w.method }}</td><td>{{ w.payout_info }}</td>
                        <td><form method="POST" action="{{ url_for('admin_complete_withdrawal', withdrawal_id=w.id) }}" style="display:inline;"><button type="submit" class="btn btn-success">Mark as Paid</button></form></td>
                    </tr>
                    {% else %}<tr><td colspan="6" style="text-align: center;">No pending withdrawals.</td></tr>{% endfor %}
                 </tbody>
            </table>
            <h2 style="margin-top: 3rem;">User Management</h2>
            <table class="admin-table">
                <thead><tr><th>User Info</th><th>Balance</th><th>Status</th><th>Actions</th></tr></thead>
                <tbody>
                    {% for user in users %}<tr>
                        <td><img src="{{ user.get_avatar_url() }}" class="avatar-small"> {{ user.username }}</td>
                        <td style="color:var(--color-success); font-weight: 600;">${{ "%.2f"|format(user.balance) }}</td>
                        <td>{% if user.is_banned %}<span class="status-banned">Banned</span>{% else %}<span class="status-active">Active</span>{% endif %}</td>
                        <td>
                            {% if user.is_banned %}<form action="{{ url_for('unban_user', user_id=user.id) }}" method="POST"><button type="submit" class="btn btn-success">Unban</button></form>
                            {% else %}<form action="{{ url_for('ban_user', user_id=user.id) }}" method="POST"><button type="submit" class="btn btn-danger">Ban</button></form>{% endif %}
                        </td>
                    </tr>{% endfor %}
                </tbody>
            </table>
        {% endif %}
    </div>
</body>
</html>
"""

# ==============================================================================
# 1. APP INITIALIZATION & CONFIGURATION
# ==============================================================================

app = Flask(__name__)
app.jinja_loader = DictLoader({'index.html': INDEX_HTML_TEMPLATE})

# --- Hardcoded Configuration ---
app.config['SECRET_KEY'] = 'xK9mN3pQ7rT5wY2zB4dF6hJ8kL1nP3sV5xC7bN9mQ2wE4rT6'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///marketplace.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- Hardcoded Secrets & Settings ---
ADMIN_PASSWORD = 'AEaeAEae123@'
PLATFORM_FEE_PERCENTAGE = 15

# Your Master Square Credentials
SQUARE_APP_ID = 'sq0idp-3lHcPZwip9351EAnAer92A'
SQUARE_LOCATION_ID = 'LMNMA0HYA66VX'
SQUARE_ACCESS_TOKEN = 'EAAAl4vy95lvz5ACW3P_SUr-FSeHSGDuEniKxlytApO5jhN-0fcW1LRxcDgxfn7F'

# Discord OAuth
DISCORD_CLIENT_ID = '1384772758046507099'
DISCORD_REDIRECT_URI = f'https://accountsellers.onrender.com/callback'
DISCORD_CLIENT_SECRET = 'T5-jdB_fYB24v8tL7PNgQZ704EKeWeeN' # Note: Storing secrets in code is not recommended for production.

db = SQLAlchemy(app)

# ==============================================================================
# 2. DATABASE MODELS
# ==============================================================================

class User(db.Model):
    id = db.Column(db.BigInteger, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    avatar_hash = db.Column(db.String(100), nullable=True)
    is_banned = db.Column(db.Boolean, default=False, nullable=False)
    balance = db.Column(db.Float, default=0.0, nullable=False)
    listings = db.relationship('Listing', backref='seller', lazy='dynamic')
    withdrawals = db.relationship('Withdrawal', backref='user', lazy='dynamic')

    def get_avatar_url(self):
        if self.avatar_hash: return f"https://cdn.discordapp.com/avatars/{self.id}/{self.avatar_hash}.png"
        return "https://cdn.discordapp.com/embed/avatars/0.png"

class Listing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='available', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    seller_id = db.Column(db.BigInteger, db.ForeignKey('user.id'), nullable=False)

class Withdrawal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    method = db.Column(db.String(50), nullable=False)
    payout_info = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)

# ==============================================================================
# 3. HELPER FUNCTIONS & DECORATORS
# ==============================================================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('You must be logged in to view this page.', 'error')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if user and user.is_banned:
            session.clear()
            flash('Your account has been banned.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_user():
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    return dict(current_user=user)

# ==============================================================================
# 4. CORE ROUTES (HOME, LISTINGS, SELLING)
# ==============================================================================

@app.route('/')
def index():
    listings = Listing.query.filter_by(status='available').order_by(Listing.created_at.desc()).all()
    return render_template('index.html', page_name='home', listings=listings)

@app.route('/sell', methods=['GET', 'POST'])
@login_required
def sell():
    if request.method == 'POST':
        new_listing = Listing(
            title=request.form['title'],
            price=float(request.form['price']),
            description=request.form.get('description'),
            seller_id=session['user_id']
        )
        db.session.add(new_listing)
        db.session.commit()
        flash('Listing created successfully!', 'success')
        return redirect(url_for('listing_detail', listing_id=new_listing.id))
    return render_template('index.html', page_name='sell')

@app.route('/listing/<int:listing_id>')
def listing_detail(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    can_purchase = 'user_id' in session and session['user_id'] != listing.seller_id and listing.status == 'available'
    return render_template('index.html', page_name='listing_detail', listing=listing, can_purchase=can_purchase,
                           square_app_id=SQUARE_APP_ID, square_location_id=SQUARE_LOCATION_ID)

@app.route('/my-activity')
@login_required
def my_activity():
    my_listings = Listing.query.filter_by(seller_id=session['user_id']).order_by(Listing.created_at.desc()).all()
    return render_template('index.html', page_name='my_activity', my_listings=my_listings)

# ==============================================================================
# 5. AUTHENTICATION ROUTES
# ==============================================================================

@app.route('/login')
def login():
    discord_auth_url = f"https://discord.com/api/oauth2/authorize?{urlencode({'client_id': DISCORD_CLIENT_ID, 'redirect_uri': DISCORD_REDIRECT_URI, 'response_type': 'code', 'scope': 'identify'})}"
    return redirect(discord_auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    token_data = {'client_id': DISCORD_CLIENT_ID, 'client_secret': DISCORD_CLIENT_SECRET, 'grant_type': 'authorization_code', 'code': code, 'redirect_uri': DISCORD_REDIRECT_URI}
    r = requests.post("https://discord.com/api/oauth2/token", data=token_data)
    if not r.ok:
        flash('Discord authentication failed.', 'error')
        return redirect(url_for('index'))
    
    headers = {'Authorization': f"Bearer {r.json()['access_token']}"}
    user_r = requests.get("https://discord.com/api/users/@me", headers=headers)
    user_data = user_r.json()
    user_id = int(user_data['id'])

    user = User.query.get(user_id)
    if not user:
        user = User(id=user_id, username=user_data['username'], avatar_hash=user_data.get('avatar'))
        db.session.add(user)
    else:
        if user.is_banned:
            flash('Your account has been banned.', 'error')
            return redirect(url_for('index'))
        user.username = user_data['username']
        user.avatar_hash = user_data.get('avatar')
    
    db.session.commit()
    session['user_id'] = user.id
    flash('Successfully logged in!', 'success')
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Successfully logged out.', 'info')
    return redirect(url_for('index'))

# ==============================================================================
# 6. PAYMENT & WALLET ROUTES
# ==============================================================================

@app.route('/create-square-payment', methods=['POST'])
@login_required
def create_square_payment():
    data = request.get_json()
    listing = Listing.query.get(data.get('listingId'))
    if not listing or listing.status != 'available':
        return jsonify({'error': 'Listing not available'}), 400

    payment_data = {
        'source_id': data.get('sourceId'),
        'idempotency_key': secrets.token_hex(16),
        'amount_money': {'amount': int(listing.price * 100), 'currency': 'USD'},
        'location_id': SQUARE_LOCATION_ID,
        'note': f"Purchase of listing #{listing.id}: {listing.title}"
    }
    headers = {'Square-Version': '2023-12-13', 'Authorization': f'Bearer {SQUARE_ACCESS_TOKEN}', 'Content-Type': 'application/json'}
    r = requests.post("https://connect.squareup.com/v2/payments", json=payment_data, headers=headers)
    
    if r.ok:
        seller = listing.seller
        earnings = listing.price * (1 - (PLATFORM_FEE_PERCENTAGE / 100.0))
        seller.balance += earnings
        listing.status = 'sold'
        db.session.commit()
        flash(f'Purchase successful! The seller has been credited ${"%.2f"|format(earnings)}.', 'success')
        return jsonify({'success': True, 'redirect_url': url_for('index')})
    else:
        error_detail = r.json().get('errors', [{}])[0].get('detail', 'Payment processing failed.')
        return jsonify({'error': error_detail}), 500

@app.route('/wallet', methods=['GET', 'POST'])
@login_required
def wallet():
    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        amount = float(request.form.get('amount'))
        if amount > user.balance:
            flash('Withdrawal amount cannot exceed your balance.', 'error')
        elif amount < 1.00:
            flash('Minimum withdrawal is $1.00.', 'error')
        else:
            new_withdrawal = Withdrawal(user_id=user.id, amount=amount, method=request.form.get('method'), payout_info=request.form.get('payout_info'))
            user.balance -= amount
            db.session.add(new_withdrawal)
            db.session.commit()
            flash('Withdrawal request submitted successfully.', 'success')
        return redirect(url_for('wallet'))
    
    withdrawals = user.withdrawals.order_by(Withdrawal.requested_at.desc()).all()
    return render_template('index.html', page_name='wallet', withdrawals=withdrawals, platform_fee=PLATFORM_FEE_PERCENTAGE)

# ==============================================================================
# 7. ADMIN ROUTES
# ==============================================================================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['is_admin'] = True
            return redirect(url_for('admin_dashboard'))
        flash('Incorrect password.', 'error')
    return render_template('index.html', page_name='admin_login')

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    users = User.query.order_by(User.username).all()
    pending_withdrawals = Withdrawal.query.filter_by(status='pending').order_by(Withdrawal.requested_at.asc()).all()
    return render_template('index.html', page_name='admin_dashboard', users=users, pending_withdrawals=pending_withdrawals)

@app.route('/admin/withdrawal/<int:withdrawal_id>/complete', methods=['POST'])
@admin_required
def admin_complete_withdrawal(withdrawal_id):
    withdrawal = Withdrawal.query.get_or_404(withdrawal_id)
    withdrawal.status = 'completed'
    db.session.commit()
    flash(f'Withdrawal for {withdrawal.user.username} marked as complete.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/user/<int:user_id>/ban', methods=['POST'])
@admin_required
def ban_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_banned = True
    db.session.commit()
    flash(f'User {user.username} has been banned.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/user/<int:user_id>/unban', methods=['POST'])
@admin_required
def unban_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_banned = False
    db.session.commit()
    flash(f'User {user.username} has been unbanned.', 'success')
    return redirect(url_for('admin_dashboard'))

# ==============================================================================
# 8. APP STARTUP & DB SETUP
# ==============================================================================

with app.app_context():
    # This check ensures db.create_all() only runs if the database file doesn't exist.
    # It's a simple way to handle initialization on platforms like Render.
    instance_path = app.instance_path
    if not os.path.exists(os.path.join(instance_path, 'marketplace.db')):
        if not os.path.exists(instance_path):
            os.makedirs(instance_path)
        print("Database not found. Creating all tables...")
        db.create_all()
        print("Database tables created.")

if __name__ == '__main__':
    app.run(debug=True)
