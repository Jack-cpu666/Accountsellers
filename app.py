import os
import secrets
import requests
from datetime import datetime
from functools import wraps
from flask import Flask, render_template_string, render_template, request, redirect, url_for, session, jsonify, flash
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
        .user-menu img { width: 36px; height: 36px; border-radius: 50%; }
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
        /* --- Listing Grid --- */
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
        .listing-header h1 { margin-bottom: 0.25rem; }
        .listing-header p { color: var(--color-text-secondary); }
        .listing-description { white-space: pre-wrap; color: var(--color-text-secondary); line-height: 1.8; }
        #card-container { background-color: var(--color-bg-darkest); padding: 1rem; border-radius: var(--border-radius); }
        .loading { display: inline-block; width: 20px; height: 20px; border: 3px solid rgba(255, 255, 255, 0.3); border-radius: 50%; border-top-color: white; animation: spin 1s ease-in-out infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }
        /* --- Chat --- */
        .chat-container { display: flex; flex-direction: column; height: 75vh; background-color: var(--color-bg-dark); border-radius: var(--border-radius); overflow: hidden; box-shadow: var(--shadow-lg); }
        .chat-header { padding: 1rem 1.5rem; background-color: var(--color-bg-medium); border-bottom: 1px solid var(--color-bg-light); }
        .message-area { flex-grow: 1; padding: 1.5rem; overflow-y: auto; display: flex; flex-direction: column; gap: 1rem; }
        .message { padding: 0.75rem 1.25rem; border-radius: 1.25rem; max-width: 75%; word-wrap: break-word; line-height: 1.4; }
        .message.sent { background: linear-gradient(45deg, var(--color-accent-primary), var(--color-accent-secondary)); color: white; align-self: flex-end; border-bottom-right-radius: 0.25rem; }
        .message.received { background-color: var(--color-bg-light); align-self: flex-start; border-bottom-left-radius: 0.25rem; }
        .message .timestamp { display: block; font-size: 0.75rem; color: rgba(255,255,255,0.6); margin-top: 0.25rem; text-align: right; }
        .message.received .timestamp { color: var(--color-text-secondary); }
        .message-input-area { display: flex; padding: 1rem; border-top: 1px solid var(--color-bg-light); background: var(--color-bg-medium); }
        .message-input-area .form-control { margin-right: 1rem; background-color: var(--color-bg-darkest); }
        /* --- Admin --- */
        .admin-table { width: 100%; border-collapse: collapse; margin-top: 2rem; }
        .admin-table th, .admin-table td { padding: 1rem; text-align: left; border-bottom: 1px solid var(--color-bg-light); }
        .admin-table th { background-color: var(--color-bg-medium); }
        .admin-table .avatar-small { width: 40px; height: 40px; border-radius: 50%; }
        .status-banned { color: var(--color-accent-primary); font-weight: 600; }
        .status-active { color: var(--color-success); font-weight: 600; }
        /* --- Filters --- */
        .filter-bar { background-color: var(--color-bg-dark); padding: 1rem; border-radius: var(--border-radius); margin-bottom: 2rem; display: flex; gap: 1rem; align-items: center; }
        .filter-bar label { font-weight: 500; }
        .filter-bar .form-control { width: auto; }
        .filter-bar .btn { padding: 0.5rem 1rem; }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <a href="{{ url_for('index') }}" class="nav-brand">GamerAccounts</a>
            <div class="nav-links">
                {% if session.get('user_id') %}
                    <a href="{{ url_for('sell') }}" class="btn btn-secondary">Sell Account</a>
                    <div class="user-menu">
                        <a href="{{ url_for('my_activity') }}">
                            <img src="{{ session.get('avatar_url') }}" alt="User Avatar">
                        </a>
                        <span>{{ session.get('username') }}</span>
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

        {# =================================== PAGE CONTENT SWITCH =================================== #}

        {% if page_name == 'home' %}
            <h1>Active Listings</h1>
            <div class="filter-bar">
                <form method="GET" action="{{ url_for('index') }}" class="filter-bar">
                    <label for="game_id">Filter by Game:</label>
                    <select name="game_id" id="game_id" class="form-control">
                        <option value="">All Games</option>
                        {% for game in games %}
                        <option value="{{ game.id }}" {% if game.id == selected_game_id %}selected{% endif %}>{{ game.name }}</option>
                        {% endfor %}
                    </select>
                    <button type="submit" class="btn btn-secondary">Filter</button>
                    <a href="{{url_for('index')}}" class="btn btn-secondary">Clear</a>
                </form>
            </div>
            <div class="grid">
                {% for listing in listings %}
                <div class="card">
                    <div class="card-body">
                        <h3 class="card-title">{{ listing.title }}</h3>
                        <p class="card-seller">
                            <img src="{{ listing.seller.get_avatar_url() }}" alt="">
                            <span>{{ listing.seller.username }}</span>
                        </p>
                        <p class="card-game" style="color: var(--color-text-secondary);">Game: {{ listing.game.name }}</p>
                        <div class="price">${{ "%.2f"|format(listing.price) }}</div>
                        <a href="{{ url_for('listing_detail', listing_id=listing.id) }}" class="btn btn-primary">View Details</a>
                    </div>
                </div>
                {% else %}
                <p>No listings found for the selected game. Try another!</p>
                {% endfor %}
            </div>

        {% elif page_name == 'listing_detail' %}
            <div class="listing-detail-grid">
                <div class="listing-content">
                    <div class="listing-header">
                        <h1>{{ listing.title }}</h1>
                        <p>Listed by {{ listing.seller.username }} on {{ listing.created_at.strftime('%B %d, %Y') }}</p>
                    </div>
                    <h3>Description</h3>
                    <p class="listing-description">{{ listing.description or 'No description provided.' }}</p>
                </div>
                <div class="listing-sidebar">
                    <h3>Purchase Account</h3>
                    <div class="price">${{ "%.2f"|format(listing.price) }}</div>
                    {% if listing.status == 'sold' %}
                        <div class="alert alert-warning">This account has been sold.</div>
                    {% elif can_purchase %}
                    <div id="payment-form">
                        <div id="card-container"></div>
                        <button id="card-button" type="button" class="btn btn-primary" style="width: 100%; margin-top: 1rem;">
                            Pay ${{ "%.2f"|format(listing.price) }}
                        </button>
                        <div id="payment-status-container" style="margin-top: 1rem;"></div>
                    </div>
                    {% elif session.get('user_id') == listing.seller_id %}
                        <div class="alert alert-info">This is your own listing.</div>
                    {% else %}
                        <div class="alert alert-info">Please log in to purchase this item.</div>
                    {% endif %}
                </div>
            </div>
            {% if can_purchase %}
            <script>
                const appId = '{{ square_app_id }}';
                const locationId = '{{ square_location_id }}';
                async function initializeCard(payments) { const card = await payments.card(); await card.attach('#card-container'); return card; }
                async function createPayment(token) {
                    const paymentResponse = await fetch('{{ url_for("create_square_payment") }}', {
                        method: 'POST', headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ sourceId: token, listingId: {{ listing.id }} })
                    });
                    if (paymentResponse.ok) return paymentResponse.json();
                    const errorBody = await paymentResponse.json(); throw new Error(errorBody.error);
                }
                async function tokenize(paymentMethod) {
                    const tokenResult = await paymentMethod.tokenize();
                    if (tokenResult.status === 'OK') return tokenResult.token;
                    throw new Error(`Tokenization failed: ${tokenResult.status}`);
                }
                document.addEventListener('DOMContentLoaded', async function () {
                    if (!window.Square) return;
                    const payments = window.Square.payments(appId, locationId);
                    const card = await initializeCard(payments);
                    document.getElementById('card-button').addEventListener('click', async function (event) {
                        event.preventDefault();
                        const cardButton = document.getElementById('card-button');
                        const statusContainer = document.getElementById('payment-status-container');
                        try {
                            cardButton.disabled = true; cardButton.innerHTML = '<span class="loading"></span> Processing...';
                            const token = await tokenize(card);
                            const paymentResults = await createPayment(token);
                            statusContainer.innerHTML = `<div class="alert alert-success">Payment successful! You can now chat with the seller.</div><a href="${paymentResults.chat_url}" class="btn btn-success" style="width:100%; margin-top:1rem;">Go to Chat</a>`;
                            cardButton.style.display = 'none';
                        } catch (e) {
                            cardButton.disabled = false; cardButton.innerHTML = 'Pay ${{ "%.2f"|format(listing.price) }}';
                            statusContainer.innerHTML = `<div class="alert alert-error">${e.message}</div>`;
                        }
                    });
                });
            </script>
            {% endif %}

        {% elif page_name == 'sell' %}
            <div class="form-container">
                <h1>Create New Listing</h1>
                <form method="POST">
                    <div class="form-group">
                        <label for="title" class="form-label">Title</label>
                        <input type="text" id="title" name="title" class="form-control" required placeholder="e.g., Radiant Account with All Agents">
                    </div>
                    <div class="form-group">
                        <label for="game_id" class="form-label">Game</label>
                        <select id="game_id" name="game_id" class="form-control" required>
                            <option value="">Select a game...</option>
                            {% for game in games %}<option value="{{ game.id }}">{{ game.name }}</option>{% endfor %}
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="price" class="form-label">Price (USD)</label>
                        <input type="number" id="price" name="price" class="form-control" required min="1.00" step="0.01" placeholder="99.99">
                    </div>
                    <div class="form-group">
                        <label for="description" class="form-label">Description</label>
                        <textarea id="description" name="description" class="form-control" rows="6" placeholder="Describe account details, skins, agents unlocked, etc."></textarea>
                    </div>
                    <button type="submit" class="btn btn-primary" style="width: 100%;">Create Listing</button>
                </form>
            </div>

        {% elif page_name == 'my_activity' %}
            <h1>My Activity</h1>
            <h2>My Listings</h2>
            <div class="grid">
                {% for listing in my_listings %}
                <div class="card">
                    <div class="card-body">
                        <h3 class="card-title">{{ listing.title }}</h3>
                        <p>Status: <span style="font-weight: bold; color: {{ 'var(--color-success)' if listing.status == 'available' else 'var(--color-warning)' }}">{{ listing.status|capitalize }}</span></p>
                        <div class="price">${{ "%.2f"|format(listing.price) }}</div>
                        <a href="{{ url_for('listing_detail', listing_id=listing.id) }}" class="btn btn-secondary">View Listing</a>
                        {% if listing.status == 'sold' %}
                        <a href="{{ url_for('chat', purchase_id=listing.purchase.id) }}" class="btn btn-primary" style="margin-top: 1rem;">Go to Chat</a>
                        {% endif %}
                    </div>
                </div>
                {% else %}
                <p>You have not created any listings yet.</p>
                {% endfor %}
            </div>
            <h2 style="margin-top: 3rem;">My Purchases</h2>
            <div class="grid">
                {% for purchase in my_purchases %}
                <div class="card">
                    <div class="card-body">
                        <h3 class="card-title">{{ purchase.listing.title }}</h3>
                        <p class="card-seller">
                            <img src="{{ purchase.listing.seller.get_avatar_url() }}" alt="">
                            <span>Purchased from {{ purchase.listing.seller.username }}</span>
                        </p>
                        <div class="price">${{ "%.2f"|format(purchase.purchase_price) }}</div>
                        <a href="{{ url_for('chat', purchase_id=purchase.id) }}" class="btn btn-primary">Go to Chat</a>
                    </div>
                </div>
                {% else %}
                <p>You have not purchased any accounts yet.</p>
                {% endfor %}
            </div>

        {% elif page_name == 'chat' %}
            <div class="chat-container">
                <div class="chat-header">
                    <h3>Chat with {{ other_user.username }}</h3>
                    <p style="color: var(--color-text-secondary); margin:0;">Regarding: {{ purchase.listing.title }}</p>
                </div>
                <div class="message-area" id="message-area">
                    {% for message in messages %}
                        <div class="message {% if message.sender_id == session['user_id'] %}sent{% else %}received{% endif %}">
                            <p>{{ message.content }}</p>
                            <span class="timestamp">{{ message.timestamp.strftime('%b %d, %H:%M') }}</span>
                        </div>
                    {% endfor %}
                </div>
                <div class="message-input-area">
                    <form method="POST" style="display: flex; width: 100%;">
                        <input type="text" name="content" class="form-control" placeholder="Type your message..." autocomplete="off" required>
                        <button type="submit" class="btn btn-primary">Send</button>
                    </form>
                </div>
            </div>
            <script>
                const messageArea = document.getElementById('message-area');
                messageArea.scrollTop = messageArea.scrollHeight;
            </script>

        {% elif page_name == 'admin_login' %}
            <div class="form-container">
                <h1>Admin Login</h1>
                <form method="POST">
                    <div class="form-group">
                        <label for="password" class="form-label">Password</label>
                        <input type="password" name="password" id="password" class="form-control" required>
                    </div>
                    <button type="submit" class="btn btn-primary" style="width: 100%;">Login</button>
                </form>
            </div>

        {% elif page_name == 'admin_dashboard' %}
            <h1>Admin Dashboard - User Management</h1>
            <table class="admin-table">
                <thead>
                    <tr><th>Avatar</th><th>Username</th><th>User ID</th><th>Status</th><th>Actions</th></tr>
                </thead>
                <tbody>
                    {% for user in users %}
                    <tr>
                        <td><img src="{{ user.get_avatar_url() }}" class="avatar-small"></td>
                        <td>{{ user.username }}</td>
                        <td>{{ user.id }}</td>
                        <td>
                            {% if user.is_banned %}
                                <span class="status-banned">Banned</span>
                            {% else %}
                                <span class="status-active">Active</span>
                            {% endif %}
                        </td>
                        <td>
                            {% if user.is_banned %}
                                <form action="{{ url_for('unban_user', user_id=user.id) }}" method="POST" style="display:inline;">
                                    <button type="submit" class="btn btn-success">Unban</button>
                                </form>
                            {% else %}
                                <form action="{{ url_for('ban_user', user_id=user.id) }}" method="POST" style="display:inline;">
                                    <button type="submit" class="btn btn-danger">Ban</button>
                                </form>
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
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

