[PT](README.md) | [EN](README.en.md) | [IT](README.it.md)

# Status Clock

Fullscreen Python dashboard built to run 24/7 and show:

- central clock with seconds
- current date
- weather for your location
- current Spotify song
- today's Google Calendar agenda

It can run in graphical mode (`gui`) or terminal mode (`cli`), and the Spotify and Google Calendar modules can be enabled or disabled in `.env`.

## Compatibility Status

- Windows: supported and tested
- Linux: supposedly supported, but not guaranteed and not fully validated
- macOS: not tested and not guaranteed

Compatibility priority:

- Windows
- Linux Fedora
- Linux Debian/Ubuntu
- Linux Arch

## Requirements

- Python 3.11 or newer
- internet access
- Spotify account if you want the Spotify module
- Google account with Google Calendar if you want the Calendar module

## Project Structure

- `src/statusclock/main.py`: main entry point
- `src/statusclock/dashboard.py`: PySide6 interface
- `src/statusclock/cli.py`: terminal interface
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
APP_MODE=gui
APP_LANGUAGE=en
ENABLE_WEATHER=true
ENABLE_SPOTIFY=true
ENABLE_GOOGLE_CALENDAR=true

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

Example:

```env
APP_LANGUAGE=en
```

### Supported modes

- `gui`: PySide6 graphical interface
- `cli`: terminal interface

Example:

```env
APP_MODE=gui
```

### Optional modules

- `ENABLE_WEATHER=true|false`
- `ENABLE_SPOTIFY=true|false`
- `ENABLE_GOOGLE_CALENDAR=true|false`

When a module is set to `false`, it disappears from both the GUI and CLI dashboards.

Examples:

```env
ENABLE_WEATHER=false
ENABLE_SPOTIFY=true
ENABLE_GOOGLE_CALENDAR=true
```

```env
ENABLE_SPOTIFY=false
ENABLE_GOOGLE_CALENDAR=true
```

```env
ENABLE_SPOTIFY=false
ENABLE_GOOGLE_CALENDAR=false
```

## Weather Setup

The project uses Open-Meteo:

- geocoding: [Open-Meteo Geocoding API](https://open-meteo.com/en/docs/geocoding-api)
- forecast and current conditions: [Open-Meteo Forecast API](https://open-meteo.com/en/docs)
- service status: [Open-Meteo Status](https://status.open-meteo.com/)

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

When Open-Meteo returns temporary errors such as `502 Bad Gateway`, the app shows a translated friendly message instead of the raw URL error.

If you do not want to use weather, set:

```env
ENABLE_WEATHER=false
```

## Spotify Setup

If you do not want to use Spotify, set:

```env
ENABLE_SPOTIFY=false
```

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
ENABLE_SPOTIFY=true
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback
```

### Notes

- The redirect URI must match exactly in both `.env` and the Spotify dashboard.
- On first run, the app may open the browser for authorization.
- The Spotify token is stored in `.cache/spotify_token.json`.

## Google Calendar Setup

If you do not want to use Google Calendar, set:

```env
ENABLE_GOOGLE_CALENDAR=false
```

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

```env
ENABLE_GOOGLE_CALENDAR=true
GOOGLE_CALENDAR_ID=primary
```

### Notes

- On first run, the app may open the browser for Google login.
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

- the window opens in fullscreen in `gui` mode
- the clock appears immediately
- in `cli` mode, the dashboard appears directly in the terminal
- the browser may open for Spotify authentication if the module is enabled
- the browser may open for Google authentication if the module is enabled
- `token.json` is created if the Calendar module is enabled
- `.cache/spotify_token.json` is created if the Spotify module is enabled

## Shortcuts

- `Esc`: closes the app in graphical mode
- `F11`: toggles fullscreen in graphical mode
- `Ctrl+C`: closes the app in CLI mode

## Automatically Created Files

- `.env`
- `token.json`
- `.cache/spotify_token.json`

The last two only appear if their respective modules are enabled.

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

- `ENABLE_SPOTIFY=true`
- `SPOTIFY_CLIENT_ID` is set
- `SPOTIFY_CLIENT_SECRET` is set
- `SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback`
- the same redirect URI exists in the Spotify dashboard
- Spotify is open and there is active or recent playback

### Google Calendar does not show events

Check:

- `ENABLE_GOOGLE_CALENDAR=true`
- `credentials.json` exists in the project root
- Google Calendar API is enabled in the correct project
- you authorized the account in the browser
- `GOOGLE_CALENDAR_ID=primary` or another valid calendar ID
- your account is listed under `Test users` if the app is still in testing

### Weather appears as unavailable

This can happen if Open-Meteo is temporarily degraded, for example with `502 Bad Gateway`.

Check:

- `ENABLE_WEATHER=true`
- [Open-Meteo Status](https://status.open-meteo.com/)
- your internet connection
- whether the location or coordinates are valid

## Final Notes

- The project has been tested on Windows.
- Linux may work, but has not been fully validated.
- macOS is not a primary target for this project and compatibility is not guaranteed.
