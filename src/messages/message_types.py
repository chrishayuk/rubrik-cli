import uuid
from enum import Enum
from typing import Optional, Union, Literal
from datetime import datetime
from pydantic import BaseModel, Field, UUID4, model_validator

class MessageRole(str, Enum):
    QUESTIONER = "Questioner"
    RESPONDER = "Responder"
    SERVER = "Server"

class MessageType(str, Enum):
    CHAT = "chat"
    HEALTHCHECK = "healthcheck"

class MessageBase(BaseModel):
    request_id: UUID4 = Field(default_factory=uuid.uuid4, description="Unique ID for correlating requests/responses.")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of when the message was received.")
    role: MessageRole = Field(..., description="Role of the message sender.")
    type: MessageType = Field(..., description="Type of the message.")

class ChatMessage(MessageBase):
    type: Literal[MessageType.CHAT] = MessageType.CHAT
    message: str = Field(..., description="The message content.")
    partial: bool = Field(False, description="Indicates if this is a partial/streamed message.")
    message_number: Optional[int] = Field(None, description="Sequence number for partial/streamed messages.")

    @model_validator(mode="after")
    def validate_non_partial_has_message(cls, model):
        # 'model' is an instance of ChatMessage, so we can access fields directly
        if not model.partial:
            if not model.message.strip():
                raise ValueError("Non-partial chat messages must have non-empty 'message' content.")
        return model


class HealthCheckMessage(MessageBase):
    type: Literal[MessageType.HEALTHCHECK] = MessageType.HEALTHCHECK
    # No 'message' field required.

class PartialChatMessage(ChatMessage):
    partial: Literal[True] = True

MessageUnion = Union[ChatMessage, HealthCheckMessage]
