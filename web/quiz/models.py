from django.conf import settings
from django.db import models


class Subject(models.Model):
    name = models.CharField(
        max_length=200, unique=True, verbose_name="Название предмета"
    )
    description = models.TextField(blank=True, verbose_name="Описание")

    class Meta:
        ordering = ["name"]
        verbose_name = "Предмет"
        verbose_name_plural = "Предметы"

    def __str__(self) -> str:
        return self.name


class Question(models.Model):
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="questions",
        verbose_name="Предмет",
    )
    text = models.TextField(verbose_name="Текст вопроса")
    explanation = models.TextField(
        blank=True, verbose_name="Пояснение к правильному ответу"
    )

    class Meta:
        ordering = ["subject__name", "id"]
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"

    def __str__(self) -> str:
        return f"{self.text[:60]} ({self.subject})"


class Choice(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="choices",
        verbose_name="Вопрос",
    )
    text = models.CharField(max_length=500, verbose_name="Текст варианта")
    is_correct = models.BooleanField(default=False, verbose_name="Правильный")

    class Meta:
        ordering = ["id"]
        verbose_name = "Вариант ответа"
        verbose_name_plural = "Варианты ответов"

    def __str__(self) -> str:
        return self.text


class Attempt(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="attempts",
        verbose_name="Пользователь",
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="attempts",
        verbose_name="Предмет",
    )
    score = models.PositiveIntegerField(
        default=0, verbose_name="Правильных ответов"
    )
    total = models.PositiveIntegerField(default=0, verbose_name="Всего вопросов")
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата создания"
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Попытка"
        verbose_name_plural = "Попытки"

    def __str__(self) -> str:
        return f"{self.user} — {self.subject}: {self.score}/{self.total}"
