import requests
from flask import Flask, request, redirect
import base64
import urllib.parse

# Fill these in from your Spotify Developer app
CLIENT_ID = "2d5d8cc0d20d4f5381a5398bef6b6ddc"
CLIENT_SECRET = "af8d16027c3e49d3a4adc879a6cde04f"
REDIRECT_URI = "http://127.0.0.1:8080/callback"

# Scopes needed for playback control
SCOPES = "user-read-playback-state user-modify-playback-state user-read-currently-playing"

app = Flask(__name__)

@app.route("/")
def login():
    # Use URL encoding for the redirect URI to ensure proper formatting
    encoded_redirect = urllib.parse.quote(REDIRECT_URI, safe="")
    encoded_scopes = urllib.parse.quote(SCOPES, safe="")
    
    auth_url = (
        "https://accounts.spotify.com/authorize"
        f"?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&scope={encoded_scopes}"
        f"&redirect_uri={encoded_redirect}"
    )
    print(f"Redirecting to: {auth_url}")  # Debug info
    return redirect(auth_url)

@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return "Error: Authorization code missing. Please go through the login flow by visiting the root URL.", 400
    
    token_url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode(),
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }
    
    print(f"Sending token request with redirect_uri: {REDIRECT_URI}")  # Debug info
    
    r = requests.post(token_url, headers=headers, data=data)
    if r.status_code == 200:
        tokens = r.json()
        return (
            f"Access Token: {tokens['access_token']}<br><br>"
            f"Refresh Token: {tokens['refresh_token']}<br><br>"
            f"Save the refresh token in your Pico code!"
        )
    else:
        return f"Error: {r.text}", 400

if __name__ == "__main__":
    print(f"Starting server with redirect URI: {REDIRECT_URI}")
    print("Open http://127.0.0.1:8080/ in your browser to begin the OAuth flow")
    app.run(host="127.0.0.1", port=8080, debug=True)