# --- Load template from the string variable above instead of a file ---
# This makes all `render_template('index.html', ...)` calls work without a templates folder.
app.jinja_loader = DictLoader({'index.html': INDEX_HTML_TEMPLATE})

# --- Hardcoded Configuration ---
app.config['SECRET_KEY'] = 'xK9mN3pQ7rT5wY2zB4dF6hJ8kL1nP3sV5xC7bN9mQ2wE4rT6'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///marketplace.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- Hardcoded Secrets & Settings ---
ADMIN_PASSWORD = 'AEaeAEae123@'
APP_BASE_URL = 'https://accountsellers.onrender.com'
APPLICATION_FEE_PERCENTAGE = 10  # 10% platform fee

# Discord OAuth
DISCORD_CLIENT_ID = '1384772758046507099'
DISCORD_CLIENT_SECRET = 'T5-jdB_fYB24v8tL7PNgQZ704EKeWeeN'
DISCORD_REDIRECT_URI = f'{APP_BASE_URL}/callback'

# Square OAuth
SQUARE_APP_ID = 'sq0idp-3lHcPZwip9351EAnAer92A'
SQUARE_APP_SECRET = 'sq0csp-nrd_xRzRYwheZKcKWfnJWbP8Dbsr85SUWcQra6d0utM'
SQUARE_ENVIRONMENT = 'production'
SQUARE_LOCATION_ID = 'LMNMA0HYA66VX'
SQUARE_REDIRECT_URI = f'{APP_BASE_URL}/square-callback'

