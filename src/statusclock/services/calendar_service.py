"""Google Calendar integration for fetching today's events."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..i18n import I18N

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


@dataclass(slots=True)
class CalendarEvent:
    """A single calendar event with its display text."""

    title: str
    start_text: str


class GoogleCalendarService:
    """Fetches events from Google Calendar for the current day."""

    def __init__(
        self,
        *,
        credentials_path: Path,
        token_path: Path,
        calendar_id: str,
        i18n: I18N,
    ) -> None:
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.calendar_id = calendar_id
        self.i18n = i18n

    def is_configured(self) -> bool:
        """Check if credentials file exists."""
        return self.credentials_path.exists()

    def fetch_today(self) -> list[CalendarEvent]:
        """Fetch today's events from Google Calendar."""
        if not self.is_configured():
            raise RuntimeError(self.i18n.t("calendar_missing_credentials"))

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
            raise RuntimeError(self.i18n.t("calendar_api_error")) from exc

        return [
            CalendarEvent(
                title=item.get("summary", self.i18n.t("calendar_untitled")),
                start_text=self._format_start(item.get("start", {})),
            )
            for item in response.get("items", [])
        ]

    def _load_credentials(self) -> Credentials:
        """Load or refresh OAuth credentials, prompting for login if needed."""
        creds = None
        if self.token_path.exists():
            creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        elif not creds or not creds.valid:
            self.token_path.parent.mkdir(parents=True, exist_ok=True)
            flow = InstalledAppFlow.from_client_secrets_file(str(self.credentials_path), SCOPES)
            creds = flow.run_local_server(port=0)
            self.token_path.write_text(creds.to_json(), encoding="utf-8")

        return creds

    def _format_start(self, start_data: dict) -> str:
        """Format event start time as HH:MM or 'All day'."""
        if "dateTime" in start_data:
            start_dt = datetime.fromisoformat(start_data["dateTime"].replace("Z", "+00:00"))
            return start_dt.astimezone().strftime("%H:%M")
        if "date" in start_data:
            return self.i18n.t("calendar_all_day")
        return self.i18n.t("calendar_unknown_time")
