import io

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db.models import Count, Q
from django.forms import inlineformset_factory
from django.test import TestCase
from django.urls import reverse

from .admin import ChoiceInlineFormSet
from .models import Attempt, Choice, Question, Subject


class ModelStrTests(TestCase):
    def setUp(self) -> None:
        self.subject = Subject.objects.create(name="Математика")
        self.question = Question.objects.create(
            subject=self.subject, text="Сколько будет 2+2?"
        )
        self.choice = Choice.objects.create(
            question=self.question, text="4", is_correct=True
        )

    def test_subject_str(self) -> None:
        self.assertEqual(str(self.subject), "Математика")

    def test_question_str_contains_text_and_subject(self) -> None:
        self.assertIn("Сколько будет 2+2?", str(self.question))
        self.assertIn("Математика", str(self.question))

    def test_choice_str(self) -> None:
        self.assertEqual(str(self.choice), "4")

    def test_attempt_str(self) -> None:
        user = get_user_model().objects.create_user(username="ivan")
        attempt = Attempt.objects.create(
            user=user, subject=self.subject, score=3, total=5
        )
        self.assertEqual(str(attempt), "ivan — Математика: 3/5")

    def test_subject_name_is_unique(self) -> None:
        with self.assertRaises(Exception):
            Subject.objects.create(name="Математика")


class ChoiceInlineFormSetTests(TestCase):
    def setUp(self) -> None:
        self.subject = Subject.objects.create(name="Физика")
        self.question = Question.objects.create(
            subject=self.subject, text="Что такое сила?"
        )

    def _formset(self, choices: list[tuple[str, bool]]):
        data = {
            "choices-TOTAL_FORMS": str(len(choices)),
            "choices-INITIAL_FORMS": "0",
            "choices-MIN_NUM_FORMS": "0",
            "choices-MAX_NUM_FORMS": "1000",
        }
        for i, (text, is_correct) in enumerate(choices):
            data[f"choices-{i}-text"] = text
            data[f"choices-{i}-is_correct"] = "on" if is_correct else ""
        factory = inlineformset_factory(
            Question,
            Choice,
            formset=ChoiceInlineFormSet,
            fields="__all__",
            extra=0,
        )
        return factory(data=data, instance=self.question)

    def test_exactly_one_correct_is_valid(self) -> None:
        formset = self._formset([("A", True), ("B", False), ("C", False)])
        self.assertTrue(formset.is_valid())
        self.assertNotIn(
            "У вопроса должен быть ровно один правильный вариант.",
            formset.non_form_errors(),
        )

    def test_zero_correct_is_invalid(self) -> None:
        formset = self._formset([("A", False), ("B", False)])
        self.assertFalse(formset.is_valid())
        self.assertIn(
            "У вопроса должен быть ровно один правильный вариант.",
            formset.non_form_errors(),
        )

    def test_two_correct_is_invalid(self) -> None:
        formset = self._formset([("A", True), ("B", True)])
        self.assertFalse(formset.is_valid())
        self.assertIn(
            "У вопроса должен быть ровно один правильный вариант.",
            formset.non_form_errors(),
        )

    def test_deleted_correct_choice_counts_as_zero(self) -> None:
        Choice.objects.create(question=self.question, text="A", is_correct=True)
        data = {
            "choices-TOTAL_FORMS": "1",
            "choices-INITIAL_FORMS": "1",
            "choices-MIN_NUM_FORMS": "0",
            "choices-MAX_NUM_FORMS": "1000",
            "choices-0-text": "A",
            "choices-0-is_correct": "on",
            "choices-0-DELETE": "on",
        }
        factory = inlineformset_factory(
            Question,
            Choice,
            formset=ChoiceInlineFormSet,
            fields="__all__",
            extra=0,
        )
        formset = factory(data=data, instance=self.question)
        self.assertFalse(formset.is_valid())
        self.assertIn(
            "У вопроса должен быть ровно один правильный вариант.",
            formset.non_form_errors(),
        )


class QuizViewTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            username="student", password="S3cure-pass!"
        )
        self.client.login(username="student", password="S3cure-pass!")
        self.subject = Subject.objects.create(name="Алгебра")
        self._add_questions(3)

    def _add_questions(self, count: int) -> None:
        for i in range(count):
            question = Question.objects.create(
                subject=self.subject,
                text=f"Вопрос {i}",
                explanation=f"Пояснение {i}",
            )
            Choice.objects.create(
                question=question, text=f"Верно {i}", is_correct=True
            )
            Choice.objects.create(
                question=question, text=f"Неверно {i}", is_correct=False
            )

    def _quiz_url(self) -> str:
        return reverse("quiz:quiz", args=[self.subject.pk])

    def _submit_url(self) -> str:
        return reverse("quiz:quiz_submit", args=[self.subject.pk])

    def _answers(self, correct: bool) -> dict[str, int]:
        data: dict[str, int] = {}
        for qid in self.client.session["quiz_question_ids"]:
            question = Question.objects.get(pk=qid)
            data[f"question_{qid}"] = question.choices.get(is_correct=correct).pk
        return data

    def test_requires_login(self) -> None:
        self.client.logout()
        for url in (
            reverse("quiz:subject_list"),
            self._quiz_url(),
            reverse("quiz:result"),
        ):
            response = self.client.get(url)
            self.assertRedirects(response, f"{reverse('login')}?next={url}")

    def test_subject_list_shows_question_count(self) -> None:
        response = self.client.get(reverse("quiz:subject_list"))
        self.assertContains(response, "Алгебра")
        self.assertContains(response, "3")

    def test_quiz_sends_ten_random_questions(self) -> None:
        self._add_questions(12)
        self.client.get(self._quiz_url())
        ids = self.client.session["quiz_question_ids"]
        self.assertEqual(len(ids), 10)
        self.assertEqual(len(set(ids)), 10)

    def test_quiz_takes_all_when_fewer_than_ten(self) -> None:
        self.client.get(self._quiz_url())
        self.assertEqual(len(self.client.session["quiz_question_ids"]), 3)

    def test_quiz_html_does_not_expose_correctness(self) -> None:
        response = self.client.get(self._quiz_url())
        self.assertNotContains(response, "is_correct")
        self.assertNotContains(response, "correct")

    def test_submit_creates_attempt_and_redirects(self) -> None:
        self.client.get(self._quiz_url())
        response = self.client.post(self._submit_url(), self._answers(correct=True))
        self.assertRedirects(response, reverse("quiz:result"))
        attempt = Attempt.objects.get()
        self.assertEqual(attempt.score, 3)
        self.assertEqual(attempt.total, 3)
        self.assertEqual(attempt.user, self.user)

    def test_refresh_result_does_not_create_new_attempt(self) -> None:
        self.client.get(self._quiz_url())
        self.client.post(self._submit_url(), self._answers(correct=True))
        self.client.get(reverse("quiz:result"))
        self.client.get(reverse("quiz:result"))
        self.assertEqual(Attempt.objects.count(), 1)

    def test_choice_from_another_question_is_ignored(self) -> None:
        self.client.get(self._quiz_url())
        ids = self.client.session["quiz_question_ids"]
        other_question = Question.objects.exclude(pk=ids[0]).first()
        foreign_choice = other_question.choices.get(is_correct=True)
        response = self.client.post(
            self._submit_url(), {f"question_{ids[0]}": foreign_choice.pk}
        )
        self.assertRedirects(response, reverse("quiz:result"))
        attempt = Attempt.objects.get()
        self.assertEqual(attempt.score, 0)

    def test_result_shows_score_mistakes_and_explanation(self) -> None:
        self.client.get(self._quiz_url())
        self.client.post(self._submit_url(), self._answers(correct=False))
        response = self.client.get(reverse("quiz:result"))
        self.assertContains(response, "0 / 3")
        self.assertContains(response, "Правильный ответ:")
        self.assertContains(response, "Пояснение 0")

    def test_get_submit_is_not_allowed(self) -> None:
        self.client.get(self._quiz_url())
        response = self.client.get(self._submit_url())
        self.assertEqual(response.status_code, 405)


class ProgressViewTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            username="student", password="S3cure-pass!"
        )
        self.client.login(username="student", password="S3cure-pass!")
        self.math = Subject.objects.create(name="Математика")
        self.phys = Subject.objects.create(name="Физика")

    def test_requires_login(self) -> None:
        self.client.logout()
        url = reverse("quiz:progress")
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('login')}?next={url}")

    def test_average_percent_per_subject(self) -> None:
        Attempt.objects.create(user=self.user, subject=self.math, score=5, total=10)
        Attempt.objects.create(user=self.user, subject=self.math, score=10, total=10)
        Attempt.objects.create(user=self.user, subject=self.phys, score=0, total=4)
        response = self.client.get(reverse("quiz:progress"))
        self.assertEqual(response.status_code, 200)
        rows = {row["subject__name"]: row for row in response.context["by_subject"]}
        self.assertAlmostEqual(rows["Математика"]["avg_percent"], 75.0)
        self.assertAlmostEqual(rows["Физика"]["avg_percent"], 0.0)
        self.assertEqual(rows["Математика"]["attempts_count"], 2)

    def test_total_zero_is_handled(self) -> None:
        Attempt.objects.create(user=self.user, subject=self.math, score=0, total=0)
        response = self.client.get(reverse("quiz:progress"))
        self.assertEqual(response.status_code, 200)
        row = next(
            r for r in response.context["by_subject"] if r["subject__name"] == "Математика"
        )
        self.assertEqual(row["avg_percent"], 0.0)
        self.assertEqual(response.context["attempts"][0].percent, 0.0)

    def test_shows_only_own_attempts(self) -> None:
        other = get_user_model().objects.create_user(
            username="other", password="P4ssword!"
        )
        Attempt.objects.create(user=other, subject=self.math, score=5, total=10)
        response = self.client.get(reverse("quiz:progress"))
        self.assertEqual(list(response.context["attempts"]), [])
        self.assertEqual(list(response.context["by_subject"]), [])

    def test_no_n_plus_one_queries(self) -> None:
        for i in range(5):
            Attempt.objects.create(
                user=self.user, subject=self.math, score=i, total=10
            )
            Attempt.objects.create(
                user=self.user, subject=self.phys, score=i, total=10
            )
        with self.assertNumQueries(4):
            self.client.get(reverse("quiz:progress"))

    def test_shows_percent(self) -> None:
        Attempt.objects.create(user=self.user, subject=self.math, score=3, total=4)
        response = self.client.get(reverse("quiz:progress"))
        self.assertContains(response, "75,0%")


class SeedQuestionsCommandTests(TestCase):
    def test_seed_creates_expected_data(self) -> None:
        call_command("seed_questions", stdout=io.StringIO())
        self.assertEqual(Subject.objects.count(), 3)
        self.assertEqual(Question.objects.count(), 30)
        self.assertEqual(Choice.objects.count(), 120)
        broken = (
            Question.objects.annotate(
                choices_count=Count("choices"),
                correct_count=Count("choices", filter=Q(choices__is_correct=True)),
            )
            .exclude(choices_count=4, correct_count=1)
            .count()
        )
        self.assertEqual(broken, 0)

    def test_seed_is_idempotent(self) -> None:
        call_command("seed_questions", stdout=io.StringIO())
        before = (
            Subject.objects.count(),
            Question.objects.count(),
            Choice.objects.count(),
        )
        call_command("seed_questions", stdout=io.StringIO())
        after = (
            Subject.objects.count(),
            Question.objects.count(),
            Choice.objects.count(),
        )
        self.assertEqual(after, before)
        self.assertEqual(after, (3, 30, 120))
