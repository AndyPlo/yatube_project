from django.test import TestCase, Client
from django.urls import reverse
from http import HTTPStatus


class AboutURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_urls_exists(self):
        """
        [!] Доступность страниц /about/ для неавториз. пользователя.
        """
        pages_list = (
            reverse('about:author'),
            reverse('about:tech'),
        )
        for page_url in pages_list:
            with self.subTest(page_url=page_url):
                response = self.guest_client.get(page_url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_urls_namespace(self):
        """
        [!] Вызов корректных шаблонов app_name = 'about'.
        """
        pages_list = (
            (reverse('about:author'), 'about/author.html'),
            (reverse('about:tech'), 'about/tech.html'),
        )
        for page_url, template in pages_list:
            with self.subTest(page_url=page_url):
                response = self.guest_client.get(page_url)
                self.assertTemplateUsed(response, template)
