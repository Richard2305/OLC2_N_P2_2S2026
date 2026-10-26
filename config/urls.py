from django.urls import path
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from config.views import home, compile_view, run_view
@require_GET
def health(request):
    return JsonResponse({"status": "ok", "language": "OxigenNative"})
urlpatterns = [path("", home), path("api/health/", health), path("api/compile/", compile_view), path("api/run/", run_view)]
