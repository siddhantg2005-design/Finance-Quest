from django.http import JsonResponse


def profile_snapshot(request):
    user = getattr(request, "mongodb_user", None)
    if not user:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    return JsonResponse({
        "user_id": user.get("id"),
        "email": user.get("email"),
        "xp": user.get("xp", 0),
        "level": user.get("level", 1),
        "badges": user.get("badges", []),
    })
