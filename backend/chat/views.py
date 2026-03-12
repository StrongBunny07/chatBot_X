import json
import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST


@csrf_exempt
@require_POST
def chat(request):
    try:
        body = json.loads(request.body)
        message = body.get('message', '').strip()

        if not message:
            return JsonResponse({'error': 'Message is required'}, status=400)

        messages = body.get('history', [])
        messages.append({'role': 'user', 'content': message})

        response = requests.post(
            f'{settings.OLLAMA_BASE_URL}/api/chat',
            json={
                'model': settings.OLLAMA_MODEL,
                'messages': messages,
                'stream': False,
            },
            timeout=120,
        )
        response.raise_for_status()

        data = response.json()
        assistant_message = data.get('message', {}).get('content', '')

        return JsonResponse({
            'response': assistant_message,
            'model': settings.OLLAMA_MODEL,
        })

    except requests.exceptions.ConnectionError:
        return JsonResponse(
            {'error': 'Cannot connect to Ollama. Is the container running?'},
            status=503,
        )
    except requests.exceptions.Timeout:
        return JsonResponse(
            {'error': 'Ollama request timed out'},
            status=504,
        )
    except json.JSONDecodeError:
        return JsonResponse(
            {'error': 'Invalid JSON in request body'},
            status=400,
        )
    except Exception as e:
        return JsonResponse(
            {'error': str(e)},
            status=500,
        )
