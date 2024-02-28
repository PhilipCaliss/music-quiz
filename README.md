# music-quiz
Några enkla script för att skapa ett musik quiz med hjälp av Spotify och chatGPT.

# Requirements
- App registrerad i Spotify Developer Dashboard: https://developer.spotify.com/dashboard
- En Open AI API nyckel, samt krediter laddade.
- En spotify prenumeration. Alla deltagare behöver en prenumeration också.

# How to run
installera de nödvändiga paketen: pip install requirements.txt
Ersätt värden i secrets.txt för CLIENT_ID, CLIENT_SECRET och open ai nyckel. CLIENT_ID och CLIENT_SECRET får man från app registreringen i Spotify dev dashboard.
Då det är en utvecklingsapp och icke publicerad så behöver alla deltagare reggas inne i spotify dev dashboarden.

Kör main.py, kopiera URL:n till en webbläsare och be deltagarna (en i taget) logga in och godkänna applikationen. Du kommer senare få ett felmeddelande men kopiera då bara URL:n och pastea in den i terminalen som väntar på svar.
Upprepa detta för alla deltagare.

Nu borde du ha en chatgpt_responses.csv och top_tracks.csv.
Kör sedan run.py för att skapa en spotify spellista som innehåller alla låtar från top_tracks.csv

