import html2text
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template


def send_email(
    subject: str,
    email_to: str,
    template_name: str = None,
    content_html: str = None,
    template_context: dict = None,
    email_from: str = settings.DEFAULT_FROM_EMAIL,
):
    origin_param = "&utm_source=job-board-alerts"
    if template_name:
        template_html = get_template(template_name)
        content_html = template_html.render(
            {
                "settings": {
                    "BASE_URL": settings.BASE_URL,
                    "FRONTEND_URL": settings.FRONTEND_URL,
                    "ORIGIN_PARAM": origin_param,
                },
                **template_context,
            }
        )
        context_txt = html2text.html2text(content_html)
    elif content_html:
        context_txt = html2text.html2text(content_html)
    else:
        raise ValueError("args not provided")

    msg = EmailMultiAlternatives(
        subject=subject,
        body=context_txt,
        from_email=email_from,
        to=[email_to],
    )
    msg.attach_alternative(content_html, "text/html")
    num_success = msg.send(fail_silently=True)
    return bool(num_success)