# --- Database Initialization ---
db = SQLAlchemy(app)

# ==============================================================================
# 2. DATABASE MODELS
# ==============================================================================

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.BigInteger, primary_key=True)  # Discord ID
    username = db.Column(db.String(80), nullable=False)
    avatar_hash = db.Column(db.String(100), nullable=True)
    is_banned = db.Column(db.Boolean, default=False, nullable=False)
    
    square_merchant_id = db.Column(db.String(100), unique=True, nullable=True)
    square_access_token = db.Column(db.String(255), unique=True, nullable=True)
    
    listings = db.relationship('Listing', backref='seller', lazy='dynamic', foreign_keys='Listing.seller_id')
    purchases = db.relationship('Purchase', backref='buyer', lazy='dynamic', foreign_keys='Purchase.buyer_id')

    def get_avatar_url(self):
        if self.avatar_hash:
            return f"https://cdn.discordapp.com/avatars/{self.id}/{self.avatar_hash}.png"
        return "https://cdn.discordapp.com/embed/avatars/0.png"

class Game(db.Model):
    __tablename__ = 'games'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    icon_url = db.Column(db.String(255), nullable=True) # URL to game icon
    listings = db.relationship('Listing', backref='game', lazy='dynamic')

class Listing(db.Model):
    __tablename__ = 'listings'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='available', nullable=False) # available, sold, delisted
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    seller_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)
    purchase = db.relationship('Purchase', backref='listing', uselist=False)

