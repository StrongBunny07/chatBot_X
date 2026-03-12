import logging
import json
import time

from django.conf import settings
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from huggingface_hub import InferenceClient

from .web_utils import (
    build_system_prompt,
    extract_urls,
    fetch_web_context,
    search_web,
    sanitize_history,
    summarize_history,
)


logger = logging.getLogger('chat')

_hf_client = InferenceClient(api_key=settings.HF_API_KEY)


def _prepare_messages(message, history, use_web, persona=None):
    if persona is None:
        persona = settings.DEFAULT_PERSONA
    
    summary_text, recent_history = summarize_history(
        history,
        settings.CHAT_RECENT_MESSAGES,
        settings.CHAT_SUMMARY_MAX_CHARS,
    )
    urls = extract_urls(message)
    web_context = ''
    used_urls = []
    auto_search_used = False

    if use_web and not urls:
        urls = search_web(message)
        auto_search_used = bool(urls)

    if use_web or urls:
        web_context, used_urls = fetch_web_context(urls)

    persona_prompt = settings.PERSONAS.get(persona, settings.PERSONAS[settings.DEFAULT_PERSONA])
    if web_context:
        system_content = f"{persona_prompt}\n\nWeb context for reference:\n{web_context}"
    else:
        system_content = persona_prompt

    messages = [
        {
            'role': 'system',
            'content': system_content,
        },
    ]

    if summary_text:
        messages.append({'role': 'system', 'content': summary_text})

    messages.extend(recent_history)
    messages.append({'role': 'user', 'content': message})

    return {
        'messages': messages,
        'used_urls': used_urls,
        'auto_search_used': auto_search_used,
        'recent_history_count': len(recent_history),
        'summary_used': bool(summary_text),
        'urls': urls,
    }


def _stream_hf_response(messages, used_urls, client_ip, started_at, auto_search_used):
    response_chars = 0
    try:
        stream = _hf_client.chat.completions.create(
            model=settings.HF_MODEL,
            messages=messages,
            max_tokens=settings.HF_MAX_TOKENS,
            temperature=settings.HF_TEMPERATURE,
            stream=True,
        )
        for chunk in stream:
            content = chunk.choices[0].delta.content or ''
            if content:
                response_chars += len(content)
                yield json.dumps({'type': 'chunk', 'content': content}) + '\n'

        duration_ms = round((time.monotonic() - started_at) * 1000, 2)
        logger.info(
            'Completed chat request ip=%s duration_ms=%s used_web_context=%s auto_search_used=%s source_count=%s response_chars=%s streamed=%s',
            client_ip, duration_ms, bool(used_urls), auto_search_used,
            len(used_urls), response_chars, True,
        )
        yield json.dumps({
            'type': 'done',
            'sources': used_urls,
            'usedWebContext': bool(used_urls),
            'autoSearchUsed': auto_search_used,
        }) + '\n'
    except Exception:
        logger.exception('Error during HuggingFace streaming')
        yield json.dumps({'type': 'error', 'content': 'Streaming error occurred.'}) + '\n'


@csrf_exempt
@require_POST
def chat(request):
    started_at = time.monotonic()
    try:
        body = json.loads(request.body)
        message = body.get('message', '').strip()
        use_web = body.get('useWeb', False)
        stream_response = body.get('stream', True)
        persona = body.get('persona', settings.DEFAULT_PERSONA)

        if not message:
            return JsonResponse({'error': 'Message is required'}, status=400)

        history = sanitize_history(body.get('history', []))
        client_ip = request.META.get('REMOTE_ADDR', 'unknown')
        request_context = _prepare_messages(message, history, use_web, persona)
        messages = request_context['messages']
        used_urls = request_context['used_urls']
        auto_search_used = request_context['auto_search_used']
        urls = request_context['urls']

        logger.info(
            'Incoming chat request ip=%s model=%s history_count=%s use_web=%s auto_search_used=%s summary_used=%s urls=%s message=%r',
            client_ip, settings.HF_MODEL, request_context['recent_history_count'],
            use_web, auto_search_used, request_context['summary_used'],
            urls, message[:200],
        )

        if stream_response:
            return StreamingHttpResponse(
                _stream_hf_response(messages, used_urls, client_ip, started_at, auto_search_used),
                content_type='application/x-ndjson',
            )

        response = _hf_client.chat.completions.create(
            model=settings.HF_MODEL,
            messages=messages,
            max_tokens=settings.HF_MAX_TOKENS,
            temperature=settings.HF_TEMPERATURE,
        )
        assistant_message = response.choices[0].message.content
        duration_ms = round((time.monotonic() - started_at) * 1000, 2)

        logger.info(
            'Completed chat request ip=%s duration_ms=%s used_web_context=%s auto_search_used=%s source_count=%s response_chars=%s streamed=%s',
            client_ip, duration_ms, bool(used_urls), auto_search_used,
            len(used_urls), len(assistant_message), False,
        )

        return JsonResponse({
            'response': assistant_message,
            'model': settings.HF_MODEL,
            'sources': used_urls,
            'usedWebContext': bool(used_urls),
            'autoSearchUsed': auto_search_used,
        })

    except json.JSONDecodeError:
        logger.exception('Invalid JSON received by chat endpoint')
        return JsonResponse({'error': 'Invalid JSON in request body'}, status=400)
    except Exception as e:
        logger.exception('Unexpected error while handling chat request')
        return JsonResponse({'error': str(e)}, status=500)
