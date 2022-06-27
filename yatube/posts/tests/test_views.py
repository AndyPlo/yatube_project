import shutil
import tempfile

from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from ..models import Follow, Group, Post, Comment

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='testslug',
            description='Тестовое описание',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsViewsTests.author)
        cache.clear()

    def context_check(self, post):
        self.assertEqual(post.text, 'Тестовый пост')
        self.assertEqual(post.group.title, 'Тестовая группа')
        self.assertEqual(post.group.description, 'Тестовое описание')
        self.assertEqual(post.author.username, 'Author')
        self.assertEqual(post.pub_date, PostsViewsTests.post.pub_date)
        self.assertEqual(post.image, PostsViewsTests.post.image)

    def test_posts_views_paginator(self):
        """[!] Паджинатор работает."""
        post_count = 12
        posts_list = [
            Post(
                text=f'Тестовый пост {i}',
                author=PostsViewsTests.author,
                group=PostsViewsTests.group
            ) for i in range(1, post_count)
        ]
        Post.objects.bulk_create(posts_list)
        fst_page = settings.POSTS_PER_PAGE
        sec_page = post_count - fst_page
        page_list = [
            (reverse('posts:index'), fst_page),
            (reverse('posts:index') + '?page=2', sec_page),
            (reverse('posts:group_list',
                     kwargs={'slug': 'testslug'}), fst_page),
            (reverse('posts:group_list',
                     kwargs={'slug': 'testslug'}) + '?page=2', sec_page),
            (reverse('posts:profile',
                     kwargs={'username': 'Author'}), fst_page),
            (reverse('posts:profile',
                     kwargs={'username': 'Author'}) + '?page=2', sec_page),
        ]
        for reverse_name, post_on_page in page_list:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(
                    len(response.context['page_obj']), post_on_page
                )

    def test_posts_views_index_correct_context(self):
        """
        [!] Проверка контекста для posts:index.
        """
        response = self.authorized_client.get(reverse('posts:index'))
        PostsViewsTests.context_check(self, response.context['page_obj'][0])

    def test_posts_views_group_list_correct_conrext(self):
        """
        [!] Проверка контекста для posts:group_list.
        """
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'testslug'}))
        PostsViewsTests.context_check(self, response.context['page_obj'][0])

    def test_posts_views_profile_correct_conrext(self):
        """
        [!] Проверка контекста для posts:profile.
        """
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'Author'}))
        PostsViewsTests.context_check(self, response.context['page_obj'][0])

    def test_posts_views_post_detail_correct_context(self):
        """[!] Проверка контекста для posts:post_detail."""
        self.authorized_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': PostsViewsTests.post.pk}),
            data={'text': 'Тестовый комментарий'},
            follow=True
        )
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': '1'}))
        PostsViewsTests.context_check(self, response.context['post'])
        self.assertEqual(
            response.context['comments'][0].text,
            'Тестовый комментарий'
        )
        self.assertEqual(
            response.context['comments'][0].author.username,
            'Author'
        )

    def test_posts_views_pages_with_form_correct_context(self):
        """
        [!] Проверка контекста для страниц с формами.
        """
        url_form_list = (
            (reverse('posts:post_create'),
             'text', forms.fields.CharField),
            (reverse('posts:post_create'),
             'group', forms.fields.ChoiceField),
            (reverse('posts:post_edit', kwargs={'post_id': '1'}),
             'text', forms.fields.CharField),
            (reverse('posts:post_edit', kwargs={'post_id': '1'}),
             'group', forms.fields.ChoiceField),
        )
        for reverse_name, value, expected in url_form_list:
            with self.subTest(value=value):
                response = self.authorized_client.get(reverse_name)
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_posts_views_post_create_check(self):
        """
        [!] Дополнительная проверка нового поста с группой.
        """
        self.another_author = User.objects.create_user(
            username='AnotherAuthor')
        self.another_group = Group.objects.create(
            title='Другая группа',
            slug='anotherslug',
            description='Другое описание',
        )
        post = Post.objects.create(
            author=self.another_author,
            text='Новый пост',
            group=self.another_group,
        )
        page_list_in = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'anotherslug'}),
            reverse('posts:profile', kwargs={'username': 'AnotherAuthor'})
        ]
        page_list_notin = [
            reverse('posts:group_list', kwargs={'slug': 'testslug'}),
            reverse('posts:profile', kwargs={'username': 'Author'})
        ]
        for reverse_name in page_list_in:
            with self.subTest(post=post):
                response = self.authorized_client.get(reverse_name)
                self.assertIn(post, response.context['page_obj'])
        for reverse_name in page_list_notin:
            with self.subTest(post=post):
                response = self.authorized_client.get(reverse_name)
                self.assertNotIn(post, response.context['page_obj'])

    def test_index_page_cache(self):
        """
        [!] Кеширование posts:index работатет.
        """
        response = self.authorized_client.get(reverse('posts:index'))
        page_content = response.content
        Post.objects.first().delete()
        response = self.authorized_client.get(reverse('posts:index'))
        cached_page_content = response.content
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        cleared_page_content = response.content
        self.assertEqual(page_content, cached_page_content)
        self.assertNotEqual(cached_page_content, cleared_page_content)

    def test_posts_view_follow_authenticated(self):
        """
        [!] Авторизованный пользователь может подписаться на автора.
        """
        another_author = User.objects.create_user(
            username='AnotherAuthor')
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': 'AnotherAuthor'})
        )
        following = Follow.objects.first()
        self.assertEqual(following.author, another_author)

    def test_posts_view_unfollow_authenticated(self):
        """
        [!] Авторизованный пользователь может отписаться от автора.
        """
        Follow.objects.create(
            user=PostsViewsTests.author,
            author=PostsViewsTests.author
        )
        self.authorized_client.get(
            reverse('posts:profile_unfollow', kwargs={'username': 'Author'})
        )
        following = Follow.objects.filter(
            author=PostsViewsTests.author).exists()
        self.assertFalse(following)

    def test_posts_views_follow_correct_context(self):
        """
        [!] Проверка контекста для posts:follow_index.
        """
        Follow.objects.create(
            user=PostsViewsTests.author,
            author=PostsViewsTests.author
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        PostsViewsTests.context_check(self, response.context['page_obj'][0])

    def test_posts_views_unfollow_correct_context(self):
        """
        [!] Проверка контекста posts:follow_index если не подписан.
        """
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotIn(PostsViewsTests.post, response.context['page_obj'])

    def test_posts_views_comments_in_context(self):
        """
        [!] Комментарии в контексте основных страниц.
        """
        page_list = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'testslug'}),
            reverse('posts:profile', kwargs={'username': 'Author'}),
            reverse('posts:follow_index')
        ]
        another_author = User.objects.create_user(
            username='AnotherAuthor')
        comment = Comment.objects.create(
            text='Комментарий',
            post=PostsViewsTests.post,
            author=another_author
        )
        Follow.objects.create(
            user=PostsViewsTests.author,
            author=another_author
        )
        for page in page_list:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                self.assertEqual(
                    response.context['comments'][0].text, comment.text)
                self.assertEqual(
                    response.context['comments'][0].author, comment.author)
                self.assertEqual(
                    response.context['comments'][0].created, comment.created)