class Purchase(db.Model):
    __tablename__ = 'purchases'
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey('listings.id'), unique=True, nullable=False)
    buyer_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False)
    seller_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False)
    purchase_price = db.Column(db.Float, nullable=False)
    application_fee = db.Column(db.Float, nullable=False)
    square_payment_id = db.Column(db.String(100), unique=True, nullable=False)
    purchased_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    messages = db.relationship('Message', backref='purchase', lazy='dynamic', cascade="all, delete-orphan")

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    purchase_id = db.Column(db.Integer, db.ForeignKey('purchases.id'), nullable=False)
    sender_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

# ==============================================================================
# 3. HELPER FUNCTIONS & DECORATORS
# ==============================================================================

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            flash('Admin access required.', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

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

# ==============================================================================
# 4. MAIN & LISTING ROUTES
# ==============================================================================

@app.route('/')
def index():
    games = Game.query.order_by(Game.name).all()
    selected_game_id = request.args.get('game_id', type=int)
    
    query = Listing.query.filter_by(status='available')
    if selected_game_id:
        query = query.filter_by(game_id=selected_game_id)
        
    listings = query.order_by(Listing.created_at.desc()).all()
    
    return render_template('index.html', page_name='home', listings=listings, games=games, selected_game_id=selected_game_id)

@app.route('/sell', methods=['GET', 'POST'])
@login_required
def sell():
    user = User.query.get(session['user_id'])
    if not user.square_merchant_id:
        flash('You must connect a Square account to receive payments before you can sell.', 'warning')
        return redirect(url_for('onboard_seller_square'))
        
    if request.method == 'POST':
        new_listing = Listing(
            title=request.form['title'],
            game_id=int(request.form['game_id']),
            price=float(request.form['price']),
            description=request.form.get('description'),
            seller_id=user.id
        )
        db.session.add(new_listing)
        db.session.commit()
        
        flash('Listing created successfully!', 'success')
        return redirect(url_for('listing_detail', listing_id=new_listing.id))
    
    games = Game.query.order_by(Game.name).all()
    return render_template('index.html', page_name='sell', games=games)

@app.route('/listing/<int:listing_id>')
def listing_detail(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    
    can_purchase = False
    if 'user_id' in session and session['user_id'] != listing.seller_id and listing.status == 'available':
        can_purchase = True
    
    return render_template('index.html', page_name='listing_detail', listing=listing, can_purchase=can_purchase,
                           square_app_id=SQUARE_APP_ID, square_location_id=SQUARE_LOCATION_ID)

@app.route('/my-activity')
@login_required
def my_activity():
    user_id = session['user_id']
    my_listings = Listing.query.filter_by(seller_id=user_id).order_by(Listing.created_at.desc()).all()
    my_purchases = Purchase.query.filter_by(buyer_id=user_id).order_by(Purchase.purchased_at.desc()).all()
    
    return render_template('index.html', page_name='my_activity', my_listings=my_listings, my_purchases=my_purchases)


# ==============================================================================
# 5. AUTHENTICATION & ONBOARDING ROUTES
# ==============================================================================

@app.route('/login')
def login():
    discord_auth_url = f"https://discord.com/api/oauth2/authorize?{urlencode({
        'client_id': DISCORD_CLIENT_ID,
        'redirect_uri': DISCORD_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'identify'
    })}"
    return redirect(discord_auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return redirect(url_for('index'))
    
    token_data = {
        'client_id': DISCORD_CLIENT_ID, 'client_secret': DISCORD_CLIENT_SECRET,
        'grant_type': 'authorization_code', 'code': code, 'redirect_uri': DISCORD_REDIRECT_URI
    }
    r = requests.post("https://discord.com/api/oauth2/token", data=token_data)
    if not r.ok:
        flash('Discord authentication failed.', 'error')
        return redirect(url_for('index'))
    
    headers = {'Authorization': f"Bearer {r.json()['access_token']}"}
    user_r = requests.get("https://discord.com/api/users/@me", headers=headers)
    user_data = user_r.json()
    
    user = User.query.get(int(user_data['id']))
    if not user:
        user = User(id=int(user_data['id']))
    
    if user.is_banned:
        flash('Your account has been banned from this platform.', 'error')
        return redirect(url_for('index'))
        
    user.username = user_data['username']
    user.avatar_hash = user_data.get('avatar')
    db.session.add(user)
    db.session.commit()
    
    session['user_id'] = user.id
    session['username'] = user.username
    session['avatar_url'] = user.get_avatar_url()
    
    flash('Successfully logged in!', 'success')
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Successfully logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/onboard-seller-square')
@login_required
def onboard_seller_square():
    square_auth_url = f"https://connect.squareup.com/oauth2/authorize?{urlencode({
        'client_id': SQUARE_APP_ID,
        'scope': 'PAYMENTS_WRITE',
        'session': 'false',
        'state': str(session['user_id']),
        'redirect_uri': SQUARE_REDIRECT_URI
    })}"
    return redirect(square_auth_url)

