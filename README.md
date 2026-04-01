# Status Clock

Painel fullscreen em Python para mostrar:

- relógio central com segundos
- data atual
- temperatura da localização
- música atual do Spotify
- eventos do dia do Google Calendar

Foi pensado para correr 24/7 num ecrã dedicado.

## Estado de compatibilidade

- Windows: suportado e testado
- Linux: supostamente suportado, mas não garantido nem testado de forma completa
- macOS: não testado nem garantido

Este projeto foi pensado com prioridade para:

- Windows
- Linux Fedora
- Linux Debian/Ubuntu
- Linux Arch

## Requisitos

- Python 3.11 ou superior
- ligação à internet
- conta Spotify
- conta Google com Google Calendar

## Estrutura do projeto

- `src/statusclock/main.py`: ponto de entrada principal
- `src/statusclock/dashboard.py`: interface PySide6
- `src/statusclock/config.py`: configuração e variáveis de ambiente
- `.env.example`: exemplo de configuração
- `start_statusclock.bat`: arranque rápido no Windows
- `setup_statusclock.bat`: setup rápido no Windows
- `start_statusclock.sh`: arranque rápido no Linux
- `setup_statusclock.sh`: setup rápido no Linux

## Instalação no Windows

### Método recomendado

Na pasta do projeto:

```powershell
.\setup_statusclock.bat
```

Depois:

```powershell
.\start_statusclock.bat
```

### Método manual

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m src.statusclock
```

## Instalação no Linux

### Método recomendado

Na pasta do projeto:

```bash
chmod +x setup_statusclock.sh start_statusclock.sh
./setup_statusclock.sh
./start_statusclock.sh
```

### Método manual

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
./.venv/bin/python -m src.statusclock
```

## Configuração

As variáveis ficam no ficheiro `.env` na raiz do projeto.

Podes começar por copiar o exemplo:

Windows:

```powershell
Copy-Item .env.example .env
```

Linux:

```bash
cp .env.example .env
```

### Exemplo de `.env`

```env
WEATHER_LOCATION=Lisbon

SPOTIPY_CLIENT_ID=coloca_aqui_o_client_id
SPOTIPY_CLIENT_SECRET=coloca_aqui_o_client_secret
SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback

GOOGLE_CALENDAR_ID=primary
```

## Configurar a meteorologia

O projeto usa Open-Meteo:

- geocoding: [Open-Meteo Geocoding API](https://open-meteo.com/en/docs/geocoding-api)
- previsão/estado atual: [Open-Meteo Forecast API](https://open-meteo.com/en/docs)

Podes configurar por nome:

```env
WEATHER_LOCATION=Lisbon
```

Ou por coordenadas:

```env
WEATHER_LAT=38.7223
WEATHER_LON=-9.1393
```

Se definires coordenadas, elas têm prioridade.

## Configurar o Spotify

Links oficiais:

- [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
- [Spotify Redirect URIs](https://developer.spotify.com/documentation/web-api/concepts/redirect_uri)
- [Spotify Web API Concepts](https://developer.spotify.com/documentation/web-api/concepts/api-calls)

### Passos

1. Abre o [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
2. Faz login.
3. Cria uma app.
4. Copia:
   - `Client ID`
   - `Client Secret`
5. Em `Edit settings`, adiciona este redirect URI:

```text
http://127.0.0.1:8888/callback
```

6. Guarda as alterações.

### `.env`

```env
SPOTIPY_CLIENT_ID=o_teu_client_id
SPOTIPY_CLIENT_SECRET=o_teu_client_secret
SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback
```

### Notas

- O redirect URI tem de ser exatamente igual no `.env` e no dashboard do Spotify.
- Na primeira execução, a app deve abrir o browser para autorização.
- O token do Spotify fica guardado em `.cache/spotify_token.json`.

## Configurar o Google Calendar

Links oficiais:

- [Google Calendar API Python Quickstart](https://developers.google.com/workspace/calendar/api/quickstart/python)
- [Configure OAuth Consent](https://developers.google.com/workspace/guides/configure-oauth-consent)
- [Google Cloud Console](https://console.cloud.google.com/)
- [Google Calendar API](https://console.cloud.google.com/apis/library/calendar-json.googleapis.com)

### Passos

1. Abre a [Google Cloud Console](https://console.cloud.google.com/).
2. Cria ou escolhe um projeto.
3. Ativa a [Google Calendar API](https://console.cloud.google.com/apis/library/calendar-json.googleapis.com).
4. Configura o OAuth consent screen.
5. Cria credenciais:
   - `OAuth client ID`
   - `Desktop app`
6. Faz download do JSON.
7. Guarda o ficheiro como `credentials.json` na raiz do projeto.

### `.env`

Para o calendário principal:

```env
GOOGLE_CALENDAR_ID=primary
```

### Notas

- Na primeira execução, a app abre o browser para login Google.
- Depois da autorização, é criado `token.json` na raiz do projeto.
- Se a app Google estiver em modo de teste, adiciona a tua conta em `Test users`.

## Como arrancar a aplicação

### Windows

```powershell
.\start_statusclock.bat
```

ou

```powershell
python -m src.statusclock
```

ou

```powershell
.venv\Scripts\python.exe src\statusclock\main.py
```

### Linux

```bash
./start_statusclock.sh
```

ou

```bash
python3 -m src.statusclock
```

ou

```bash
./.venv/bin/python src/statusclock/main.py
```

## Primeira execução

No primeiro arranque, o comportamento esperado é:

- a janela abre em fullscreen
- o relógio aparece logo
- o browser pode abrir para autenticação Spotify
- o browser pode abrir para autenticação Google
- é criado `token.json`
- é criado `.cache/spotify_token.json`

## Atalhos

- `Esc`: fecha a app
- `F11`: alterna fullscreen

## Ficheiros criados automaticamente

- `.env`
- `token.json`
- `.cache/spotify_token.json`

## Resolução de problemas

### `ModuleNotFoundError: No module named 'dotenv'`

Estás a usar um Python diferente daquele onde instalaste as dependências.

Windows:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Linux:

```bash
./.venv/bin/python -m pip install -r requirements.txt
```

### `ImportError: attempted relative import with no known parent package`

Usa um destes arranques:

Windows:

```powershell
.\start_statusclock.bat
```

Linux:

```bash
./start_statusclock.sh
```

ou então arranca como módulo:

```bash
python3 -m src.statusclock
```

### O Spotify não mostra a música

Confirma:

- `SPOTIPY_CLIENT_ID` preenchido
- `SPOTIPY_CLIENT_SECRET` preenchido
- `SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback`
- o mesmo redirect URI existe no dashboard do Spotify
- tens o Spotify aberto e uma música em reprodução ou recentemente ativa

### O Google Calendar não mostra eventos

Confirma:

- `credentials.json` existe na raiz do projeto
- a Google Calendar API está ativa no projeto certo
- autorizaste a conta no browser
- `GOOGLE_CALENDAR_ID=primary` ou outro ID válido
- a tua conta está em `Test users`, se a app estiver em teste

### Quero reinstalar dependências

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

## Notas finais

- O projeto foi testado em Windows.
- Linux deve funcionar, mas não foi validado de ponta a ponta.
- macOS não é alvo principal deste projeto e não há garantia de compatibilidade.
