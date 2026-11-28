from ridedesk.adapters.messages import EmailMessage, EmailSender, SmsMessage, SmsSender


def test_each_email_gets_its_own_provider_id(email: EmailSender) -> None:
    message = EmailMessage(to="rider@example.com", subject="Booked", body="See you soon.")

    first = email.send(message)
    second = email.send(message)

    assert first.provider_message_id
    assert first.provider_message_id != second.provider_message_id


def test_each_sms_gets_its_own_provider_id(sms: SmsSender) -> None:
    message = SmsMessage(to="+15550100", body="Your driver is on the way.")

    first = sms.send(message)
    second = sms.send(message)

    assert first.provider_message_id
    assert first.provider_message_id != second.provider_message_id
