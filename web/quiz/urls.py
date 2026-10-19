from django.urls import path

from . import views

app_name = "quiz"

urlpatterns = [
    path("", views.subject_list, name="subject_list"),
    path("subject/<int:pk>/", views.quiz, name="quiz"),
    path("subject/<int:pk>/submit/", views.quiz_submit, name="quiz_submit"),
    path("result/", views.result, name="result"),
]
