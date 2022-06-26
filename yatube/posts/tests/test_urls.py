from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from http import HTTPStatus
from django.urls import reverse
from django.core.cache import cache

from ..models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='testslug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост' * 20,
            group=cls.group,
        )
        cls.guest_urls = (
            (reverse('posts:index'), 'posts/index.html'),
            (reverse('posts:post_detail',
                     kwargs={'post_id': '1'}), 'posts/post_detail.html'),
            (reverse('posts:group_list',
                     kwargs={'slug': 'testslug'}), 'posts/group_list.html'),
            (reverse('posts:profile',
                     kwargs={'username': 'Author'}), 'posts/profile.html'),
        )
        cls.authorized_urls = (
            (reverse('posts:post_create'), 'posts/create_post.html'),
            (reverse('posts:post_edit',
                     kwargs={'post_id': '1'}), 'posts/create_post.html'),
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsURLTests.author)
        cache.clear()

    def test_post_urls_exists(self):
        """
        [!] Доступность основных страниц для неавториз. пользователя.
        """
        for url, _ in PostsURLTests.guest_urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_urls_exists_authorized(self):
        """
        [!] Доступность основных страниц для авториз. пользователя (автора).
        """
        for url, _ in PostsURLTests.authorized_urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_urls_404_page(self):
        """
        [!] Провека несуществующей страницы.
        """
        response = self.guest_client.get('/unexist_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_post_urls_create_redirect_guest(self):
        """
        [!] Редирект неавториз. пользователя со страницы posts:post_create.
        """
        response = self.guest_client.get(reverse('posts:post_create'))
        login_url = reverse('users:login')
        create_post_url = reverse('posts:post_create')
        self.assertRedirects(
            response,
            f'{login_url}?next={create_post_url}'
        )

    def test_post_urls_edit_redirect_guest(self):
        """
        [!] Редирект неавториз. пользоват. со страницы posts:post_edit.
        """
        response = self.guest_client.get(reverse('posts:post_edit',
                                                 kwargs={'post_id': '1'}))
        login_url = reverse('users:login')
        edit_post_url = reverse('posts:post_edit', kwargs={'post_id': '1'})
        self.assertRedirects(
            response,
            f'{login_url}?next={edit_post_url}'
        )

    def test_post_urls_redirect_nonauthor(self):
        """
        [!] Редирект не автора со страницы posts:post_edit.
        """
        self.user = User.objects.create_user(username='NonAuthor')
        self.authorized_client.force_login(self.user)
        response = self.authorized_client.get(reverse('posts:post_edit',
                                                      kwargs={'post_id': '1'}))
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': '1'})
        )

    def test_posts_urls_uses_correct_template(self):
        """
        [!] Вызов корректных шаблонов app_name = 'posts'.
        """
        url_template = (
            PostsURLTests.guest_urls
            + PostsURLTests.authorized_urls
        )
        for url, template in url_template:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
