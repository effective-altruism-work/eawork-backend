import mailchimp_marketing as MailchimpMarketing
from mailchimp_marketing.api_client import ApiClientError
from ninja.errors import HttpError
import hashlib
import json
from django.conf import settings

#  "subscribed", "unsubscribed", "cleaned", "pending", "transactional", or "archived"

def get_newsletter_subscription_status(email: str) -> str:
    try:
        client = MailchimpMarketing.Client()
        client.set_config(
            {"api_key": settings.MAILCHIMP["API_KEY"], "server": settings.MAILCHIMP["SERVER"]}
        )

        response = client.lists.get_list_member(
            settings.MAILCHIMP["LIST_ID"], email, fields=["status"]
        )
        return response["status"]
    except ApiClientError as error:
        if "title" in error.text:
            jsn = json.loads(error.text)
            if jsn["title"] == "Resource Not Found":
                # this isn't really an error, it just means the user was not found
                # Later we will use a different mailchimp endpoint
                return None
        raise HttpError(error.status_code, error.text)


def post_newsletter_subscribe(email: str, status: str):
    # we also have this check in views.py -> newsletter_subscribe out of an 
    if status == "unsubscribed":
        raise HttpError("400", "email address was previously unsubscribed")
    try:
        client = MailchimpMarketing.Client()
        client.set_config(
            {"api_key": settings.MAILCHIMP["API_KEY"], "server": settings.MAILCHIMP["SERVER"]}
        )

        if status is None:
            # member does not already exist, add with all the params.
            interests = {}
            for interest in settings.MAILCHIMP["INTERESTS"]:
                interests[interest] = True

            res = client.lists.add_list_member(
                settings.MAILCHIMP["LIST_ID"],
                {
                    "status": "subscribed",
                    "email_address": email,
                    "id": hashlib.md5(email.encode("utf-8")).hexdigest(),
                    "interests": interests,
                    "merge_fields": {"SOURCE": "Website"},
                },
            )
            return "subscribed"
        else:
            res = client.lists.update_list_member(
                settings.MAILCHIMP["LIST_ID"], email, {"status": "subscribed"}
            )
            return "subscribed"
    except ApiClientError as error:
        raise HttpError("400", json.loads(error.text))
