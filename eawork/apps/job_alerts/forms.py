from django import forms


class UnsubscribeForm(forms.Form):
    too_many_emails = forms.BooleanField(label="Too many emails")
    alerts = forms.BooleanField(label="I want to change alert filters")
    unexpected = forms.BooleanField(label="This isn't what I expected")
    irrelevant = forms.BooleanField(label="The roles were not relevant to me")
    other_reason = forms.Textarea()
