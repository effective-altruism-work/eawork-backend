from sre_constants import SUCCESS
from eawork.send_email import send_email
from django.conf import settings
from enum import Enum


class Task(Enum):
    IMPORT = "API import"
    EMAIL_ALERT = "Email alerts"
    INDEX_PARITY_CHECK = "Algolia index parity check"


class Code(Enum):
    SUCCESS = "Success"
    FAILURE = "Failure"


def email_log(task: Task, code: Code, content=""):
    icon = "\N{grinning face}" if code == Code.SUCCESS else "\N{cross mark}"
    return send_email(
        subject=f"{icon} {task.value}: {code.value}",
        email_from=settings.DEFAULT_FROM_EMAIL,
        email_to=[settings.LOG_EMAIL, settings.LOG_EMAIL_2],
        template_name="email_log.html",
        template_context={
            "task": task.value,
            "status": code.value,
            "icon": icon,
            "content": content,
        },
    )
