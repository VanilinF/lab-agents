from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AuthFlowTests(TestCase):
    def test_register_creates_user_and_redirects_to_login(self) -> None:
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "petr",
                "password1": "S3cure-pass!",
                "password2": "S3cure-pass!",
            },
        )
        self.assertRedirects(response, reverse("login"))
        self.assertTrue(get_user_model().objects.filter(username="petr").exists())

    def test_login_redirects_home_and_shows_username(self) -> None:
        get_user_model().objects.create_user(username="petr", password="S3cure-pass!")
        response = self.client.post(
            reverse("login"),
            {"username": "petr", "password": "S3cure-pass!"},
        )
        self.assertRedirects(response, reverse("home"))
        response = self.client.get(reverse("home"))
        self.assertContains(response, "petr")

    def test_logout_via_post_redirects_home(self) -> None:
        get_user_model().objects.create_user(username="petr", password="S3cure-pass!")
        self.client.login(username="petr", password="S3cure-pass!")
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("home"))
        response = self.client.get(reverse("home"))
        self.assertNotContains(response, "petr")

    def test_logout_via_get_not_allowed(self) -> None:
        get_user_model().objects.create_user(username="petr", password="S3cure-pass!")
        self.client.login(username="petr", password="S3cure-pass!")
        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 405)
