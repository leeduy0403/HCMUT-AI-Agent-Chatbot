from pydantic import BaseModel, Field

class TopicSchema(BaseModel):
    name: str = Field(..., description="One of the following values: greeting, off_topic, company_info, wanna_exit, product_consulting, make_order")
    confidence: float = Field(..., description="Score between 0 and 1")
    context: str = Field(..., description="User input context")
