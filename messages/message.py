import uuid
from pydantic import BaseModel, Field, UUID4, model_validator
from typing import Optional
from datetime import datetime

class MessageModel(BaseModel):
    # message sender role
    role: str = Field(..., description="Role of the message sender, e.g. 'Questioner' or 'Responder'.")

    # message content
    message: Optional[str] = Field(None, description="The message content.")

    # indicates if this message is partial
    partial: bool = Field(False, description="Indicates if this is a partial/streamed message.")

    # unique ID for correlating requests/responses
    request_id: UUID4 = Field(default_factory=uuid.uuid4, description="Unique ID for correlating requests/responses.")

    # timestamp of when the message was received
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of when the message was received.")

    @model_validator(mode="after")
    def validate_message_content(cls, values):
        # Here, `values` is the model instance, not a dict.
        partial = values.partial
        msg = values.message

        # If it's not a partial message, ensure the message field has some content.
        if not partial and (msg is None or msg.strip() == ""):
            raise ValueError("Non-partial messages must have non-empty 'message' content.")
        
        # return the message
        return values
