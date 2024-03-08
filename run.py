import pandas as pd
from urllib.parse import urlencode, urlparse, parse_qs
import requests

def get_secrets(keyname, filename="secrets.txt"):
    #Tillåtna keynames är "open ai key", "CLIENT_ID", "CLIENT_SECRET"
    with open(filename, "r") as file:
        for line in file:
            if line.startswith(keyname):
                _, key = line.strip().split(" = ")
                return key
    return None
        

#Credentials - Måste ha reggat en app i developer dashboard hos spotify.
CLIENT_ID = str(get_secrets("CLIENT_ID"))
CLIENT_SECRET = str(get_secrets("CLIENT_SECRET"))
REDIRECT_URI = 'http://localhost:8000/callback/'
AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'

def get_auth_url():
    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'scope': 'user-read-private user-read-email user-top-read playlist-modify-private playlist-modify-public',
    }
    url = f"{AUTH_URL}?{urlencode(params)}"
    return url

auth_url = get_auth_url()
print("Please open the following URL in an incognito window of your browser and authorize the application:")
print(auth_url)

redirected_url = input("Paste the URL you were redirected to: ")
parsed_url = urlparse(redirected_url)
code = parse_qs(parsed_url.query)['code'][0]

def get_access_token(code):
    payload = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }
    response = requests.post(TOKEN_URL, data=payload)
    return response.json()

token_info = get_access_token(code)
access_token = token_info['access_token']

# Load the track data from the CSV file
csv_file_path = 'top_tracks.csv'
tracks_df = pd.read_csv(csv_file_path)

# Display the DataFrame to ensure it's loaded correctly
print(tracks_df.head())

def create_playlist(access_token, user_id, playlist_name):
    url = f'https://api.spotify.com/v1/users/{user_id}/playlists'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    payload = {
        'name': playlist_name,
        'description': 'Playlist created from CSV file',
        'public': False  # Or True if you want it public
    }
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 201:  # 201 Created
        return response.json()
    else:
        print(f"Failed to create playlist, status code: {response.status_code}")
        print("Response:", response.text)
        return None

def add_tracks_to_playlist(access_token, playlist_id, track_uris):
    url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    # Split track_uris into batches of 100
    batches = [track_uris[i:i + 100] for i in range(0, len(track_uris), 100)]

    for batch in batches:
        payload = {
            'uris': batch
        }
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code in [200, 201]:  # Success
            print(f"Tracks successfully added to playlist {playlist_id}")
        else:
            print(f"Failed to add tracks to playlist, status code: {response.status_code}")
            print("Response:", response.text)
            # If any batch fails, stop the function and return None
            return None

    # If all batches are added successfully
    return {"message": "All tracks added successfully"}


def get_spotify_user_id(access_token):
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get('https://api.spotify.com/v1/me', headers=headers)
    if response.status_code == 200:
        user_info = response.json()
        return user_info['id']
    else:
        print(f"Failed to fetch user ID, status code: {response.status_code}")
        return None

user_id = get_spotify_user_id(access_token)
if user_id:
    print(f"Your Spotify user ID is: {user_id}")

playlist_name = 'Music Quiz test playlist'
playlist = create_playlist(access_token, user_id, playlist_name)
if playlist and 'id' in playlist:
    playlist_id = playlist['id']

    # Assuming 'Spotify URL' contains the full track URLs, extract track IDs and convert to URIs
    track_uris = ['spotify:track:' + url.split('/')[-1] for url in tracks_df['Spotify URL'] if pd.notnull(url) and url.startswith('https://')]

    # Add tracks to the playlist
    add_tracks_response = add_tracks_to_playlist(access_token, playlist_id, track_uris)

    if add_tracks_response:
        print(f"Playlist '{playlist_name}' created and tracks added.")
    else:
        print("Failed to add tracks to the playlist.")
else:
    print("Failed to create the playlist.")
