import json
import time
from typing import AsyncGenerator
import httpx

from app.config import OLLAMA_URL, LLM_MODEL_NAME
from app.services.web_search import search_web


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": (
                "Search the internet for current or factual information "
                "that may not be available in the model's knowledge."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to use on the web.",
                    }
                },
                "required": ["query"],
            },
        },
    }
]


async def call_ollama(
    messages: list[dict],
) -> dict:
    payload = {
        "model": LLM_MODEL_NAME,
        "messages": messages,
        "tools": TOOLS,
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            OLLAMA_URL,
            json=payload,
        )

    response.raise_for_status()
    return response.json()


async def generate_response(
    messages: list[dict[str, str]],
) -> tuple[str, list[dict[str, str]], list[str], dict]:
    ollama_messages = [
        {
            "role": "system",
            "content": (
                "You are ResearchMate, an AI research assistant. "
                "Answer questions accurately and clearly. "
                "When the user asks for current information, "
                "recent events, facts that may have changed, "
                "or information you are uncertain about, "
                "use the search_web tool. "
                "When search results are provided, use them "
                "to construct your answer and do not invent sources."
            ),
        }
    ]

    ollama_messages.extend(messages)

    tools_used = []
    sources = []
    
    usage_stats = {
        "model_name": LLM_MODEL_NAME,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "latency_ms": 0.0,
    }

    start_time = time.time()
    response = await call_ollama(ollama_messages)
    end_time = time.time()
    
    usage_stats["latency_ms"] += (end_time - start_time) * 1000
    usage_stats["prompt_tokens"] += response.get("prompt_eval_count", 0)
    usage_stats["completion_tokens"] += response.get("eval_count", 0)

    assistant_message = response["message"]
    tool_calls = assistant_message.get("tool_calls", [])

    if not tool_calls:
        usage_stats["total_tokens"] = usage_stats["prompt_tokens"] + usage_stats["completion_tokens"]
        return (
            assistant_message.get("content", ""),
            sources,
            tools_used,
            usage_stats,
        )

    ollama_messages.append(assistant_message)

    for tool_call in tool_calls:
        function = tool_call["function"]
        function_name = function["name"]
        arguments = function.get("arguments", {})

        if function_name == "search_web":
            query = arguments.get("query", "")
            tools_used.append("search_web")
            search_results = search_web(
                query=query,
                max_results=5,
            )
            sources.extend(search_results)
            tool_result = json.dumps(
                search_results,
                ensure_ascii=False,
            )
            ollama_messages.append(
                {
                    "role": "tool",
                    "content": tool_result,
                }
            )

    start_time = time.time()
    final_response = await call_ollama(ollama_messages)
    end_time = time.time()
    
    usage_stats["latency_ms"] += (end_time - start_time) * 1000
    usage_stats["prompt_tokens"] += final_response.get("prompt_eval_count", 0)
    usage_stats["completion_tokens"] += final_response.get("eval_count", 0)
    usage_stats["total_tokens"] = usage_stats["prompt_tokens"] + usage_stats["completion_tokens"]

    final_message = final_response["message"]

    return (
        final_message.get("content", ""),
        sources,
        tools_used,
        usage_stats,
    )


async def generate_response_stream(
    messages: list[dict[str, str]],
) -> AsyncGenerator[dict, None]:
    """
    Yields structured SSE events:
    - {"type": "status", "message": "Analyzing question..."}
    - {"type": "tool_start", "tool": "search_web", "query": "..."}
    - {"type": "sources", "sources": [...]}
    - {"type": "token", "content": "..."}
    - {"type": "done", "full_content": "...", "sources": [...], "tools_used": [...], "usage_stats": {...}}
    """
    ollama_messages = [
        {
            "role": "system",
            "content": (
                "You are ResearchMate, an AI research assistant. "
                "Answer questions accurately and clearly. "
                "When the user asks for current information, "
                "recent events, facts that may have changed, "
                "or information you are uncertain about, "
                "use the search_web tool. "
                "When search results are provided, use them "
                "to construct your answer and do not invent sources."
            ),
        }
    ]
    ollama_messages.extend(messages)

    tools_used = []
    sources = []
    full_content = ""
    usage_stats = {
        "model_name": LLM_MODEL_NAME,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "latency_ms": 0.0,
    }

    start_time = time.time()
    yield {"type": "status", "message": "Analyzing research question..."}

    # First call: evaluate whether tool execution is required
    response = await call_ollama(ollama_messages)
    assistant_message = response["message"]
    tool_calls = assistant_message.get("tool_calls", [])

    usage_stats["prompt_tokens"] += response.get("prompt_eval_count", 0)
    usage_stats["completion_tokens"] += response.get("eval_count", 0)

    if tool_calls:
        ollama_messages.append(assistant_message)
        for tool_call in tool_calls:
            function = tool_call["function"]
            function_name = function["name"]
            arguments = function.get("arguments", {})

            if function_name == "search_web":
                query = arguments.get("query", "")
                tools_used.append("search_web")
                yield {
                    "type": "status",
                    "message": f'Searching the web for: "{query}"...',
                }

                search_results = search_web(query=query, max_results=5)
                sources.extend(search_results)

                yield {
                    "type": "sources",
                    "sources": sources,
                }

                tool_result = json.dumps(search_results, ensure_ascii=False)
                ollama_messages.append(
                    {
                        "role": "tool",
                        "content": tool_result,
                    }
                )

        yield {"type": "status", "message": "Synthesizing research report..."}

    # Now stream the final response from Ollama
    payload = {
        "model": LLM_MODEL_NAME,
        "messages": ollama_messages,
        "stream": True,
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream("POST", OLLAMA_URL, json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                    msg = chunk.get("message", {})
                    token = msg.get("content", "")
                    if token:
                        full_content += token
                        yield {"type": "token", "content": token}
                    
                    if chunk.get("done", False):
                        usage_stats["prompt_tokens"] += chunk.get("prompt_eval_count", 0)
                        usage_stats["completion_tokens"] += chunk.get("eval_count", 0)
                except Exception:
                    continue

    end_time = time.time()
    usage_stats["latency_ms"] = (end_time - start_time) * 1000
    usage_stats["total_tokens"] = usage_stats["prompt_tokens"] + usage_stats["completion_tokens"]

    yield {
        "type": "done",
        "full_content": full_content,
        "sources": sources,
        "tools_used": tools_used,
        "usage_stats": usage_stats,
    }