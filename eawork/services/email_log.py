from sre_constants import SUCCESS
from eawork.send_email import send_email
from django.conf import settings
from enum import Enum

class Task(Enum):
    IMPORT = "API import"
    EMAIL_ALERT = "Email alerts"
    INDEX_PARITY_CHECK = "Algolia index parity check"

class Code(Enum):
    SUCCESS = "success"
    FAILURE = "failure"


def email_log(task: Task, status: str, code: Code, content=""):
    icon = "\U0002705" if code == Code.SUCCESS else "\U00026A0"
    return send_email(
        subject=f"{task}: {status} {code}",
        email_from=settings.DEFAULT_FROM_EMAIL,
        email_to=settings.LOG_EMAIL,
        template_name="templates/email_log.html",
        template_context={"task": task, "status": status, "icon": icon, "content": content},
    )
