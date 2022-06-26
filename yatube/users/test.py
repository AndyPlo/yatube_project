from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from http import HTTPStatus
from django import forms

User = get_user_model()


class UsersTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.authorized_urls = (
            (reverse('users:password_change_done'),
             'users/password_change_done.html'),
            (reverse('users:password_change'),
             'users/password_change_form.html'),
        )
        cls.guest_urls = (
            (reverse('users:login'),
             'users/login.html'),
            (reverse('users:password_reset_complete'),
             'users/password_reset_complete.html'),
            (reverse('users:password_reset_done'),
             'users/password_reset_done.html'),
            (reverse('users:password_reset_form'),
             'users/password_reset_form.html'),
            (reverse('users:signup'),
             'users/signup.html'),
            (reverse('users:logout'),
             'users/logged_out.html'),
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='AuthUser')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_users_urls_exists_authorized(self):
        """
        [!] Доступность страниц auth для авториз. пользователя.
        """
        for url, _ in UsersTests.authorized_urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_users_urls_exists(self):
        """
        [!] Доступность страниц auth для неавториз. пользователя.
        """
        for url, _ in UsersTests.guest_urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_users_urls_namespace_correct_template(self):
        """
        [!] Вызов корректных шаблонов app_name = users.
        """
        url_template = (UsersTests.authorized_urls + UsersTests.guest_urls)
        for url, template in url_template:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_users_signup_page_correct_context(self):
        """[!] Проверка контекста для users:signup."""
        page_list = [
            ('first_name', forms.fields.CharField),
            ('last_name', forms.fields.CharField),
            ('username', forms.fields.CharField),
            ('email', forms.fields.EmailField),
            ('password1', forms.fields.CharField),
            ('password2', forms.fields.CharField),
        ]
        for value, expected in page_list:
            with self.subTest(value=value):
                response = self.guest_client.get(reverse('users:signup'))
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_users_new_user_create(self):
        """[!] Создается новый пользователь при заполнении формы."""
        form_data = {
            'username': 'testuser',
            'password1': 'Afgk12345',
            'password2': 'Afgk12345',
        }
        response = self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True
        )
        self.assertTrue(User.objects.get(username='testuser'))
        self.assertRedirects(response, reverse('posts:index'))
