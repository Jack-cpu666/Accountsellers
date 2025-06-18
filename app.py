# Save this file as app.py
import os
import secrets
import requests
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import urlencode
from jinja2 import DictLoader, FileSystemLoader # Using FileSystemLoader is better practice but sticking to user request

# ==============================================================================
# 0. HTML TEMPLATE (REBUILT TO REPLICATE ELDORADO.GG)
# ==============================================================================

# This is a massive HTML string to keep it in one file as requested.
# It uses Jinja2 templating to render different pages and components.
ELDORADO_REPLICA_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Eldorado Replica</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --color-bg-primary: #121218; --color-bg-secondary: #1f2129; --color-bg-tertiary: #2e3039;
            --color-border: #3d3f4a; --color-text-primary: #ffffff; --color-text-secondary: #a3a3ac;
            --color-accent-primary: #ffc23f; --color-accent-secondary: #f97316; --color-success: #22c55e;
            --color-danger: #ef4444; --color-info: #3b82f6;
            --font-family: 'Inter', sans-serif; --border-radius: 0.25rem;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background-color: var(--color-bg-primary); color: var(--color-text-primary); font-family: var(--font-family); font-size: 14px; }
        .container { max-width: 1400px; margin: 0 auto; padding: 1.5rem; }
        a { color: var(--color-text-secondary); text-decoration: none; transition: color 0.2s; }
        a:hover { color: var(--color-accent-primary); }
        h1, h2, h3 { font-weight: 600; margin-bottom: 1rem; }
        h1 { font-size: 1.75rem; } h2 { font-size: 1.25rem; }

        /* --- Header --- */
        .header { background-color: var(--color-bg-secondary); border-bottom: 1px solid var(--color-border); padding: 1rem 1.5rem; display: flex; align-items: center; gap: 2rem; }
        .header-brand { font-size: 1.5rem; font-weight: 800; color: var(--color-accent-primary); }
        .header-nav a { font-weight: 500; padding: 0.5rem 1rem; }
        .header-search { flex-grow: 1; position: relative; }
        .header-search input { width: 100%; background-color: var(--color-bg-tertiary); border: 1px solid var(--color-border); border-radius: var(--border-radius); padding: 0.75rem 1rem 0.75rem 2.5rem; color: var(--color-text-primary); font-size: 1rem; }
        .header-search .search-icon { position: absolute; left: 0.75rem; top: 50%; transform: translateY(-50%); color: var(--color-text-secondary); }
        .header-actions { display: flex; align-items: center; gap: 1rem; }
        .btn { display: inline-block; padding: 0.6rem 1.2rem; font-weight: 600; border-radius: var(--border-radius); border: none; cursor: pointer; text-align: center; }
        .btn-primary { background-color: var(--color-accent-primary); color: var(--color-bg-primary); }
        .btn-primary:hover { background-color: #ffcf66; }
        .btn-secondary { background-color: var(--color-bg-tertiary); color: var(--color-text-primary); }
        .user-menu { display: flex; align-items: center; gap: 0.75rem; }
        .user-menu img { width: 32px; height: 32px; border-radius: 50%; }

        /* --- Content Grids (Homepage) --- */
        .content-section { background-color: var(--color-bg-secondary); border-radius: var(--border-radius); padding: 1.5rem; margin-bottom: 1.5rem; }
        .main-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.5rem; }
        .game-list { list-style: none; }
        .game-list-item a { display: flex; align-items: center; gap: 1rem; padding: 0.75rem; border-radius: var(--border-radius); }
        .game-list-item a:hover { background-color: var(--color-bg-tertiary); }
        .game-list-item img { width: 28px; height: 28px; object-fit: contain; }
        .game-list-item span { font-weight: 500; }
        .sub-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1.5rem; }

        /* --- Listing Page (Valorant example) --- */
        .listing-page-grid { display: grid; grid-template-columns: 280px 1fr; gap: 1.5rem; }
        .filters { background-color: var(--color-bg-secondary); padding: 1.5rem; border-radius: var(--border-radius); }
        .filter-group { margin-bottom: 1.5rem; }
        .filter-group label { font-weight: 600; display: block; margin-bottom: 0.75rem; }
        .filter-select, .filter-input { width: 100%; background-color: var(--color-bg-tertiary); border: 1px solid var(--color-border); border-radius: var(--border-radius); padding: 0.6rem 1rem; color: var(--color-text-primary); }
        .tag-list { display: flex; flex-wrap: wrap; gap: 0.5rem; }
        .tag { background-color: var(--color-bg-tertiary); padding: 0.4rem 0.8rem; border-radius: 1rem; cursor: pointer; transition: background-color 0.2s; }
        .tag:hover { background-color: var(--color-border); }
        .listings-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.5rem; }
        .listing-card { background-color: var(--color-bg-secondary); border: 1px solid var(--color-border); border-radius: var(--border-radius); overflow: hidden; display: flex; flex-direction: column; transition: transform 0.2s, box-shadow 0.2s; }
        .listing-card:hover { transform: translateY(-4px); box-shadow: 0 5px 15px rgba(0,0,0,0.2); }
        .listing-card-image { height: 170px; background-size: cover; background-position: center; }
        .listing-card-body { padding: 1rem; flex-grow: 1; display: flex; flex-direction: column; }
        .card-region { font-size: 0.8rem; color: var(--color-text-secondary); margin-bottom: 0.5rem; }
        .card-title { font-size: 1rem; font-weight: 600; margin-bottom: 1rem; flex-grow: 1; }
        .card-seller-info { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
        .seller-name { display: flex; align-items: center; gap: 0.5rem; font-size: 0.9rem; }
        .seller-name img { width: 24px; height: 24px; border-radius: 50%; }
        .seller-rating { color: var(--color-text-secondary); font-size: 0.9rem; }
        .card-footer { display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--color-border); padding-top: 1rem; margin-top: 1rem; }
        .card-price { font-size: 1.25rem; font-weight: 700; color: var(--color-success); }
        .card-delivery { font-size: 0.9rem; color: var(--color-accent-primary); }
        
        /* --- Seller Form --- */
        .form-container { max-width: 700px; margin: 2rem auto; padding: 2rem; background-color: var(--color-bg-secondary); border-radius: var(--border-radius); }
        .form-group { margin-bottom: 1.5rem; }
        .form-label { display: block; margin-bottom: 0.5rem; font-weight: 500; }
        .form-control { width: 100%; padding: 0.75rem; background-color: var(--color-bg-tertiary); border: 1px solid var(--color-border); border-radius: var(--border-radius); color: var(--color-text-primary); font-size: 1rem; }
        textarea.form-control { min-height: 120px; resize: vertical; }
        .terms-box { background-color: var(--color-bg-tertiary); border: 1px solid var(--color-border); padding: 1rem; max-height: 200px; overflow-y: auto; font-size: 0.8rem; color: var(--color-text-secondary); margin-bottom: 1rem; }
        .terms-box ul { padding-left: 1.5rem; }
        .form-check { display: flex; align-items: center; gap: 0.75rem; }

        /* --- Admin Panel --- */
        .admin-table { width: 100%; border-collapse: collapse; margin-top: 2rem; background-color: var(--color-bg-secondary); border-radius: var(--border-radius); overflow: hidden; font-size: 0.9rem; }
        .admin-table th, .admin-table td { padding: 1rem; text-align: left; border-bottom: 1px solid var(--color-border); }
        .admin-table th { background-color: var(--color-bg-tertiary); }
        .admin-table tr:last-child td { border-bottom: none; }
        .admin-table .avatar-small { width: 32px; height: 32px; border-radius: 50%; vertical-align: middle; margin-right: 1rem; }
        .status-banned, .btn-danger { background-color: var(--color-danger); color: white; padding: 0.2rem 0.5rem; border-radius: var(--border-radius); }
        .status-active, .btn-success { background-color: var(--color-success); color: white; padding: 0.2rem 0.5rem; border-radius: var(--border-radius);}
        .status-pending { background-color: var(--color-accent-primary); color: var(--color-bg-primary); padding: 0.2rem 0.5rem; border-radius: var(--border-radius); }
        .admin-actions form { display: inline-block; margin-right: 0.5rem; }
        .btn-sm { padding: 0.4rem 0.8rem; font-size: 0.8rem; }
        
        /* --- Flash Messages & Footer --- */
        .alert { padding: 1rem; border-radius: var(--border-radius); margin: 0 0 1.5rem 0; border: 1px solid transparent; }
        .alert-success { background-color: rgba(34, 197, 94, 0.1); border-color: var(--color-success); color: var(--color-success); }
        .alert-error { background-color: rgba(239, 68, 68, 0.1); border-color: var(--color-danger); color: var(--color-danger); }
        .alert-info { background-color: rgba(59, 130, 246, 0.1); border-color: var(--color-info); color: var(--color-info); }
        .footer { background-color: var(--color-bg-secondary); padding: 3rem 1.5rem; border-top: 1px solid var(--color-border); margin-top: 3rem; }
        .footer-top { display: flex; justify-content: space-between; align-items: center; padding-bottom: 2rem; border-bottom: 1px solid var(--color-border); margin-bottom: 2rem; }
        .payment-icons { display: flex; gap: 1rem; align-items: center; }
        .payment-icons img { height: 24px; }
        .footer-grid { display: grid; grid-template-columns: 1.5fr repeat(3, 1fr); gap: 2rem; }
        .footer-about .logo { font-size: 1.5rem; font-weight: 800; color: var(--color-accent-primary); margin-bottom: 1rem; }
        .footer-about p { color: var(--color-text-secondary); margin-bottom: 1rem; }
        .social-icons { display: flex; gap: 1rem; }
        .footer-links h4 { margin-bottom: 1rem; font-weight: 600; }
        .footer-links ul { list-style: none; }
        .footer-links ul li { margin-bottom: 0.5rem; }
    </style>
