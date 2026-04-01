from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


@dataclass(slots=True)
class CalendarEvent:
    title: str
    start_text: str


class GoogleCalendarService:
    def __init__(
        self,
        *,
        credentials_path: Path,
        token_path: Path,
        calendar_id: str,
    ) -> None:
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.calendar_id = calendar_id

    def is_configured(self) -> bool:
        return self.credentials_path.exists()

    def fetch_today(self) -> list[CalendarEvent]:
        if not self.is_configured():
            raise RuntimeError("Falta o ficheiro credentials.json do Google Calendar.")

        try:
            creds = self._load_credentials()
            service = build("calendar", "v3", credentials=creds, cache_discovery=False)

            now = datetime.now().astimezone()
            start = datetime.combine(now.date(), time.min, tzinfo=now.tzinfo)
            end = start + timedelta(days=1)

            response = (
                service.events()
                .list(
                    calendarId=self.calendar_id,
                    timeMin=start.isoformat(),
                    timeMax=end.isoformat(),
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
        except HttpError as exc:
            raise RuntimeError(
                "Erro Google Calendar. Confirma o calendario escolhido e as permissoes OAuth."
            ) from exc

        items = response.get("items", [])

        events: list[CalendarEvent] = []
        for item in items:
            start_data = item.get("start", {})
            start_text = self._format_start(start_data)
            events.append(
                CalendarEvent(
                    title=item.get("summary", "Sem titulo"),
                    start_text=start_text,
                )
            )
        return events

    def _load_credentials(self) -> Credentials:
        creds = None
        if self.token_path.exists():
            creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        elif not creds or not creds.valid:
            self.token_path.parent.mkdir(parents=True, exist_ok=True)
            flow = InstalledAppFlow.from_client_secrets_file(
                str(self.credentials_path), SCOPES
            )
            creds = flow.run_local_server(port=0)
            self.token_path.write_text(creds.to_json(), encoding="utf-8")

        return creds

    @staticmethod
    def _format_start(start_data: dict) -> str:
        if "dateTime" in start_data:
            start_dt = datetime.fromisoformat(start_data["dateTime"].replace("Z", "+00:00"))
            return start_dt.astimezone().strftime("%H:%M")
        if "date" in start_data:
            return "Todo o dia"
        return "Hora desconhecida"