@app.route('/square-callback')
def square_callback():
    code = request.args.get('code')
    user_id = request.args.get('state')
    
    if not code or 'user_id' not in session or session['user_id'] != int(user_id):
        flash('Square authorization failed or session mismatch.', 'error')
        return redirect(url_for('index'))
    
    token_data = {
        'client_id': SQUARE_APP_ID, 'client_secret': SQUARE_APP_SECRET,
        'code': code, 'grant_type': 'authorization_code', 'redirect_uri': SQUARE_REDIRECT_URI
    }
    r = requests.post("https://connect.squareup.com/oauth2/token", json=token_data)
    if not r.ok:
        flash(f'Failed to connect Square account. Error: {r.json().get("errors", [{}])[0].get("detail", "Unknown")}', 'error')
        return redirect(url_for('sell'))
        
    token_info = r.json()
    user = User.query.get(int(user_id))
    user.square_merchant_id = token_info['merchant_id']
    user.square_access_token = token_info['access_token']
    db.session.commit()
    
    flash('Square account connected successfully! You can now create listings.', 'success')
    return redirect(url_for('sell'))

# ==============================================================================
# 6. PAYMENT & MESSAGING ROUTES
# ==============================================================================

@app.route('/create-square-payment', methods=['POST'])
@login_required
def create_square_payment():
    data = request.get_json()
    source_id = data.get('sourceId')
    listing_id = data.get('listingId')
    
    listing = Listing.query.get(listing_id)
    if not listing or listing.status != 'available':
        return jsonify({'error': 'Listing not available'}), 400

    if listing.seller.is_banned:
        return jsonify({'error': 'Seller is currently banned'}), 400
    
    total_cents = int(listing.price * 100)
    app_fee_cents = int(total_cents * (APPLICATION_FEE_PERCENTAGE / 100))
    
    payment_data = {
        'source_id': source_id,
        'idempotency_key': secrets.token_hex(16),
        'amount_money': {'amount': total_cents, 'currency': 'USD'},
        'app_fee_money': {'amount': app_fee_cents, 'currency': 'USD'},
        'location_id': SQUARE_LOCATION_ID,
        'note': f"Purchase of listing #{listing.id}: {listing.title}"
    }
    
    headers = {
        'Square-Version': '2023-12-13',
        'Authorization': f'Bearer {listing.seller.square_access_token}',
        'Content-Type': 'application/json'
    }
    
    r = requests.post(f"https://connect.squareup.com/v2/payments", json=payment_data, headers=headers)
    
    if r.ok:
        payment_result = r.json()['payment']
        
        listing.status = 'sold'
        new_purchase = Purchase(
            listing_id=listing.id,
            buyer_id=session['user_id'],
            seller_id=listing.seller_id,
            purchase_price=listing.price,
            application_fee=app_fee_cents / 100.0,
            square_payment_id=payment_result['id']
        )
        db.session.add(new_purchase)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'chat_url': url_for('chat', purchase_id=new_purchase.id)
        })
    else:
        errors = r.json().get('errors', [{}])
        error_detail = errors[0].get('detail', 'Payment processing failed.')
        return jsonify({'error': error_detail}), 500

