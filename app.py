import os
from flask import Flask, request, redirect, session, url_for
from requests_oauthlib import OAuth2Session

# --- Configuration ---
# Your specific Discord application credentials have been hardcoded below.
CLIENT_ID = '1384772758046507099'
CLIENT_SECRET = 'T5-jdB_fYB24v8tL7PNgQZ704EKeWeeN'

# This secret key is for Flask's session management. It can be any string.
SECRET_KEY = 'this-is-a-secret-for-testing-only'

# --- OAuth2 Settings ---
API_BASE_URL = 'https://discord.com/api'
AUTHORIZATION_BASE_URL = API_BASE_URL + '/oauth2/authorize'
TOKEN_URL = API_BASE_URL + '/oauth2/token'

# --- Flask App Initialization ---
app = Flask(__name__)
app.secret_key = SECRET_KEY

# --- Helper Functions and HTML Templates ---

def get_user_info(token):
    """Fetches user info from Discord API."""
    discord_session = OAuth2Session(CLIENT_ID, token=token)
    try:
        response = discord_session.get(API_BASE_URL + '/users/@me')
        response.raise_for_status() # Raise an exception for bad status codes
        return response.json()
    except Exception as e:
        print(f"Error fetching user info: {e}")
        return None

def generate_html(title, body_content):
    """A simple HTML template to keep everything in one file."""
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #36393f; color: #dcddde; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
            .container {{ background-color: #2f3136; padding: 2rem; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.2); text-align: center; }}
            h1 {{ color: #ffffff; }}
            a {{ color: #7289da; text-decoration: none; font-weight: bold; padding: 10px 20px; border: 1px solid #7289da; border-radius: 5px; transition: background-color 0.2s, color 0.2s; }}
            a:hover {{ background-color: #7289da; color: #ffffff; }}
            p {{ line-height: 1.6; }}
            ul {{ list-style-type: none; padding: 0; }}
            li {{ background-color: #36393f; margin: 5px 0; padding: 10px; border-radius: 4px; }}
            img {{ border-radius: 50%; width: 100px; height: 100px; }}
        </style>
    </head>
    <body>
        <div class="container">
            {body_content}
        </div>
    </body>
    </html>
    """

# --- App Routes ---

@app.route("/")
def index():
    """Home page."""
    if 'discord_token' in session:
        user = get_user_info(session['discord_token'])
        if user:
            username = user.get('username')
            content = f"""
                <h1>Welcome, {username}!</h1>
                <p>You are successfully logged in with Discord.</p>
                <a href="{url_for('profile')}">View Profile</a>
                <br><br>
                <a href="{url_for('logout')}">Logout</a>
            """
            return generate_html("Home", content)

    # If not logged in or token failed, show the login page
    session.clear() # Clear any invalid session data
    content = """
        <h1>Discord Login Test</h1>
        <p>This is a simple website to test Discord OAuth2 login.</p>
        <a href="/login">Login with Discord</a>
    """
    return generate_html("Login", content)

@app.route("/login")
def login():
    """Redirects user to Discord for authorization."""
    # The redirect_uri must match EXACTLY what you've set in the Discord Dev Portal
    redirect_uri = url_for('callback', _external=True)
    discord = OAuth2Session(CLIENT_ID, redirect_uri=redirect_uri, scope=['identify', 'email'])
    authorization_url, state = discord.authorization_url(AUTHORIZATION_BASE_URL)
    session['oauth2_state'] = state
    return redirect(authorization_url)

@app.route("/callback")
def callback():
    """Handles the callback from Discord after authorization."""
    if request.values.get('error'):
        return request.values['error']
    
    # The redirect_uri must match the one used in the /login route
    redirect_uri = url_for('callback', _external=True)
    discord = OAuth2Session(CLIENT_ID, state=session.get('oauth2_state'), redirect_uri=redirect_uri)
    
    try:
        token = discord.fetch_token(
            TOKEN_URL,
            client_secret=CLIENT_SECRET,
            authorization_response=request.url
        )
        session['discord_token'] = token
    except Exception as e:
        print(f"Error fetching token: {e}")
        return redirect(url_for('index')) # Redirect home on error

    return redirect(url_for('profile'))

@app.route("/profile")
def profile():
    """Displays the user's profile information."""
    if 'discord_token' not in session:
        return redirect(url_for('index'))
    
    user_info = get_user_info(session['discord_token'])
    if not user_info:
        # Token might be expired or invalid, so clear session and send to login
        session.clear()
        return redirect(url_for('index'))

    content = f"""
        <h1>User Profile</h1>
        <img src="https://cdn.discordapp.com/avatars/{user_info['id']}/{user_info['avatar']}.png" alt="Avatar">
        <ul>
            <li><strong>ID:</strong> {user_info.get('id')}</li>
            <li><strong>Username:</strong> {user_info.get('username')}#{user_info.get('discriminator')}</li>
            <li><strong>Email:</strong> {user_info.get('email')}</li>
        </ul>
        <a href="{url_for('index')}">Home</a>
    """
    return generate_html("Profile", content)

@app.route("/logout")
def logout():
    """Logs the user out by clearing the session."""
    session.clear()
    return redirect(url_for('index'))

# This block allows you to run the app directly for local testing.
# Render.com will use Gunicorn and will not execute this part.
if __name__ == "__main__":
    # This line allows OAuth to work over HTTP for local testing.
    # It should not be used in a production environment with HTTPS.
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.run(host='127.0.0.1', port=5000, debug=True)
