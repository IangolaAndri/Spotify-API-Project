import json
import requests
from flask import Flask, redirect, render_template, request, jsonify, session, url_for
import urllib.parse
from datetime import datetime, timedelta
from flask_cors import CORS 

app = Flask(__name__)

app.secret_key ='12435323466_Sdgfsf@5_'

CLIENT_ID = '1ddccac063164e1e9d28144abfc6a79f'
CLIENT_SECRET = '895d1a98344d4999ad4d59e76d804520'
REDIRECT_URI = 'https://spotify-api-project-3.onrender.com/callback'

AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE_URL = 'https://api.spotify.com/v1/'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    scope = 'user-read-private user-read-email user-top-read'

    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'scope': scope,
        'redirect_uri': REDIRECT_URI,
        'show_dialog': True
    }

    #making request to authorization spotify 
    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    return redirect(auth_url)

@app.route('/logout')
def logout():
    session.pop('access_token', None)
    session.pop('refresh_token', None)
    session.pop('expires_at', None)
   
    return redirect('/')

@app.route('/callback')
def callback():
    if 'error' in request.args:
        return jsonify({"error": request.args['erro']})
    
    #requesting access token
    if 'code' in request.args:
        req_body = {
            'code': request.args['code'],
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        response = requests.post(TOKEN_URL, data=req_body)
        token_info = response.json()
        

        session['access_token'] = token_info['access_token']
        session['refresh_token'] = token_info['refresh_token']
        session['expires_at'] = datetime.now().timestamp() + token_info['expires_in']

        return redirect("/topTracks")

@app.route('/get-session-data')
def get_session_data():
    if 'access_token' not in session:
        return redirect("/login")
    
    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh-token')
    
    return jsonify(session)

@app.route('/playlists')
def get_playlists():
    if 'access_token' not in session:
        return redirect(url_for('login'))
    
    if datetime.now().timestamp() > session['expires_at']:
       return redirect(url_for('refresh_token'))

    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    response = requests.get(API_BASE_URL + 'me/playlists', headers=headers)
    playlists = response.json()
    playlists_data = {}
    save_to_json(playlists['items'], 'playlists_data.json')


    return render_template('playlists.html', playlists=playlists['items'])

def get_top_tracks(time_range):
    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    response = requests.get(API_BASE_URL + f'me/top/tracks?time_range={time_range}&limit=50&offset=0', headers=headers)
    top_tracks = response.json()
    return top_tracks['items']

@app.route('/topTracks')
def get_topTracks():
    if 'access_token' not in session:
       return redirect(url_for('login'))
    if datetime.now().timestamp() > session['expires_at']:
        return redirect(url_for('refresh_token'))

    top_tracks_data = {}

    time_ranges = ['short_term', 'medium_term', 'long_term']

    for time_range in time_ranges:
        top_tracks_data[time_range] = get_top_tracks(time_range)
        save_to_json(top_tracks_data, 'top_tracks_data.json')

    return render_template('topTracks.html', top_tracks=top_tracks_data)

def get_top_artists(time_range):
    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    response = requests.get(API_BASE_URL + f'me/top/artists?time_range={time_range}&limit=50&offset=0', headers=headers)
    top_artists = response.json()
    return top_artists['items']

def save_to_json(data, filename):
    with open(filename, 'w') as json_file:
        json.dump(data, json_file, indent=2)

@app.route('/topArtists')
def get_topArtists():
    if 'access_token' not in session:
        return redirect(url_for('login'))
    
    if datetime.now().timestamp() > session['expires_at']:
        return redirect(url_for('refresh_token'))
    
    top_artists_data = {}

    time_ranges = ['short_term', 'medium_term', 'long_term']

    for time_range in time_ranges:
        top_artists_data[time_range] = get_top_artists(time_range)
        save_to_json(top_artists_data, 'top_artists_data.json')

    return render_template('topArtists.html', top_artists=top_artists_data)

@app.route('/refresh_token')
def refresh_token():
    if 'refresh_token' not in session:
        return redirect(url_for('login'))
    
    # Requesting new access token if expiered 
    if datetime.now().timestamp() > session['expires_at']:
        req_body = {
            'grant_type': 'refresh_token',
            'refresh_token': session['refresh_token'],
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        response = requests.post(TOKEN_URL, data=req_body)
        new_token_info = response.json()

        session['access_token'] = new_token_info['access_token']
        session['expires_at'] = datetime.now().timestamp() + new_token_info['expires_in']

        return redirect(url_for('get_topTracks'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=8080)
