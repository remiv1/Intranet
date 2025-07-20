from pydantic import BaseModel
from datetime import datetime

class LogEntry(BaseModel):
    user_id: str
    page: str
    timestamp: datetime
    session_duration: float | None = None

class LogLogin(LogEntry):
    action: str = "login"

class LogLogout(LogEntry):
    action: str = "logout"

class ChangeSecurity(LogEntry):
    action: str = "change_security"
    security_level: str = 'high'
    user_modified: str | None = None
    change_level: bool = False
    level_before: str | None = None
    level_after: str | None = None
    change_pwd: bool = False
    change_email: bool = False
    email_before: str | None = None
    email_after: str | None = None
    ip_trace: str

class LogPageView(LogEntry):
    action: str = "page_view"
    page_title: str | None = None
    referrer: str | None = None
    user_agent: str | None = None
    ip_address: str | None = None