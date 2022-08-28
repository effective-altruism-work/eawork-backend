import html2text
from django.core.mail import EmailMultiAlternatives


def send_email(
    subject: str,
    message_html: str,
    email_to: str,
    email_from: str = "support@eawork.org",
):
    message_txt = html2text.html2text(message_html)
    msg = EmailMultiAlternatives(
        subject=subject,
        body=message_txt,
        from_email=email_from,
        to=[email_to],
    )
    msg.attach_alternative(message_html, "text/html")
    msg.send()
