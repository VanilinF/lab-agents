import random

from django.contrib.auth.decorators import login_required
from django.db.models import (
    Avg,
    Case,
    Count,
    Expression,
    F,
    FloatField,
    Value,
    When,
)
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Attempt, Question, Subject

QUIZ_SIZE = 10


def _sample_question_ids(subject: Subject) -> list[int]:
    ids = list(subject.questions.values_list("id", flat=True))
    return random.sample(ids, min(QUIZ_SIZE, len(ids)))


def _questions_in_order(ids: list[int]) -> list[Question]:
    by_id = {
        question.pk: question
        for question in Question.objects.filter(pk__in=ids).prefetch_related("choices")
    }
    return [by_id[qid] for qid in ids if qid in by_id]


@login_required
def subject_list(request: HttpRequest) -> HttpResponse:
    subjects = Subject.objects.annotate(question_count=Count("questions"))
    return render(request, "quiz/subject_list.html", {"subjects": subjects})


@login_required
def quiz(request: HttpRequest, pk: int) -> HttpResponse:
    subject = get_object_or_404(Subject, pk=pk)
    ids = _sample_question_ids(subject)
    request.session["quiz_question_ids"] = ids
    request.session["quiz_subject_id"] = subject.pk
    questions = _questions_in_order(ids)
    return render(
        request,
        "quiz/quiz.html",
        {"subject": subject, "questions": questions},
    )


@login_required
@require_POST
def quiz_submit(request: HttpRequest, pk: int) -> HttpResponse:
    subject = get_object_or_404(Subject, pk=pk)
    ids = request.session.get("quiz_question_ids")
    if not ids or request.session.get("quiz_subject_id") != subject.pk:
        return redirect("quiz:quiz", pk=subject.pk)

    questions = _questions_in_order(ids)
    score = 0
    mistakes: list[dict[str, str]] = []
    for question in questions:
        raw_choice_id = request.POST.get(f"question_{question.pk}")
        chosen = None
        if raw_choice_id is not None and raw_choice_id.isdigit():
            chosen = question.choices.filter(pk=int(raw_choice_id)).first()
        correct = question.choices.filter(is_correct=True).first()
        if chosen is not None and chosen.is_correct:
            score += 1
        else:
            mistakes.append(
                {
                    "question": question.text,
                    "your_answer": chosen.text if chosen is not None else "Нет ответа",
                    "correct_answer": correct.text if correct is not None else "",
                    "explanation": question.explanation,
                }
            )

    attempt = Attempt.objects.create(
        user=request.user, subject=subject, score=score, total=len(questions)
    )
    request.session["quiz_result"] = {
        "attempt_id": attempt.pk,
        "subject": subject.name,
        "score": score,
        "total": len(questions),
        "mistakes": mistakes,
    }
    request.session.pop("quiz_question_ids", None)
    request.session.pop("quiz_subject_id", None)
    return redirect("quiz:result")


@login_required
def result(request: HttpRequest) -> HttpResponse:
    payload = request.session.get("quiz_result")
    if not payload:
        return redirect("quiz:subject_list")
    return render(request, "quiz/result.html", {"result": payload})


def _percent_expression() -> Expression:
    return Case(
        When(total=0, then=Value(0.0)),
        default=F("score") * 100.0 / F("total"),
        output_field=FloatField(),
    )


@login_required
def progress(request: HttpRequest) -> HttpResponse:
    attempts = (
        request.user.attempts.select_related("subject")
        .annotate(percent=_percent_expression())
        .order_by("-created_at")
    )
    by_subject = (
        request.user.attempts.values("subject_id", "subject__name")
        .annotate(
            avg_percent=Avg(_percent_expression()),
            attempts_count=Count("id"),
        )
        .order_by("subject__name")
    )
    return render(
        request,
        "quiz/progress.html",
        {"attempts": attempts, "by_subject": by_subject},
    )
