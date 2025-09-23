import tempfile
from typing import List, Optional, cast

from fastapi import Body, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from litellm import completion, transcription
from openai import OpenAI
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.ai import ai_controller
from src.ai.ai_service import get_user_api_key
from src.ai.models import AIImprovementRequest
from src.config import settings
from src.db import get_db
from src.main import app
from src.models import ChatMessage
from src.views import dependency_to_override


@app.post("/api/ai-improvement", response_class=JSONResponse)
async def ai_improvement_create(
    request: AIImprovementRequest = Body(...),
    db: Session = Depends(get_db),
    user=Depends(dependency_to_override),
) -> JSONResponse:
    """
    Create a new AI improvement job.

    Args:
        request: The improvement request containing initiative_id or task_id
        db: Database session
        user: Current authenticated user

    Returns:
        JSONResponse containing job_id and status
    """
    try:
        # Convert ChatMessageInput back to dict for the controller if necessary,
        # or update controller to accept Pydantic models. Assuming dict for now.
        messages_as_dicts = (
            [msg.model_dump() for msg in request.messages] if request.messages else None
        )
        job = ai_controller.create_ai_improvement_job(
            user=user,
            input_data=request.input_data,
            lens=request.lens,
            mode=request.mode,
            # Cast to List[ChatMessage] to satisfy type checker
            thread_id=request.thread_id,
            messages=cast(Optional[List[ChatMessage]], messages_as_dicts),
            db=db,
        )
        return JSONResponse({"job_id": str(job.id), "status": job.status})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/ai-improvement", response_class=JSONResponse)
async def ai_improvement_get(request: Request) -> JSONResponse:
    """
    Placeholder API endpoint for AI improvement functionality.
    This will be expanded with actual AI-driven improvement logic in the future.

    Returns:
        JSONResponse: A simple placeholder response
    """
    return JSONResponse({"message": "Placeholder response"})


@app.post("/api/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(dependency_to_override),
):
    user_litellm_api_key = get_user_api_key(user.id, db)

    if not user_litellm_api_key:
        raise HTTPException(status_code=400, detail="User has no OpenAI API key")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        tmp.write(await file.read())
        tmp.flush()
        with open(tmp.name, "rb") as audio:
            transcript = transcription(
                model="whisper-1",
                file=audio,
                response_format="text",
                language="en",
                api_key=user_litellm_api_key,
                api_base=settings.litellm_url,
            )
            return {"transcript": transcript}


class TextCompletionRequest(BaseModel):
    text: str
    stream: bool = False


class RewriteRequest(BaseModel):
    text: str
    existing_description: str


@app.post("/api/text-completion")
async def text_completion(
    request: TextCompletionRequest = Body(...),
    db: Session = Depends(get_db),
    user=Depends(dependency_to_override),
):
    user_litellm_api_key = get_user_api_key(user.id, db)

    if not user_litellm_api_key:
        raise HTTPException(status_code=400, detail="User has no OpenAI API key")

    text_completion_system_prompt = """
    You are a helpful assistant that completes text.

    The user has started writing a description for an intitiative. A partially written description is provided.
    Your job is to complete the description.

    The message should be in plain text, no markdown, no code blocks, no formatting.

    You may add 2-3 sentences to the description.

    If the current sentence may not be complete, you may continue it.

    If the paragraph seems complete, you may end it and start a new paragraph.

    If the description is complete, you may return nothing.
    """

    if request.stream:

        async def generate():
            response = completion(
                model="gpt-4.1-nano",
                messages=[
                    {"role": "system", "content": text_completion_system_prompt},
                    {"role": "user", "content": request.text},
                ],
                stream=True,
                max_tokens=1000,
                api_key=user_litellm_api_key,
                api_base=settings.litellm_url,
            )

            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    yield f"data: {chunk.choices[0].delta.content}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")
    else:
        response = completion(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": text_completion_system_prompt},
                {"role": "user", "content": request.text},
            ],
            api_key=user_litellm_api_key,
            api_base=settings.litellm_url,
        )
        return {"response": response.choices[0].message.content}


@app.post("/api/rewrite")
async def rewrite_text(
    request: RewriteRequest = Body(...),
    db: Session = Depends(get_db),
    user=Depends(dependency_to_override),
):
    user_litellm_api_key = get_user_api_key(user.id, db)

    if not user_litellm_api_key:
        raise HTTPException(status_code=400, detail="User has no OpenAI API key")

    system_prompt = f"""
    You are a helpful assistant that rewrites text.
    The user will provide text that needs to be rewritten.
    For context, the preceeding text is: {request.existing_description}
    The proceeding text cannot be changed or removed at this point.
    The user's text will be the next paragraph.
    Only output the user provided text, rewritten. Do not include any of the proceeding text in the output text.
    Please rewrite the text to be coherent with the existing description.
    Please rewrite the text to be concise and to the point.
    Please rewrite the text to be grammatically correct.
    Please rewrite the text to be easy to read and understand.
    """

    user_message = request.text

    try:
        response = completion(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            max_tokens=1000,
            api_key=user_litellm_api_key,
            api_base=settings.litellm_url,
        )

        rewritten_text = response.choices[0].message.content
        if rewritten_text is None:
            # Handle the case where content might be None, though unlikely for a successful completion
            raise HTTPException(
                status_code=500, detail="LiteLLM API returned no content."
            )

        return {"rewritten_text": rewritten_text}

    except Exception as e:
        print(f"Error during LiteLLM API call: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error processing rewrite request: {str(e)}"
        )
