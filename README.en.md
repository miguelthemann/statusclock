[PT](README.md) | [EN](README.en.md) | [IT](README.it.md)

# Status Clock

Fullscreen Python dashboard that shows:

- central clock with seconds
- current date
- weather for your location
- current Spotify song
- today's Google Calendar events

It is intended to run 24/7 on a dedicated display.

## Compatibility Status

- Windows: supported and tested
- Linux: supposedly supported, but not guaranteed and not fully tested
- macOS: not tested and not guaranteed

This project was designed with priority for:

- Windows
- Linux Fedora
- Linux Debian/Ubuntu
- Linux Arch

## Requirements

- Python 3.11 or newer
- internet access
- Spotify account
- Google account with Google Calendar

## Project Structure

- `src/statusclock/main.py`: main entry point
- `src/statusclock/dashboard.py`: PySide6 interface
- `src/statusclock/config.py`: configuration and environment variables
- `.env.example`: example configuration
- `start_statusclock.bat`: quick Windows launcher
- `setup_statusclock.bat`: quick Windows setup
- `start_statusclock.sh`: quick Linux launcher
- `setup_statusclock.sh`: quick Linux setup

## Installation on Windows

### Recommended method

In the project folder:

```powershell
.\setup_statusclock.bat
```

Then:

```powershell
.\start_statusclock.bat
```

### Manual method

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m src.statusclock
```

## Installation on Linux

### Recommended method

In the project folder:

```bash
chmod +x setup_statusclock.sh start_statusclock.sh
./setup_statusclock.sh
./start_statusclock.sh
```

### Manual method

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
./.venv/bin/python -m src.statusclock
```

## Configuration

Environment variables live in the `.env` file at the project root.

You can start by copying the example:

Windows:

```powershell
Copy-Item .env.example .env
```

Linux:

```bash
cp .env.example .env
```

### Example `.env`

```env
APP_LANGUAGE=en

WEATHER_LOCATION=London

SPOTIFY_CLIENT_ID=put_your_client_id_here
SPOTIFY_CLIENT_SECRET=put_your_client_secret_here
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback

GOOGLE_CALENDAR_ID=primary
```

### Supported languages

- `pt`: Portuguese
- `en`: English
- `it`: Italian

Set the UI language with:

```env
APP_LANGUAGE=en
```

## Weather Setup

The project uses Open-Meteo:

- geocoding: [Open-Meteo Geocoding API](https://open-meteo.com/en/docs/geocoding-api)
- forecast/current conditions: [Open-Meteo Forecast API](https://open-meteo.com/en/docs)

You can configure weather by name:

```env
WEATHER_LOCATION=London
```

Or by coordinates:

```env
WEATHER_LAT=51.5072
WEATHER_LON=-0.1276
```

If coordinates are set, they take priority.

## Spotify Setup

Official links:

- [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
- [Spotify Redirect URIs](https://developer.spotify.com/documentation/web-api/concepts/redirect_uri)
- [Spotify Web API Concepts](https://developer.spotify.com/documentation/web-api/concepts/api-calls)

### Steps

1. Open the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
2. Sign in.
3. Create an app.
4. Copy:
   - `Client ID`
   - `Client Secret`
5. In `Edit settings`, add this redirect URI:

```text
http://127.0.0.1:8888/callback
```

6. Save the changes.

### `.env`

```env
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback
```

### Notes

- The redirect URI must match exactly in both `.env` and the Spotify dashboard.
- On first run, the app should open the browser for authorization.
- The Spotify token is stored in `.cache/spotify_token.json`.

## Google Calendar Setup

Official links:

- [Google Calendar API Python Quickstart](https://developers.google.com/workspace/calendar/api/quickstart/python)
- [Configure OAuth Consent](https://developers.google.com/workspace/guides/configure-oauth-consent)
- [Google Cloud Console](https://console.cloud.google.com/)
- [Google Calendar API](https://console.cloud.google.com/apis/library/calendar-json.googleapis.com)

### Steps

1. Open the [Google Cloud Console](https://console.cloud.google.com/).
2. Create or select a project.
3. Enable the [Google Calendar API](https://console.cloud.google.com/apis/library/calendar-json.googleapis.com).
4. Configure the OAuth consent screen.
5. Create credentials:
   - `OAuth client ID`
   - `Desktop app`
6. Download the JSON file.
7. Save it as `credentials.json` in the project root.

### `.env`

For the main calendar:

```env
GOOGLE_CALENDAR_ID=primary
```

### Notes

- On first run, the app opens the browser for Google login.
- After authorization, `token.json` is created in the project root.
- If the Google app is still in testing mode, add your account under `Test users`.

## How to Start the App

### Windows

```powershell
.\start_statusclock.bat
```

or

```powershell
python -m src.statusclock
```

or

```powershell
.venv\Scripts\python.exe src\statusclock\main.py
```

### Linux

```bash
./start_statusclock.sh
```

or

```bash
python3 -m src.statusclock
```

or

```bash
./.venv/bin/python src/statusclock/main.py
```

## First Run

On first launch, the expected behavior is:

- the window opens in fullscreen
- the clock appears immediately
- the browser may open for Spotify authentication
- the browser may open for Google authentication
- `token.json` is created
- `.cache/spotify_token.json` is created

## Shortcuts

- `Esc`: closes the app
- `F11`: toggles fullscreen

## Automatically Created Files

- `.env`
- `token.json`
- `.cache/spotify_token.json`

## Troubleshooting

### `ModuleNotFoundError: No module named 'dotenv'`

You are using a different Python interpreter from the one where the dependencies were installed.

Windows:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Linux:

```bash
./.venv/bin/python -m pip install -r requirements.txt
```

### `ImportError: attempted relative import with no known parent package`

Use one of these launch methods:

Windows:

```powershell
.\start_statusclock.bat
```

Linux:

```bash
./start_statusclock.sh
```

Or run it as a module:

```bash
python3 -m src.statusclock
```

### Spotify does not show the song

Check:

- `SPOTIFY_CLIENT_ID` is set
- `SPOTIFY_CLIENT_SECRET` is set
- `SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback`
- the same redirect URI exists in the Spotify dashboard
- Spotify is open and there is active or recent playback

### Google Calendar does not show events

Check:

- `credentials.json` exists in the project root
- Google Calendar API is enabled in the correct project
- you authorized the account in the browser
- `GOOGLE_CALENDAR_ID=primary` or another valid calendar ID
- your account is listed under `Test users` if the app is still in testing

### Reinstall dependencies

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

## Final Notes

- The project has been tested on Windows.
- Linux may work, but has not been fully validated.
- macOS is not a primary target for this project and compatibility is not guaranteed.
