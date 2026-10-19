from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from quiz.models import Choice, Question, Subject
from quiz.seed_data import SEED_DATA


class Command(BaseCommand):
    help = "Создаёт 3 предмета и по 10 вопросов к экзамену (идемпотентно)."

    def _validate_seed_data(self) -> None:
        for subject_data in SEED_DATA:
            for question_data in subject_data["questions"]:
                correct_count = sum(
                    1 for choice in question_data["choices"] if choice["is_correct"]
                )
                if len(question_data["choices"]) != 4 or correct_count != 1:
                    raise CommandError(
                        f"Некорректные данные вопроса: {question_data['text'][:60]}"
                    )

    def handle(self, *args: object, **options: object) -> None:
        self._validate_seed_data()
        subjects_created = 0
        questions_created = 0
        choices_created = 0
        with transaction.atomic():
            for subject_data in SEED_DATA:
                subject, created = Subject.objects.get_or_create(
                    name=subject_data["name"],
                    defaults={"description": subject_data["description"]},
                )
                subjects_created += int(created)
                for question_data in subject_data["questions"]:
                    question, created = Question.objects.get_or_create(
                        subject=subject,
                        text=question_data["text"],
                        defaults={"explanation": question_data["explanation"]},
                    )
                    questions_created += int(created)
                    if not created:
                        continue
                    choices = [
                        Choice(question=question, **choice)
                        for choice in question_data["choices"]
                    ]
                    Choice.objects.bulk_create(choices)
                    choices_created += len(choices)
        self.stdout.write(
            self.style.SUCCESS(
                "Готово: "
                f"предметов создано {subjects_created}, "
                f"вопросов {questions_created}, "
                f"вариантов ответа {choices_created}"
            )
        )
