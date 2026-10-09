import os
from typing import TypeVar

from contextlib import asynccontextmanager

from dotenv import load_dotenv
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)
_MODEL = "apodex/apodex-1.1-mini:free" # todo: find a different free model with zdr that supports pydantic
_ROUTING = {"models": ["mistralai/mistral-nemo"]}

load_dotenv()

@asynccontextmanager
async def openrouter():
    client = AsyncOpenAI(
        base_url = os.getenv("OPENROUTER_LLM_BASE_URL"),
        api_key = os.getenv("OPENROUTER_LLM_API_KEY"),
    )
    try:
        yield client
    finally:
        await client.close()

async def structured_output(
    client: AsyncOpenAI,
    messages: list[ChatCompletionMessageParam],
    response_model: type[T] | None = None,
) -> T | str:

    completion = await client.chat.completions.parse(
        model=_MODEL,
        messages=messages,
        response_format=response_model,
        extra_body=_ROUTING,
    )
    message = completion.choices[0].message

    if message.refusal:
        raise RuntimeError(f"Model refused: {message.refusal}")
    if message.parsed is None:
        raise RuntimeError("Model returned no parsed structured output")

    return message.parsed

async def output(
    client: AsyncOpenAI,
    messages: list[ChatCompletionMessageParam],
) -> T | str:
    completion = await client.chat.completions.create(
        model=_MODEL,
        messages=messages,
        extra_body=_ROUTING,
    )
    message = completion.choices[0].message

    if message.refusal:
        raise RuntimeError(f"Model refused: {message.refusal}")
    if message.content is None:
        raise RuntimeError("Model returned no text content")

    return message.content
    