@app.route('/chat/<int:purchase_id>', methods=['GET', 'POST'])
@login_required
def chat(purchase_id):
    purchase = Purchase.query.get_or_404(purchase_id)
    current_user_id = session['user_id']

    if current_user_id != purchase.buyer_id and current_user_id != purchase.seller_id:
        flash('You do not have permission to view this conversation.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        content = request.form.get('content')
        if content:
            new_message = Message(
                purchase_id=purchase_id,
                sender_id=current_user_id,
                content=content
            )
            db.session.add(new_message)
            db.session.commit()
        return redirect(url_for('chat', purchase_id=purchase_id))

    other_user_id = purchase.seller_id if current_user_id == purchase.buyer_id else purchase.buyer_id
    other_user = User.query.get(other_user_id)
    messages = purchase.messages.order_by(Message.timestamp.asc()).all()
    
    return render_template('index.html', page_name='chat', purchase=purchase, other_user=other_user, messages=messages)

# ==============================================================================
# 7. ADMIN ROUTES
# ==============================================================================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['is_admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Incorrect password.', 'error')
    return render_template('index.html', page_name='admin_login')

@app.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    users = User.query.order_by(User.username).all()
    return render_template('index.html', page_name='admin_dashboard', users=users)

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
# 8. APP STARTUP & COMMANDS
# ==============================================================================

# This ensures the DB is created on first run in environments like Render
with app.app_context():
    if not os.path.exists(os.path.join('instance', 'marketplace.db')):
        db.create_all()
        # Seed games
        games_to_seed = [
            {'name': 'Valorant', 'icon_url': '...'},
            {'name': 'League of Legends', 'icon_url': '...'},
            {'name': 'CS:GO 2', 'icon_url': '...'},
            {'name': 'Overwatch 2', 'icon_url': '...'}
        ]
        for g in games_to_seed:
            if not Game.query.filter_by(name=g['name']).first():
                db.session.add(Game(**g))
        db.session.commit()
        print("Database created and seeded on startup.")
