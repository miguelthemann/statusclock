[PT](README.md) | [EN](README.en.md) | [IT](README.it.md)

# Status Clock

Dashboard fullscreen in Python che mostra:

- orologio centrale con secondi
- data attuale
- meteo della tua posizione
- brano Spotify attuale
- eventi di oggi da Google Calendar

È pensato per funzionare 24/7 su uno schermo dedicato.

## Stato di Compatibilità

- Windows: supportato e testato
- Linux: teoricamente supportato, ma non garantito e non testato in modo completo
- macOS: non testato e non garantito

Questo progetto è stato pensato con priorità per:

- Windows
- Linux Fedora
- Linux Debian/Ubuntu
- Linux Arch

## Requisiti

- Python 3.11 o superiore
- accesso a internet
- account Spotify
- account Google con Google Calendar

## Struttura del Progetto

- `src/statusclock/main.py`: punto di ingresso principale
- `src/statusclock/dashboard.py`: interfaccia PySide6
- `src/statusclock/config.py`: configurazione e variabili d'ambiente
- `.env.example`: esempio di configurazione
- `start_statusclock.bat`: avvio rapido su Windows
- `setup_statusclock.bat`: setup rapido su Windows
- `start_statusclock.sh`: avvio rapido su Linux
- `setup_statusclock.sh`: setup rapido su Linux

## Installazione su Windows

### Metodo consigliato

Nella cartella del progetto:

```powershell
.\setup_statusclock.bat
```

Poi:

```powershell
.\start_statusclock.bat
```

### Metodo manuale

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m src.statusclock
```

## Installazione su Linux

### Metodo consigliato

Nella cartella del progetto:

```bash
chmod +x setup_statusclock.sh start_statusclock.sh
./setup_statusclock.sh
./start_statusclock.sh
```

### Metodo manuale

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
./.venv/bin/python -m src.statusclock
```

## Configurazione

Le variabili d'ambiente si trovano nel file `.env` nella root del progetto.

Puoi iniziare copiando l'esempio:

Windows:

```powershell
Copy-Item .env.example .env
```

Linux:

```bash
cp .env.example .env
```

### Esempio di `.env`

```env
APP_LANGUAGE=it

WEATHER_LOCATION=Rome

SPOTIFY_CLIENT_ID=inserisci_il_client_id
SPOTIFY_CLIENT_SECRET=inserisci_il_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback

GOOGLE_CALENDAR_ID=primary
```

### Lingue supportate

- `pt`: portoghese
- `en`: inglese
- `it`: italiano

Imposta la lingua dell'interfaccia con:

```env
APP_LANGUAGE=it
```

## Configurare il Meteo

Il progetto usa Open-Meteo:

