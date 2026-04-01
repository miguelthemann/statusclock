# Status Clock

Painel fullscreen em Python para mostrar:

- relógio central com segundos
- data atual
- temperatura da tua localização
- música atual do Spotify
- eventos de hoje do Google Calendar

Foi pensado para correr 24/7 num ecrã dedicado.

## O que este projeto faz

No centro do ecrã mostra:

- horas com segundos
- data atual

Nos cartões laterais mostra:

- tempo atual via Open-Meteo
- música atual do Spotify, incluindo capa do álbum
- agenda do dia via Google Calendar

## Requisitos

- Windows, Linux ou macOS
- Python 3.11 ou superior
- ligação à internet
- conta Spotify
- conta Google com Google Calendar

## Estrutura rápida

- app principal: [`src/statusclock/main.py`](D:/statusclock/src/statusclock/main.py)
- interface: [`src/statusclock/dashboard.py`](D:/statusclock/src/statusclock/dashboard.py)
- configuração: [`src/statusclock/config.py`](D:/statusclock/src/statusclock/config.py)
- exemplo de variáveis de ambiente: [`.env.example`](D:/statusclock/.env.example)
- arranque rápido no Windows: [`start_statusclock.bat`](D:/statusclock/start_statusclock.bat)
- setup automático no Windows: [`setup_statusclock.bat`](D:/statusclock/setup_statusclock.bat)

## Instalação no Windows

### Opção mais simples

Corre:

```powershell
D:\statusclock\setup_statusclock.bat
```

Esse script:

- cria `.venv` se ainda não existir
- instala as dependências de [`requirements.txt`](D:/statusclock/requirements.txt)
- cria `.env` a partir de [`.env.example`](D:/statusclock/.env.example) se ainda não existir

Depois, para abrir a app:

```powershell
D:\statusclock\start_statusclock.bat
```

### Opção manual

```powershell
cd D:\statusclock
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Para arrancar:

```powershell
python -m src.statusclock
```

## Configuração

Há 3 blocos de configuração:

- tempo
- Spotify
- Google Calendar

As variáveis ficam no ficheiro `.env` na raiz do projeto.

Podes começar deste ficheiro:

- [`.env.example`](D:/statusclock/.env.example)

### Exemplo completo de `.env`

```env
WEATHER_LOCATION=Lisbon

SPOTIPY_CLIENT_ID=coloca_aqui_o_client_id
SPOTIPY_CLIENT_SECRET=coloca_aqui_o_client_secret
SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback

