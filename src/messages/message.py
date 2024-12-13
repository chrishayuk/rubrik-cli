import uuid
from pydantic import BaseModel, Field, UUID4, model_validator
from typing import Optional
from datetime import datetime

class MessageModel(BaseModel):
    """
    Defines the structure of incoming and outgoing messages.
    """
    role: str = Field(..., description="Role of the message sender, e.g. 'Questioner' or 'Responder'.")
    message: Optional[str] = Field(None, description="The message content.")
    partial: bool = Field(False, description="Indicates if this is a partial/streamed message.")
    request_id: UUID4 = Field(default_factory=uuid.uuid4, description="Unique ID for correlating requests/responses.")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of when the message was received.")
    message_number: Optional[int] = Field(None, description="Sequence number for partial/streamed messages of a single request_id.")

    @model_validator(mode="after")
    def validate_message_content(cls, values):
        # Ensure that if partial=False, message is not empty.
        if not values.partial and (values.message is None or values.message.strip() == ""):
            raise ValueError("Non-partial messages must have non-empty 'message' content.")
        return values
