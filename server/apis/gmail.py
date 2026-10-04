import os

import asyncio
from aiolimiter import AsyncLimiter
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource, build
from googleapiclient.errors import HttpError

_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.labels"]
# Keep headroom below the 6,000 units/minute per-user quota
_QUOTA_LIMIT = 5400
_QUOTA_LIMIT_PERIOD = 60
_QUOTA_COSTS = {
    'messages.get': 20,
    'messages.list': 5,
    'labels.list': 1,
}

quota_limiter = AsyncLimiter(
    max_rate=_QUOTA_LIMIT,
    time_period=_QUOTA_LIMIT_PERIOD,
)

def _is_rate_limit_error(exc):
    if not isinstance(exc, HttpError):
        return False
    if exc.resp.status == 429:
        return True
    if exc.resp.status != 403:
        return False

    details = exc.error_details
    if isinstance(details, dict):
        details = [details]
    if not isinstance(details, list):
        return False

    return any(
        isinstance(detail, dict)
        and detail.get("reason") in {"rateLimitExceeded", "userRateLimitExceeded"}
        for detail in details
    )


class GmailClient:

    def __init__(self):
        self.creds = self._get_credentials()
        self.service = build("gmail", "v1", credentials=self.creds)

    @classmethod
    async def create(cls) -> "GmailClient":
        return await asyncio.to_thread(cls)

    @retry(wait=wait_exponential(multiplier=1, min=2, max=60), stop=stop_after_attempt(5), retry=retry_if_exception(_is_rate_limit_error))
    async def _list_messages(self, service: Resource, max_results: int, page_token: str | None):
        await quota_limiter.acquire(amount=_QUOTA_COSTS['messages.list'])
        
        return await asyncio.to_thread(
            service.users().messages().list(
                userId="me",
                maxResults=max_results,
                pageToken=page_token,
                includeSpamTrash=True,
            ).execute
        )

    @retry(wait=wait_exponential(multiplier=1, min=2, max=60), stop=stop_after_attempt(5), retry=retry_if_exception(_is_rate_limit_error))
    async def _get_message(self, service: Resource, msg_id: str):
        await quota_limiter.acquire(amount=_QUOTA_COSTS['messages.get'])
        
        return await asyncio.to_thread(
            service.users().messages().get(
                userId='me', 
                id=msg_id, 
                format='full'
            ).execute
        )

    @retry(wait=wait_exponential(multiplier=1, min=2, max=60), stop=stop_after_attempt(5), retry=retry_if_exception(_is_rate_limit_error))
    async def _list_labels(self, service: Resource):
        await quota_limiter.acquire(amount=_QUOTA_COSTS['labels.list'])
        
        return await asyncio.to_thread(
            service.users().labels().list(userId='me').execute
        )


    def _get_credentials(self) -> Credentials:
        load_dotenv()

        client_id = os.getenv("GMAIL_CLIENT_ID")
        client_secret = os.getenv("GMAIL_CLIENT_SECRET")
        refresh_token = os.getenv("GMAIL_REFRESH_TOKEN")
        if not client_id or not client_secret or not refresh_token:
            raise RuntimeError(
                "Set GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, and GMAIL_REFRESH_TOKEN"
            )

        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=_SCOPES,
        )
        creds.refresh(Request())
        return creds

    async def get_email_ids(self, max_results: int = 500, page_token: str = None) -> tuple[list[dict[str, str]], str | None]:
        results = await self._list_messages(self.service, max_results, page_token)
        messages = results.get("messages", [])
        next_page_token = results.get("nextPageToken", None)
        return messages, next_page_token

    async def get_email(self, message_id: str) -> dict[str, dict]:
        email =  await self._get_message(self.service, message_id)
        return email

    async def get_labels(self) -> list[dict[str, object]]:
        results = await self._list_labels(self.service)
        return results.get("labels", [])
