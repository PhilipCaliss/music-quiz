# %%
import requests
from urllib.parse import urlencode, urlparse, parse_qs
import pandas as pd
import os
 
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
 
# %%
def get_auth_url():
    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'scope': 'user-read-private user-read-email user-top-read',
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
 
def get_user_top_tracks(access_token):
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    url = 'https://api.spotify.com/v1/me/top/tracks?limit=10'
    response = requests.get(url, headers=headers)
 
    if response.status_code != 200:
        print("Failed to fetch top tracks.")
        print("Status Code:", response.status_code)
        print("Response:", response.text)
        return None
 
    return response.json()
 
try:
    top_tracks = get_user_top_tracks(access_token)
    if top_tracks:
        for i, track in enumerate(top_tracks['items'], start=1):
            print(f"{i}. {track['name']} by {', '.join(artist['name'] for artist in track['artists'])}")
except KeyError:
    print("Error in processing top tracks data. Please check the access token and try again.")
 
 
 
def tracks_to_dataframe(tracks):
    track_data = []
 
    for track in tracks['items']:
        track_info = {
            'Spotify ID': track['id'], 
            'Name': track['name'],
            'Artists': ', '.join(artist['name'] for artist in track['artists']),
            'Album': track['album']['name'],
            'Release Date': track['album']['release_date'],
            'Duration (s)': track['duration_ms'] // 1000,
            'Popularity': track['popularity'],
            'Explicit': track['explicit'],
            'Spotify URL': track['external_urls']['spotify'],
            'Preview URL': track['preview_url'] or 'N/A'
        }
        track_data.append(track_info)
 
    
    return pd.DataFrame(track_data)
 
top_tracks_df = tracks_to_dataframe(top_tracks)
 
# %%
 
def get_audio_features_for_tracks(track_ids, access_token):
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    url = f'https://api.spotify.com/v1/audio-features?ids={",".join(track_ids)}'
    response = requests.get(url, headers=headers)
   
    if response.status_code == 200:
        return response.json().get('audio_features', [])
    else:
        print(f"Failed to fetch audio features, status code: {response.status_code}")
        print("Response:", response.text)
        return []
 
track_ids = [track['id'] for track in top_tracks['items']]
 
audio_features = get_audio_features_for_tracks(track_ids, access_token)
 
for feature in audio_features:
    for key, value in feature.items():
        if key not in top_tracks_df.columns:
            top_tracks_df[key] = pd.NA
        top_tracks_df.loc[top_tracks_df['Spotify ID'] == feature['id'], key] = value
       
def get_user_profile(access_token):
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    url = 'https://api.spotify.com/v1/me'
    response = requests.get(url, headers=headers)
    user_info = response.json()
    return user_info.get('display_name')

user_name = get_user_profile(access_token)

if user_name:
    top_tracks_df['User Name'] = user_name
else:
    print("Failed to fetch user's name")
 
print(top_tracks_df)
 
csv_file_path = 'top_tracks.csv'
file_exists = os.path.isfile(csv_file_path)
 
#Sparar top_tracks.csv
top_tracks_df.to_csv(csv_file_path, mode='a', header=not file_exists, index=False)
 
# %%
 
#Skicka låtarna till chatgpt
openai_url = "https://api.openai.com/v1/chat/completions"
open_ai_key = get_secrets("open ai key")

headers = {
    "Authorization": f"Bearer {open_ai_key}",
    "Content-Type": "application/json",
}

top_tracks_list = "\n".join(f"{track['Name']} by {track['Artists']}" for index, track in top_tracks_df.iterrows())
print(top_tracks_list)

#Meddelande som skickas till chatGPT
prompt_content = f"Summarize this person based on their top tracks:\n{top_tracks_list}"

#Ändra role system för att påverka hur chatGPT svarar.
data = {
    "model": "gpt-3.5-turbo",
    "messages": [
        {"role": "system", "content": "You are part of a music quiz, your job is to summarize their taste of music and give clues to participants so that they can guess who the user behind the tracks are."},
        {"role": "user", "content": prompt_content}
    ]
}

#OBS nedan kostar pengar
response = requests.post(openai_url, headers=headers, json=data)

#Skapar chatgpt_responses.csv från chatgpt
if response.status_code == 200:
    summary_text = response.json()['choices'][0]['message']['content'].strip()
    print(summary_text)

    response_df = pd.DataFrame({
        'User Name': [user_name],
        'ChatGPT Response': [summary_text]
    })
    
    responses_csv_file_path = 'chatgpt_responses.csv'
    responses_file_exists = os.path.isfile(responses_csv_file_path)
    response_df.to_csv(responses_csv_file_path, mode='a', header=not responses_file_exists, index=False)
else:
    print("Failed to generate summary:", response.text)
# %%
