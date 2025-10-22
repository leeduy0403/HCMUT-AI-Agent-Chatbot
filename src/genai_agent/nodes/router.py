import os
import json
from dotenv import load_dotenv, find_dotenv
from litellm import completion
from ..schemas.topic import TopicSchema
from pydantic.tools import parse_obj_as
from ..states.sales_agent_state import SalesAgentState
from ..utils.helpers import parsing_messages_to_history, remove_think_tag
from logger import logger
from config import LLM_MODELS

load_dotenv(find_dotenv())

TOPIC = {
    "greeting": "greeting",
    "off_topic": "off_topic",
    "university_info": "university_info",
    "undergraduate_info": "undergraduate_info",
    "graduate_info": "graduate_info",
    "tuition_info": "tuition_info",
    "regulation_info": "regulation_info",
    "wanna_exit": "wanna_exit"
}

def router_node(state: SalesAgentState):
    user_input = state['messages'][-1].content
    chat_history = parsing_messages_to_history(state.get('messages', ''))

    json_example = {
        "name": f"Một trong các giá trị sau: {', '.join(TOPIC.values())}",
        "confidence": "Float Score between 0 and 1",
        "context": "User's input"
    }


    prompt = f"""
    # Role
    - Assistant là một chuyên viên tư vấn học vụ thông minh của **Trường Đại học Bách Khoa – Đại học Quốc gia TP.HCM (HCMUT)**.
    - Assistant có kiến thức toàn diện về thông tin trường, các chương trình đào tạo, quy chế, học phí và hỗ trợ sinh viên.

    # Skills
    - Assistant có kỹ năng giao tiếp thân thiện, lịch sự, và chuyên nghiệp với sinh viên, phụ huynh và giảng viên.
    - Assistant có khả năng hiểu ngữ cảnh hội thoại để phân loại chính xác chủ đề mà người dùng đang hỏi.

    # Context
    ```
    Chat History:
    {chat_history}

    User's input:
    {user_input}

    ```
    # Tasks
    - Assistant MUST đọc kỹ Chat History và User's input để xác định **ý định (intent)** của người dùng.
    - Assistant MUST phân loại ý định này theo các topic sau:

    1. Greeting:
        - Nếu người dùng chào hỏi Assistant. Return "{TOPIC.get("greeting")}"
        - Example:
            - Xin chào
            - Hello
            - Chào bạn
            - Em ơi
            - Có ai không
            - Anh/Chị muốn hỏi chút
            - Cho em hỏi tí nha

    2. Thông tin chung về Trường Đại học Bách Khoa:
        - Nếu người dùng hỏi về các thông tin tổng quan của trường như: lịch sử, địa chỉ, cơ sở, liên hệ, tầm nhìn, sứ mệnh, thành tích. Return "{TOPIC.get("university_info")}"
        - Example:
            - Trường Bách Khoa ở đâu vậy?
            - Cho em hỏi địa chỉ trường Bách Khoa.
            - Trường mình có mấy cơ sở?
            - Giới thiệu về trường Bách Khoa giúp em.
            - Trường Bách Khoa trực thuộc đại học nào?
            - Sứ mệnh của trường là gì?
            - Trường có bao nhiêu khoa?

    3. Thông tin chương trình Đại học (Undergraduate):
        - Nếu người dùng hỏi về ngành học, tuyển sinh, điểm chuẩn, chương trình đào tạo, thời gian học, điều kiện xét tuyển ở bậc đại học. Return "{TOPIC.get("undergraduate_info")}"
        - Example:
            - Cho em hỏi ngành Khoa học máy tính của Bách Khoa.
            - Ngành Cơ khí học mấy năm vậy ạ?
            - Bách Khoa có đào tạo chương trình chất lượng cao không?
            - Điểm chuẩn ngành Công nghệ thông tin năm ngoái bao nhiêu?
            - Tuyển sinh đại học năm nay thế nào?

    4. Thông tin chương trình Sau đại học (Graduate):
        - Nếu người dùng hỏi về chương trình cao học, thạc sĩ, tiến sĩ, hoặc điều kiện xét tuyển sau đại học. Return "{TOPIC.get("graduate_info")}"
        - Example:
            - Bách Khoa có đào tạo thạc sĩ không?
            - Điều kiện để học cao học là gì?
            - Học tiến sĩ tại Bách Khoa mất bao lâu?
            - Có chương trình cao học quốc tế không?

    5. Thông tin học phí và học bổng:
        - Nếu người dùng hỏi về học phí, lệ phí, học bổng, hoặc chính sách miễn giảm học phí. Return "{TOPIC.get("tuition_info")}"
        - Example:
            - Học phí ngành Điện tử của Bách Khoa là bao nhiêu?
            - Chương trình tiên tiến học phí có cao không?
            - Bách Khoa có học bổng dành cho sinh viên giỏi không?
            - Có chính sách miễn giảm học phí cho sinh viên khó khăn không?

    6. Thông tin quy định và quy chế học tập:
        - Nếu người dùng hỏi về quy định học tập, thi cử, bảo lưu, nghỉ học, cảnh báo học vụ, hoặc các quy chế sinh viên. Return "{TOPIC.get("regulation_info")}"
        - Example:
            - Quy định về bảo lưu học tập của Bách Khoa là gì?
            - Khi nào bị cảnh báo học vụ?
            - Nếu bị điểm F thì xử lý như thế nào?
            - Quy chế thi lại của trường ra sao?

    7. Off Topic:
        - Nếu câu hỏi không liên quan đến các chủ đề trên. Return "{TOPIC.get("off_topic")}"
        - Example:
            - Viết thơ đi.
            - Nói chuyện vui chút đi.
            - Hôm nay thời tiết thế nào?
            - Code Python giúp tôi với.

    8. Wanna Exit:
        - Nếu người dùng có ý định kết thúc trò chuyện hoặc không muốn hỏi thêm. Return "{TOPIC.get("wanna_exit")}"
        - Example:
            - Cảm ơn, em biết rồi.
            - Không hỏi nữa nha.
            - Thôi để sau hỏi tiếp.
            - Bye nhé.

    # Ouput
    - Assistant MUST trả lời bằng JSON format với các field như sau:
    ```
    {json.dumps(json_example, ensure_ascii=False)}
    ```

    # Constraints
    - Assistant MUST reply by JSON format ONLY như trong mục Output. No need explaination.
    - Assistant MUST return exactly one of the following topics: {', '.join(TOPIC.values())}.
    - Trong trường hợp Assistant không thể xác định được topic, Assistant DO NOT attempt to guess the topic, just return "{TOPIC.get("off_topic")}".
    """

    response = completion(
        api_key=os.getenv("GROQ_API_KEY"),
        model=LLM_MODELS['router']['router_node'],
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.5,
        response_format=TopicSchema
    )

    new_topic = parse_obj_as(TopicSchema, json.loads(remove_think_tag(response.choices[0].message.content)))
    new_topic.name = new_topic.name.lower()

    topic = state.get('topic', None)
    logger.info(f"Topic: {topic}")

    if isinstance(new_topic.confidence, str):
        new_topic.confidence = 0.0
    if topic is None:
        if new_topic.name != TOPIC.get('off_topic') and new_topic.confidence < 0.5:
            new_topic.name = TOPIC.get('off_topic')

        logger.info(f"New Topic: {new_topic}")
        return {
            "topic": new_topic,
            "human_input": user_input,
            "ai_reply": None
        }

    return {
        "human_input": user_input,
        "ai_reply": None
    }
    