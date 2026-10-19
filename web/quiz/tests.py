from django.contrib.auth import get_user_model
from django.forms import inlineformset_factory
from django.test import TestCase

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
        self.assertNotIn("У вопроса должен быть ровно один правильный вариант.", formset.non_form_errors())

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
