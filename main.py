import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import google.genai as genai
from google.genai import types
from os import getenv
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

PROJECT_ID = getenv("PROJECT_ID")
LOCATION = getenv("LOCATION", "us-central1")  # Hoặc vị trí endpoint của bạn
MODEL_ENDPOINT_ID = getenv("MODEL_ENDPOINT_ID")  # Chỉ cần ID, không cần full path

# Kiểm tra nếu các biến môi trường cần thiết không được cấu hình
if not PROJECT_ID or not MODEL_ENDPOINT_ID:
    raise ValueError(
        "Required environment variables PROJECT_ID and MODEL_ENDPOINT_ID must be set"
    )

# Khởi tạo FastAPI app
app = FastAPI(
    title="Archimedes AI Math Solver",
    description="AI-powered mathematics problem solver using Google Vertex AI",
    version="1.0.0",
)


# Định nghĩa cấu trúc dữ liệu cho request body
class GenerationRequest(BaseModel):
    prompt: str
    language: str = "vi"  # Mặc định là Tiếng Việt


# Cấu hình client Generative AI
client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location=LOCATION,
)

# Endpoint của bạn
MODEL_PATH = f"projects/{PROJECT_ID}/locations/{LOCATION}/endpoints/{MODEL_ENDPOINT_ID}"


@app.post("/generate")
async def generate_content(request: GenerationRequest):
    """
    Nhận prompt và language, trả về kết quả từ mô hình Gemini.
    """
    try:
        # Kiểm tra đầu vào
        if not request.prompt.strip():
            raise HTTPException(status_code=400, detail="Prompt cannot be empty")

        # Load system instruction từ file
        si_text1 = ""
        try:
            if request.language == "vi":
                # Nếu ngôn ngữ là Tiếng Việt, đọc file prompt.md
                with open("prompt/prompt_vi.md", "r", encoding="utf-8") as file:
                    si_text1 = file.read()
            else:
                with open("prompt/prompt.md", "r", encoding="utf-8") as file:
                    si_text1 = file.read()
        except:
            si_text1 = ""

        # Tạo content cho request
        contents = [
            types.Content(
                role="user", parts=[types.Part.from_text(text=request.prompt)]
            )
        ]

        # Cấu hình tools
        tools = [
            types.Tool(google_search=types.GoogleSearch()),
        ]

        # Cấu hình generation
        generate_content_config = types.GenerateContentConfig(
            temperature=0.85,
            top_p=1,
            seed=69,
            max_output_tokens=30000,
            safety_settings=[
                types.SafetySetting(
                    category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_ONLY_HIGH"
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_DANGEROUS_CONTENT",
                    threshold="BLOCK_MEDIUM_AND_ABOVE",
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    threshold="BLOCK_MEDIUM_AND_ABOVE",
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_ONLY_HIGH"
                ),
            ],
            tools=tools,
            system_instruction=[types.Part.from_text(text=si_text1)],
            thinking_config=types.ThinkingConfig(
                thinking_budget=10000,
            ),
        )

        # Gọi API và thu thập response
        response_text = ""
        try:
            for chunk in client.models.generate_content_stream(
                model=MODEL_PATH,
                contents=contents,
                config=generate_content_config,
            ):
                if (
                    not chunk.candidates
                    or not chunk.candidates[0].content
                    or not chunk.candidates[0].content.parts
                ):
                    continue
                response_text += chunk.text
        except Exception as api_error:
            raise HTTPException(
                status_code=500, detail=f"API generation error: {str(api_error)}"
            )

        if not response_text.strip():
            raise HTTPException(status_code=500, detail="Empty response from AI model")

        return {"response": response_text}

    except HTTPException:
        # Re-raise HTTPException as-is
        raise
    except Exception as e:
        # Bắt lỗi và trả về thông báo lỗi chi tiết
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/generate/stream")
async def generate_content_stream(request: GenerationRequest):
    """
    Nhận prompt và language, trả về kết quả streaming từ mô hình Gemini.
    """

    def generate_stream():
        try:
            # Kiểm tra đầu vào
            if not request.prompt.strip():
                yield f"data: {json.dumps({'error': 'Prompt cannot be empty'})}\n\n"
                return

            # Load system instruction từ file
            si_text1 = ""
            try:
                if request.language == "vi":
                    # Nếu ngôn ngữ là Tiếng Việt, đọc file prompt.md
                    with open("prompt/prompt_vi.md", "r", encoding="utf-8") as file:
                        si_text1 = file.read()
                else:
                    with open("prompt/prompt.md", "r", encoding="utf-8") as file:
                        si_text1 = file.read()
            except:
                si_text1 = ""

            # Tạo content cho request
            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=request.prompt)],
                )
            ]

            # Cấu hình tools
            tools = [
                types.Tool(google_search=types.GoogleSearch()),
            ]

            # Cấu hình generation
            generate_content_config = types.GenerateContentConfig(
                temperature=0.85,
                top_p=1,
                seed=69,
                max_output_tokens=30000,
                safety_settings=[
                    types.SafetySetting(
                        category="HARM_CATEGORY_HATE_SPEECH",
                        threshold="BLOCK_ONLY_HIGH",
                    ),
                    types.SafetySetting(
                        category="HARM_CATEGORY_DANGEROUS_CONTENT",
                        threshold="BLOCK_MEDIUM_AND_ABOVE",
                    ),
                    types.SafetySetting(
                        category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        threshold="BLOCK_MEDIUM_AND_ABOVE",
                    ),
                    types.SafetySetting(
                        category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_ONLY_HIGH"
                    ),
                ],
                tools=tools,
                system_instruction=[types.Part.from_text(text=si_text1)],
                thinking_config=types.ThinkingConfig(
                    thinking_budget=10000,
                ),
            )

            # Gửi thông báo bắt đầu
            yield f"data: {json.dumps({'type': 'start', 'message': 'Generating response...'})}\n\n"

            # Gọi API và stream response
            response_text = ""
            try:
                for chunk in client.models.generate_content_stream(
                    model=MODEL_PATH,
                    contents=contents,
                    config=generate_content_config,
                ):
                    if (
                        not chunk.candidates
                        or not chunk.candidates[0].content
                        or not chunk.candidates[0].content.parts
                    ):
                        continue

                    chunk_text = chunk.text
                    response_text += chunk_text

                    # Gửi chunk data
                    yield f"data: {json.dumps({'type': 'chunk', 'text': chunk_text})}\n\n"

            except Exception as api_error:
                yield f"data: {json.dumps({'type': 'error', 'message': f'API generation error: {str(api_error)}'})}\n\n"
                return

            # Gửi thông báo kết thúc
            if response_text.strip():
                yield f"data: {json.dumps({'type': 'end', 'message': 'Response completed', 'full_text': response_text})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Empty response from AI model'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': f'Internal server error: {str(e)}'})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        },
    )


@app.get("/")
def read_root():
    return {"status": "API is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "Archimedes AI Math Solver"}
