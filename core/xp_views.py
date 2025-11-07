import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .gamelogic import award_xp

@csrf_exempt
def award_xp_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    try:
        body = json.loads(request.body or b"{}")
        user_id = body.get("user_id")
        reason = body.get("reason") or "manual_award"
        xp_amount = int(body.get("xp_amount") or 0)
        if not user_id or xp_amount == 0:
            return JsonResponse({"error": "user_id and positive xp_amount required"}, status=400)
        res = award_xp(str(user_id), reason, int(xp_amount))
        return JsonResponse(res, status=200)
    except Exception:
        return JsonResponse({"error": "XP award failed"}, status=400)