GOOGLE_CALENDAR_ID=primary
```

## Configurar a temperatura

O projeto usa:

- geocoding da Open-Meteo: [Open-Meteo Geocoding API](https://open-meteo.com/en/docs/geocoding-api)

Podes configurar a localização de 2 formas.

### Opção 1: por nome da cidade

No `.env`:

```env
WEATHER_LOCATION=Lisbon
```

### Opção 2: por coordenadas

No `.env`:

```env
WEATHER_LAT=38.7223
WEATHER_LON=-9.1393
```

Se definires coordenadas, elas têm prioridade sobre o nome.

## Configurar o Spotify

O projeto usa OAuth com a Spotify Web API para ler a música atual.

Links úteis:

- dashboard: [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
- docs de redirect URI: [Spotify Redirect URIs](https://developer.spotify.com/documentation/web-api/concepts/redirect_uri)
- visão geral da API: [Spotify Web API Concepts](https://developer.spotify.com/documentation/web-api/concepts/api-calls)

### Passos

1. Vai a [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
2. Faz login com a tua conta Spotify.
3. Cria uma app nova.
4. Guarda estes dois valores:
   - `Client ID`
   - `Client Secret`
5. Abre `Edit settings`.
6. Em `Redirect URIs`, adiciona exatamente:

```text
http://127.0.0.1:8888/callback
```

7. Guarda as alterações.

### Preencher o `.env`

```env
SPOTIPY_CLIENT_ID=o_teu_client_id
SPOTIPY_CLIENT_SECRET=o_teu_client_secret
SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback
```

### Notas importantes

- O redirect URI tem de bater exatamente certo com o valor configurado no dashboard do Spotify.
- Para apps novas, `127.0.0.1` é a opção segura. Não uses outro valor a menos que saibas o que estás a fazer.
- Na primeira execução, a app deve abrir o browser para pedires autorização.
- O token é guardado localmente em `.cache/spotify_token.json`.

## Configurar o Google Calendar

O projeto usa OAuth com a Google Calendar API para ler os eventos de hoje.

Links úteis:

- quickstart oficial em Python: [Google Calendar API Python Quickstart](https://developers.google.com/workspace/calendar/api/quickstart/python)
- configurar consent screen: [Configure OAuth Consent](https://developers.google.com/workspace/guides/configure-oauth-consent)
- consola cloud: [Google Cloud Console](https://console.cloud.google.com/)
- página da API: [Google Calendar API](https://console.cloud.google.com/apis/library/calendar-json.googleapis.com)

### Passos

1. Vai à [Google Cloud Console](https://console.cloud.google.com/).
2. Cria um projeto novo ou escolhe um existente.
3. Ativa a [Google Calendar API](https://console.cloud.google.com/apis/library/calendar-json.googleapis.com).
4. Configura o OAuth consent screen.
5. Cria credenciais do tipo:
   - `OAuth client ID`
   - `Desktop app`
6. Faz download do ficheiro JSON das credenciais.
7. Guarda esse ficheiro na raiz do projeto com o nome:

```text
credentials.json
```

Deves deixar o `credentials.json` na pasta root do projeto.

### Preencher o `.env`

Se quiseres usar o teu calendário principal:

```env
GOOGLE_CALENDAR_ID=primary
```

Se quiseres usar outro calendário, troca esse valor pelo ID do calendário.

### Notas importantes

- Na primeira execução, a app deve abrir o browser para login Google.
- Depois da autorização, será criado um ficheiro `token.json` na raiz do projeto.
- Se a tua app Google estiver em modo de teste, garante que o teu email está nos `Test users`.

## Como arrancar a aplicação

### Por Script no Windows

```powershell
D:\statusclock\start_statusclock.bat
```

### Direto por Python

```powershell
cd D:\statusclock
.venv\Scripts\python.exe -m src.statusclock
```

### Método direto pelo ficheiro principal

Isto também está preparado para funcionar:

```powershell
D:\statusclock\.venv\Scripts\python.exe D:\statusclock\src\statusclock\main.py
```

## Atalhos

- `Esc` fecha a app
- `F11` alterna fullscreen

## FAQs

### `ModuleNotFoundError: No module named 'dotenv'`

Estás a usar um Python diferente daquele onde instalaste as dependências.

Solução:

```powershell
cd D:\statusclock
D:\statusclock\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### `ImportError: attempted relative import with no known parent package`

Isso acontece quando arrancas com um comando que não está a usar o projeto como pacote.

Usa um destes:

```powershell
D:\statusclock\start_statusclock.bat
```

ou

```powershell
cd D:\statusclock
.venv\Scripts\python.exe -m src.statusclock
```

ou

```powershell
D:\statusclock\.venv\Scripts\python.exe D:\statusclock\src\statusclock\main.py
```

### O Spotify não mostra a música

Confirma:

- `SPOTIPY_CLIENT_ID` preenchido
- `SPOTIPY_CLIENT_SECRET` preenchido
- `SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback`
- esse mesmo redirect URI existe no dashboard do Spotify
- tens o Spotify aberto e uma música em reprodução ou recentemente ativa

### O Google Calendar não mostra eventos

Confirma:

- `credentials.json` existe na raiz
- a Google Calendar API está ativa no projeto certo
- autorizaste a conta no browser
- `GOOGLE_CALENDAR_ID=primary` ou outro ID válido
- o teu utilizador está em `Test users`, se a app estiver em teste

### A app não abre pelo `.bat`

Corre primeiro:

```powershell
D:\statusclock\setup_statusclock.bat
```

### Quero reinstalar as dependências todas

```powershell
cd D:\statusclock
D:\statusclock\.venv\Scripts\python.exe -m pip install --upgrade pip
D:\statusclock\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Dicas de uso

- Se o ecrã for dedicado, podes configurar o Windows para arrancar a app no início de sessão.
- Se mudares credenciais do Spotify ou Google, pode ser útil apagar os tokens antigos e autenticar de novo.
- Se mudares de conta Google, apaga `token.json` e volta a abrir a app.
- Se mudares de conta Spotify, apaga `.cache/spotify_token.json` e volta a abrir a app.
