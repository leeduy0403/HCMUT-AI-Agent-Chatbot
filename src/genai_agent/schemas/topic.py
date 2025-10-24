from pydantic import BaseModel, Field

class TopicSchema(BaseModel):
    name: str = Field(..., description="One of the following values: greeting, off_topic, university_info, undergraduate_info, graduate_info, tuition_fee_info, regulation_info, wanna_exit")
    confidence: float = Field(..., description="Score between 0 and 1")
    context: str = Field(..., description="User input context")