- geocoding: [Open-Meteo Geocoding API](https://open-meteo.com/en/docs/geocoding-api)
- previsione/condizioni attuali: [Open-Meteo Forecast API](https://open-meteo.com/en/docs)

Puoi configurare il meteo per nome:

```env
WEATHER_LOCATION=Rome
```

Oppure tramite coordinate:

```env
WEATHER_LAT=41.9028
WEATHER_LON=12.4964
```

Se imposti le coordinate, hanno priorità.

## Configurare Spotify

Link ufficiali:

- [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
- [Spotify Redirect URIs](https://developer.spotify.com/documentation/web-api/concepts/redirect_uri)
- [Spotify Web API Concepts](https://developer.spotify.com/documentation/web-api/concepts/api-calls)

### Passi

1. Apri lo [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
2. Accedi.
3. Crea un'app.
4. Copia:
   - `Client ID`
   - `Client Secret`
5. In `Edit settings`, aggiungi questo redirect URI:

```text
http://127.0.0.1:8888/callback
```

6. Salva le modifiche.

### `.env`

```env
SPOTIFY_CLIENT_ID=il_tuo_client_id
SPOTIFY_CLIENT_SECRET=il_tuo_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback
```

### Note

- Il redirect URI deve essere esattamente uguale sia nel `.env` sia nel dashboard Spotify.
- Al primo avvio, l'app dovrebbe aprire il browser per l'autorizzazione.
- Il token Spotify viene salvato in `.cache/spotify_token.json`.

## Configurare Google Calendar

Link ufficiali:

- [Google Calendar API Python Quickstart](https://developers.google.com/workspace/calendar/api/quickstart/python)
- [Configure OAuth Consent](https://developers.google.com/workspace/guides/configure-oauth-consent)
- [Google Cloud Console](https://console.cloud.google.com/)
- [Google Calendar API](https://console.cloud.google.com/apis/library/calendar-json.googleapis.com)

### Passi

1. Apri la [Google Cloud Console](https://console.cloud.google.com/).
2. Crea o seleziona un progetto.
3. Abilita la [Google Calendar API](https://console.cloud.google.com/apis/library/calendar-json.googleapis.com).
4. Configura la schermata di consenso OAuth.
5. Crea le credenziali:
   - `OAuth client ID`
   - `Desktop app`
6. Scarica il file JSON.
7. Salvalo come `credentials.json` nella root del progetto.

### `.env`

Per il calendario principale:

```env
GOOGLE_CALENDAR_ID=primary
```

### Note

- Al primo avvio, l'app apre il browser per il login Google.
- Dopo l'autorizzazione, viene creato `token.json` nella root del progetto.
- Se l'app Google è ancora in modalità test, aggiungi il tuo account in `Test users`.

## Come Avviare l'Applicazione

### Windows

```powershell
.\start_statusclock.bat
```

oppure

```powershell
python -m src.statusclock
```

oppure

```powershell
.venv\Scripts\python.exe src\statusclock\main.py
```

### Linux

```bash
./start_statusclock.sh
```

oppure

```bash
python3 -m src.statusclock
```

oppure

```bash
./.venv/bin/python src/statusclock/main.py
```

## Primo Avvio

Al primo avvio, il comportamento atteso è:

- la finestra si apre in fullscreen
- l'orologio appare subito
- il browser può aprirsi per l'autenticazione Spotify
- il browser può aprirsi per l'autenticazione Google
- viene creato `token.json`
- viene creato `.cache/spotify_token.json`

## Scorciatoie

- `Esc`: chiude l'app
- `F11`: attiva/disattiva il fullscreen

## File Creati Automaticamente

- `.env`
- `token.json`
- `.cache/spotify_token.json`

## Risoluzione dei Problemi

### `ModuleNotFoundError: No module named 'dotenv'`

Stai usando un interprete Python diverso da quello in cui hai installato le dipendenze.

Windows:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Linux:

```bash
./.venv/bin/python -m pip install -r requirements.txt
```

### `ImportError: attempted relative import with no known parent package`

Usa uno di questi metodi di avvio:

Windows:

```powershell
.\start_statusclock.bat
```

Linux:

```bash
./start_statusclock.sh
```

Oppure eseguilo come modulo:

```bash
python3 -m src.statusclock
```

### Spotify non mostra il brano

Controlla:

- `SPOTIFY_CLIENT_ID` impostato
- `SPOTIFY_CLIENT_SECRET` impostato
- `SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback`
- lo stesso redirect URI esiste nel dashboard Spotify
- Spotify è aperto e c'è una riproduzione attiva o recente

### Google Calendar non mostra eventi

Controlla:

- `credentials.json` esiste nella root del progetto
- Google Calendar API è abilitata nel progetto corretto
- hai autorizzato l'account nel browser
- `GOOGLE_CALENDAR_ID=primary` o un altro ID calendario valido
- il tuo account è presente in `Test users` se l'app è ancora in test

### Reinstallare le dipendenze

Windows:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Linux:

```bash
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -r requirements.txt
```

## Note Finali

- Il progetto è stato testato su Windows.
- Linux potrebbe funzionare, ma non è stato validato completamente.
- macOS non è un obiettivo principale di questo progetto e la compatibilità non è garantita.