</head>
<body>
    <header class="header">
        <a href="{{ url_for('index') }}" class="header-brand">Eldorado</a>
        <nav class="header-nav">
            <a href="#">Currency</a><a href="{{ url_for('accounts_page') }}">Accounts</a><a href="#">Top Up</a><a href="#">Items</a><a href="#">Boosting</a>
        </nav>
        <div class="header-search">
             <svg class="search-icon" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
             <input type="text" placeholder="Search Eldorado">
        </div>
        <div class="header-actions">
            {% if current_user %}
                <a href="{{ url_for('sell') }}" class="btn btn-secondary">Sell</a>
                <div class="user-menu">
                    <a href="#" title="My Wallet">${{ "%.2f"|format(current_user.balance) }}</a>
                    <img src="{{ current_user.get_avatar_url() }}" alt="User Avatar">
                    <span>{{ current_user.username }}</span>
                    <a href="{{ url_for('logout') }}" class="btn-secondary" style="padding: 0.5rem">Logout</a>
                </div>
            {% else %}
                <a href="{{ url_for('login') }}" class="btn btn-primary">Log in</a>
            {% endif %}
        </div>
    </header>

    <main class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        {# =================================== PAGE CONTENT RENDERER =================================== #}
        
        {# --- HOMEPAGE --- #}
        {% if page_name == 'home' %}
            <div class="main-grid">
                <div class="content-section">
                    <ul class="game-list">
                        <li class="game-list-item"><a href="#"><img src="https://w9g7dlhw3kaank.www.eldorado.gg/eZx6JAX2LagMBqHE2KA6uArDjiyageBtaOKAc27OFObfoiPUo8YSah1i8j7hZYWNGihERevCUutO1QkbN76V10FUlep7XGZtQUTClCsR"><span>Grand Theft Auto 5</span></a></li>
                        <li class="game-list-item"><a href="{{ url_for('accounts_page') }}"><img src="https://w9g7dlhw3kaank.www.eldorado.gg/1VQh9pUkzuJzipbqBVYVQEhZcStbCK5o5iFA1b6HXK6inxwNZtrwk9N7s2qCP9TKOWXjwJoi2XcKtesOALht64ctcYR436Z8ymTtRyvr"><span>Valorant</span></a></li>
                        <li class="game-list-item"><a href="#"><img src="https://w9g7dlhw3kaank.www.eldorado.gg/AVmE7gXYnryQmSVw9inDmTA6OPr7JrnDqhdEvJOkjT5X3L4E14QnEmWSf32sjraD87Nu40B7Y9SwXPAMCmtUHkYZ3RFP9OOi3Oe60MXZ"><span>Call of Duty</span></a></li>
                        <li class="game-list-item"><a href="#"><img src="https://w9g7dlhw3kaank.www.eldorado.gg/QuuoMpKV4bQkriTtBSTeL3yiVJGUgGIoQRprm4x1EKtms4aY6zVNZzyMSLJKEJTD0L6Jji9ZqcHVaAUrscRclqUNP1Qsy3Cl2T5HG4XV"><span>Roblox</span></a></li>
                        <li class="game-list-item"><a href="#"><img src="https://w9g7dlhw3kaank.www.eldorado.gg/0M2H9KHtSgKEILZYSvsREfBgcOrdsu7qp3YNCzF1LddCvWVJnl0twy6M3LiFXbdzbcvp01QvjLJ380cedUVx5xPMaklFAdPidPVYUYtL"><span>League of Legends</span></a></li>
                    </ul>
                </div>
                <div class="content-section">
                     <ul class="game-list">
                        <li class="game-list-item"><a href="#"><img src="https://w9g7dlhw3kaank.www.eldorado.gg/CXbg4YWohvH5bnTn28GAn6b7fncdfefZKgUCNc5fzrfmon6G6L93FS8XMn11mSpVjder8szjFpiRoWhUhlcDS3t0ZekShePFeJYeBc8f"><span>Fortnite</span></a></li>
                        <li class="game-list-item"><a href="#"><img src="https://w9g7dlhw3kaank.www.eldorado.gg/JAz4O53sP1UahsZv58p5d4d5aGU6LfUcKWvCA4HQJR2qNAwRufr3VLHFOXvvil9LDKZF8e7Fjd7jM6xl7yav5Ix3BNmdC0pM3b3W8Z5F"><span>Rainbow Six Siege</span></a></li>
                        <li class="game-list-item"><a href="#"><img src="https://assetsdelivery.eldorado.gg/v7/_assets_/icons/v21/1.png"><span>Old School RuneScape</span></a></li>
                        <li class="game-list-item"><a href="#"><img src="https://assetsdelivery.eldorado.gg/v7/_assets_/icons/v21/200.png"><span>Grow a Garden</span></a></li>
                        <li class="game-list-item"><a href="#"><img src="https://assetsdelivery.eldorado.gg/v7/_assets_/icons/v21/22.png"><span>Clash of Clans</span></a></li>
                    </ul>
                </div>
                <div class="content-section">
                    <ul class="game-list">
                        <li class="game-list-item"><a href="#"><img src="https://assetsdelivery.eldorado.gg/v7/_assets_/icons/v21/1.png"><span>Old School RuneScape Gold</span></a></li>
                        <li class="game-list-item"><a href="#"><img src="https://w9g7dlhw3kaank.www.eldorado.gg/QuuoMpKV4bQkriTtBSTeL3yiVJGUgGIoQRprm4x1EKtms4aY6zVNZzyMSLJKEJTD0L6Jji9ZqcHVaAUrscRclqUNP1Qsy3Cl2T5HG4XV"><span>Roblox Robux</span></a></li>
                        <li class="game-list-item"><a href="#"><img src="https://assetsdelivery.eldorado.gg/v7/_assets_/icons/v21/193.png"><span>EA Sports FC Coins</span></a></li>
                        <li class="game-list-item"><a href="#"><img src="https://assetsdelivery.eldorado.gg/v7/_assets_/icons/v21/16.png"><span>WoW Classic Era Gold</span></a></li>
                        <li class="game-list-item"><a href="#"><img src="https://assetsdelivery.eldorado.gg/v7/_assets_/icons/v21/2.png"><span>World of Warcraft Gold</span></a></li>
                    </ul>
                </div>
            </div>
            <div class="sub-grid">
                <div class="content-section">
                    <h2>Popular Boosting Services</h2>
                    <ul class="game-list">
                        <li class="game-list-item"><a href="#"><img src="https://w9g7dlhw3kaank.www.eldorado.gg/1VQh9pUkzuJzipbqBVYVQEhZcStbCK5o5iFA1b6HXK6inxwNZtrwk9N7s2qCP9TKOWXjwJoi2XcKtesOALht64ctcYR436Z8ymTtRyvr"><span>Valorant</span></a></li>
                        <li class="game-list-item"><a href="#"><img src="https://assetsdelivery.eldorado.gg/v7/_assets_/icons/v21/1.png"><span>Old School RuneScape</span></a></li>
                        <li class="game-list-item"><a href="#"><img src="https://w9g7dlhw3kaank.www.eldorado.gg/JAz4O53sP1UahsZv58p5d4d5aGU6LfUcKWvCA4HQJR2qNAwRufr3VLHFOXvvil9LDKZF8e7Fjd7jM6xl7yav5Ix3BNmdC0pM3b3W8Z5F"><span>Rainbow Six Siege</span></a></li>
                        <li class="game-list-item"><a href="#"><img src="https://assetsdelivery.eldorado.gg/v7/_assets_/icons/v21/72.png"><span>Rocket League</span></a></li>
                    </ul>
                </div>
                <div class="content-section">
                    <h2>Popular Items</h2>
                     <ul class="game-list">
                        <li class="game-list-item"><a href="#"><img src="https://assetsdelivery.eldorado.gg/v7/_assets_/icons/v21/200.png"><span>Grow a Garden</span></a></li>
                        <li class="game-list-item"><a href="#"><img src="https://w9g7dlhw3kaank.www.eldorado.gg/QuuoMpKV4bQkriTtBSTeL3yiVJGUgGIoQRprm4x1EKtms4aY6zVNZzyMSLJKEJTD0L6Jji9ZqcHVaAUrscRclqUNP1Qsy3Cl2T5HG4XV"><span>Roblox</span></a></li>
                    </ul>
                </div>
            </div>

        {# --- ACCOUNTS LISTING PAGE --- #}
        {% elif page_name == 'accounts_page' %}
            <h1>Valorant Accounts for Sale</h1>
            <div class="listing-page-grid">
                <aside class="filters">
                    <h3>Filters</h3>
                    <div class="filter-group"><label>Region</label><select class="filter-select"><option>EU/TR/MENA/CIS</option><option>NA</option></select></div>
                    <div class="filter-group"><label>Rank</label><select class="filter-select"><option>Any</option><option>Radiant</option><option>Immortal</option><option>Diamond</option></select></div>
                    <div class="filter-group"><label>Price</label><input type="text" class="filter-input" placeholder="Any"></div>
                    <div class="filter-group"><label>Quick Filters</label><div class="tag-list"><span class="tag">Ranked Ready</span><span class="tag">Smurf</span><span class="tag">Champions 2021</span></div></div>
                </aside>
                <div class="listings-container">
                    <div class="listings-grid">
                        {% for listing in listings %}
                        <a href="#" class="listing-card">
                           <div class="listing-card-image" style="background-image: url('{{ listing.image_url or 'https://placehold.co/400x200/2e3039/ffffff?text=Account' }}')"></div>
                           <div class="listing-card-body">
                               <p class="card-region">【EU/TR/MENA/CIS】· PC · Ranked Ready</p>
                               <h3 class="card-title">{{ listing.title }}</h3>
                               <div class="card-seller-info">
                                   <div class="seller-name">
                                       <img src="{{ listing.seller.get_avatar_url() }}" alt="">
                                       <span>{{ listing.seller.username }}</span>
                                   </div>
                                   <div class="seller-rating">99.8%</div>
                               </div>
                               <div class="card-footer">
                                   <div class="card-price">${{ "%.2f"|format(listing.price) }}</div>
                                   <div class="card-delivery">⚡ Instant</div>
                               </div>
                           </div>
                        </a>
                        {% else %}
                        <p>No approved listings available right now. Check back soon!</p>
                        {% endfor %}
                    </div>
                </div>
            </div>

        {# --- SELL PAGE --- #}
        {% elif page_name == 'sell' %}
            <div class="form-container">
                <h1>Submit New Listing for Review</h1>
                <p style="color:var(--color-text-secondary); margin-top:-0.5rem; margin-bottom: 2rem;">Your submission will be reviewed by an admin. If approved, it will appear on the marketplace.</p>
                <form method="POST">
                    <div class="form-group"><label class="form-label">Title (e.g., EU Radiant Account, 5 Skins)</label><input type="text" name="title" class="form-control" required></div>
                    <div class="form-group"><label class="form-label">Price (USD)</label><input type="number" name="price" class="form-control" required min="1.00" step="0.01"></div>
                    <div class="form-group"><label class="form-label">Account Details / Description</label><textarea name="description" class="form-control" rows="4" placeholder="Provide all relevant details about the account."></textarea></div>
                    <hr style="border-color: var(--color-border); margin: 2rem 0;">
                    <h2>Seller Verification</h2>
                    <div class="form-group"><label class="form-label">Are you the original owner of the account?</label><select name="q_owner" class="form-control" required><option value="yes">Yes</option><option value="no">No</option></select></div>
                    <div class="form-group"><label class="form-label">Provide the account login credentials (will be encrypted and stored securely)</label><textarea name="q_credentials" class="form-control" rows="3" required placeholder="example@email.com:password123"></textarea></div>
                    <div class="form-group"><label class="form-label">Optional: Image URL for the listing card</label><input type="text" name="image_url" class="form-control" placeholder="https://.../image.png"></div>
                    <hr style="border-color: var(--color-border); margin: 2rem 0;">
                    <div class="form-group">
                        <label class="form-label">Terms of Service</label>
                        <div class="terms-box">
                            <p>By submitting this listing, you agree to the following:</p>
                            <ul>
                                <li>You are the rightful owner of the account or have permission to sell it.</li>
                                <li>All information provided is accurate and not misleading.</li>
                                <li>You will not access the account after it has been sold.</li>
                                <li>Fraudulent activity will result in a permanent ban and forfeiture of funds.</li>
                                <li>A platform fee of {{ platform_fee }}% will be deducted from the final sale price.</li>
                            </ul>
                        </div>
                        <div class="form-check">
                            <input type="checkbox" id="terms" name="terms" required>
                            <label for="terms">I have read and agree to the Seller Terms of Service.</label>
                        </div>
                    </div>
                    <button type="submit" class="btn btn-primary" style="width: 100%; padding: 0.8rem;">Submit for Review</button>
                </form>
            </div>
        
        {# --- ADMIN LOGIN --- #}
        {% elif page_name == 'admin_login' %}
            <div class="form-container" style="max-width: 400px;">
                <h1>Admin Login</h1>
                <form method="POST">
                    <div class="form-group"><label class="form-label">Password</label><input type="password" name="password" class="form-control" required></div>
                    <button type="submit" class="btn btn-primary" style="width: 100%;">Login</button>
                </form>
            </div>

        {# --- ADMIN DASHBOARD --- #}
        {% elif page_name == 'admin_dashboard' %}
            <h1>Admin Dashboard</h1>
            
            <h2>Pending Listings for Approval</h2>
            <table class="admin-table">
                 <thead><tr><th>Seller</th><th>Title</th><th>Price</th><th>Submitted</th><th>Actions</th></tr></thead>
                 <tbody>
                    {% for l in pending_listings %}
                    <tr>
                        <td>{{ l.seller.username }}</td>
                        <td>{{ l.title }}</td>
                        <td>${{ "%.2f"|format(l.price) }}</td>
                        <td>{{ l.created_at.strftime('%Y-%m-%d') }}</td>
                        <td class="admin-actions">
                            <form method="POST" action="{{ url_for('admin_approve_listing', listing_id=l.id) }}"><button type="submit" class="btn-sm btn-success">Approve</button></form>
                            <form method="POST" action="{{ url_for('admin_deny_listing', listing_id=l.id) }}"><button type="submit" class="btn-sm btn-danger">Deny</button></form>
                        </td>
                    </tr>
                    {% else %}<tr><td colspan="5" style="text-align: center;">No pending listings to review.</td></tr>{% endfor %}
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
                        <td class="admin-actions">
                            {% if user.is_banned %}
                                <form action="{{ url_for('unban_user', user_id=user.id) }}" method="POST"><button type="submit" class="btn-sm btn-success">Unban</button></form>
                            {% else %}
                                <form action="{{ url_for('ban_user', user_id=user.id) }}" method="POST"><button type="submit" class="btn-sm btn-danger">Ban</button></form>
                            {% endif %}
                            <form action="{{ url_for('delete_user', user_id=user.id) }}" method="POST" onsubmit="return confirm('Are you sure you want to permanently delete this user and all their data?');">
                                <button type="submit" class="btn-sm btn-danger">Delete</button>
                            </form>
                        </td>
                    </tr>{% endfor %}
                </tbody>
            </table>
        {% endif %}

    </main>

    <footer class="footer">
        <div class="footer-top">
            <div class="payment-icons">
                <img src="https://assetsdelivery.eldorado.gg/v7/_assets_/payment-methods/visa.svg" alt="Visa">
                <img src="https://assetsdelivery.eldorado.gg/v7/_assets_/payment-methods/mastercard.svg" alt="Mastercard">
                <img src="https://assetsdelivery.eldorado.gg/v7/_assets_/payment-methods/amex.svg" alt="Amex">
                <img src="https://assetsdelivery.eldorado.gg/v7/_assets_/payment-methods/discover.svg" alt="Discover">
                <img src="https://assetsdelivery.eldorado.gg/v7/_assets_/payment-methods/gpay.svg" alt="Google Pay">
                <img src="https://assetsdelivery.eldorado.gg/v7/_assets_/payment-methods/applepay.svg" alt="Apple Pay">
                <span>+15 more</span>
            </div>
        </div>
        <div class="footer-grid">
            <div class="footer-about">
                <h3 class="logo">Eldorado</h3>
                <p>Join us today to level up your gaming experience!</p>
                <div class="social-icons">
                    <a href="#">Reddit</a> <a href="#">TikTok</a> <a href="#">X</a> <a href="#">Facebook</a> <a href="#">YouTube</a>
                </div>
            </div>
            <div class="footer-links">
                <h4>Eldorado</h4>
                <ul>
                    <li><a href="#">Help Center</a></li>
                    <li><a href="#">Contact us</a></li>
                    <li><a href="#">Bug Bounty</a></li>
                    <li><a href="#">Blog</a></li>
                    <li><a href="#">Become a Partner</a></li>
                </ul>
            </div>
            <div class="footer-links">
                <h4>Legal</h4>
                <ul>
                    <li><a href="#">Account Warranty</a></li>
                    <li><a href="#">TradeShield (Buying)</a></li>
                    <li><a href="#">TradeShield (Selling)</a></li>
                    <li><a href="#">Deposits</a></li>
                    <li><a href="#">Withdrawals</a></li>
                </ul>
            </div>
             <div class="footer-links">
                <h4>Policies</h4>
                <ul>
                    <li><a href="#">Account Seller Rules</a></li>
                    <li><a href="#">Seller Rules</a></li>
                    <li><a href="#">Changing Username</a></li>
                    <li><a href="#">Fees</a></li>
                    <li><a href="#">Refund Policy</a></li>
                </ul>
            </div>
        </div>
    </footer>
</body>
</html>
"""

# ==============================================================================
# 1. APP INITIALIZATION & CONFIGURATION
# ==============================================================================

app = Flask(__name__)
# Using DictLoader to keep everything in a single file as per user's code structure
app.jinja_loader = DictLoader({'layout.html': ELDORADO_REPLICA_TEMPLATE})

# --- Hardcoded Configuration (DANGEROUS: Use environment variables in production) ---
app.config['SECRET_KEY'] = 'xK9mN3pQ7rT5wY2zB4dF6hJ8kL1nP3sV5xC7bN9mQ2wE4rT6' # Replace with a new, random key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///marketplace.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- Hardcoded Secrets & Settings (DANGEROUS) ---
ADMIN_PASSWORD = 'AEaeAEae123@' # The requested hardcoded password
PLATFORM_FEE_PERCENTAGE = 15

# Discord OAuth Credentials
DISCORD_CLIENT_ID = '1384772758046507099'
DISCORD_CLIENT_SECRET = 'T5-jdB_fYB24v8tL7PNgQZ704EKeWeeN'
DISCORD_REDIRECT_URI = 'http://127.0.0.1:5000/callback' # CHANGE THIS to your production URL (e.g., https://accountsellers.onrender.com/callback)

db = SQLAlchemy(app)

# ==============================================================================
# 2. DATABASE MODELS (MODIFIED)
# ==============================================================================

class User(db.Model):
    id = db.Column(db.BigInteger, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    avatar_hash = db.Column(db.String(100), nullable=True)
    is_banned = db.Column(db.Boolean, default=False, nullable=False)
    balance = db.Column(db.Float, default=0.0, nullable=False)
    listings = db.relationship('Listing', backref='seller', lazy='dynamic', cascade="all, delete-orphan")

    def get_avatar_url(self):
        if self.avatar_hash: return f"https://cdn.discordapp.com/avatars/{self.id}/{self.avatar_hash}.png"
        return "https://cdn.discordapp.com/embed/avatars/0.png"

class Listing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    # NEW: Status for admin approval workflow.
    # 'pending': Awaiting admin review
    # 'approved': Live on the site
    # 'sold': Purchased by a user
    status = db.Column(db.String(20), default='pending', nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    seller_id = db.Column(db.BigInteger, db.ForeignKey('user.id'), nullable=False)

# ==============================================================================
# 3. HELPER FUNCTIONS & DECORATORS
# ==============================================================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('You must be logged in to view this page.', 'error')
            return redirect(url_for('index'))
        user = User.query.get(session['user_id'])
        if not user or user.is_banned:
            session.clear()
            flash('Your account is not active or has been banned.', 'error')
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
def inject_globals():
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    return dict(current_user=user, platform_fee=PLATFORM_FEE_PERCENTAGE)

# ==============================================================================
# 4. CORE & AUTHENTICATION ROUTES
# ==============================================================================

@app.route('/')
def index():
    return render_template('layout.html', page_name='home')

@app.route('/login')
def login():
    params = {'client_id': DISCORD_CLIENT_ID, 'redirect_uri': DISCORD_REDIRECT_URI, 'response_type': 'code', 'scope': 'identify'}
    return redirect(f"https://discord.com/api/oauth2/authorize?{urlencode(params)}")

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
        user.username = user_data['username']; user.avatar_hash = user_data.get('avatar')
    
    db.session.commit()
    session['user_id'] = user.id
    flash(f"Welcome, {user.username}! You've successfully logged in.", 'success')
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# ==============================================================================
# 5. SELLER & LISTING ROUTES
# ==============================================================================

@app.route('/accounts')
def accounts_page():
    # Only show listings that the admin has approved.
    approved_listings = Listing.query.filter_by(status='approved').order_by(Listing.created_at.desc()).all()
    return render_template('layout.html', page_name='accounts_page', listings=approved_listings)

@app.route('/sell', methods=['GET', 'POST'])
@login_required
def sell():
    if request.method == 'POST':
        # Create the listing with 'pending' status for admin review.
        new_listing = Listing(
            title=request.form['title'],
            price=float(request.form['price']),
            description=request.form.get('description'),
            image_url=request.form.get('image_url'),
            seller_id=session['user_id'],
            status='pending' # IMPORTANT: All new listings are pending
        )
        db.session.add(new_listing)
        db.session.commit()
        flash('Your listing has been submitted for review. It will be visible after admin approval.', 'success')
        return redirect(url_for('index'))
    return render_template('layout.html', page_name='sell')

# ==============================================================================
# 6. ADMIN ROUTES (NEW & IMPROVED)
# ==============================================================================

@app.route('/admingg', methods=['GET', 'POST'])
def admin_login():
    if session.get('is_admin'):
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['is_admin'] = True
            flash('Admin login successful.', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Incorrect password.', 'error')
    return render_template('layout.html', page_name='admin_login')

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    users = User.query.order_by(User.username).all()
    pending_listings = Listing.query.filter_by(status='pending').order_by(Listing.created_at.asc()).all()
    return render_template('layout.html', page_name='admin_dashboard', users=users, pending_listings=pending_listings)

@app.route('/admin/listing/<int:listing_id>/approve', methods=['POST'])
@admin_required
def admin_approve_listing(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    listing.status = 'approved'
    db.session.commit()
    flash(f'Listing "{listing.title}" has been approved.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/listing/<int:listing_id>/deny', methods=['POST'])
@admin_required
def admin_deny_listing(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    db.session.delete(listing)
    db.session.commit()
    flash(f'Listing "{listing.title}" has been denied and deleted.', 'success')
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

@app.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    username = user.username
    db.session.delete(user) # Cascade will delete their listings
    db.session.commit()
    flash(f'User {username} and all their data has been permanently deleted.', 'success')
    return redirect(url_for('admin_dashboard'))

# ==============================================================================
# 8. APP STARTUP & DB SETUP
# ==============================================================================

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
