from django.urls import path

from . import views

app_name = "gist"

urlpatterns = [
    path("", views.index, name="index"),
    path("api/start", views.start_task, name="start_task"),
    path("api/status/<str:task_id>", views.get_status, name="get_status"),
]
