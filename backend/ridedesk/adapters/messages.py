"""Email and SMS senders. Mocks keep an outbox so tests can read what was sent."""

import uuid
from typing import Protocol

from pydantic import BaseModel, Field


class EmailMessage(BaseModel):
    to: str = Field(min_length=3)
    subject: str
    body: str
    reply_to: str | None = None


class SmsMessage(BaseModel):
    to: str = Field(min_length=7)
    body: str = Field(min_length=1)


class SendResult(BaseModel):
    provider_message_id: str


class EmailSender(Protocol):
    def send(self, message: EmailMessage) -> SendResult: ...


class SmsSender(Protocol):
    def send(self, message: SmsMessage) -> SendResult: ...


class MockEmail:
    def __init__(self) -> None:
        self.outbox: list[EmailMessage] = []

    def send(self, message: EmailMessage) -> SendResult:
        self.outbox.append(message)
        return SendResult(provider_message_id=f"mock-email-{uuid.uuid4().hex}")


class MockSms:
    def __init__(self) -> None:
        self.outbox: list[SmsMessage] = []

    def send(self, message: SmsMessage) -> SendResult:
        self.outbox.append(message)
        return SendResult(provider_message_id=f"mock-sms-{uuid.uuid4().hex}")
