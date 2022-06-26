import shutil
import tempfile

from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from ..models import Post, Group, Comment
from django.core.cache import cache

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='testslug',
            description='Тестовое описание'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='Author')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def get_image(self):
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        return SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

    def test_posts_forms_post_create_authorized_user(self):
        """
        [!] Добавляется пост после отправки валидной формы.
        """
        form_data_new = {
            'text': 'Текст из формы',
            'group': '1',
            'image': self.get_image(),
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data_new,
            follow=True
        )
        post = Post.objects.first()
        self.assertEqual(post.text, 'Текст из формы')
        self.assertEqual(post.group, PostsFormsTests.group)
        self.assertEqual(post.image, 'posts/small.gif')
        self.assertRedirects(response, reverse('posts:profile',
                                               kwargs={'username': 'Author'}))

    def test_posts_forms_comment_create_authorized_user(self):
        """
        [!] Добавляется комментарий если пользователь авторизован.
        """
        post = Post.objects.create(
            text='Тестовый пост',
            author=self.user,
        )
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post.pk}),
            data={'text': 'Тестовый комментарий'},
            follow=True
        )
        comment = Comment.objects.first()
        self.assertEqual(comment.text, 'Тестовый комментарий')
        self.assertRedirects(response, reverse('posts:post_detail',
                                               kwargs={'post_id': post.pk}))

    def test_posts_forms_comment_create_guest_user(self):
        """
        [!] Неавторизованный пользователь не может добавить комментарий.
        """
        post = Post.objects.create(
            text='Тестовый пост',
            author=self.user,
        )
        self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post.pk}),
            data={'text': 'Тестовый комментарий'},
            follow=True
        )
        self.assertIsNone(Comment.objects.first())

    def test_posts_forms_post_create_guest_user(self):
        """
        [!] Неавторизованный пользователь не можеть опубликовать пост.
        """
        form_data_new = {
            'text': 'Текст из формы',
            'group': '1',
            'image': self.get_image(),
        }
        self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data_new,
            follow=True
        )
        self.assertIsNone(Post.objects.first())

    def test_posts_forms_post_edit_authorized_user(self):
        """
        [!] Редактируется пост после отправки валидной формы.
        """
        Post.objects.create(
            text='Тестовый пост',
            author=self.user,
        )
        form_data_edited = {
            'text': 'Измененный текст',
            'group': '1',
        }

        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': '1'}),
            data=form_data_edited,
            follow=True
        )
        post = Post.objects.first()
        self.assertEqual(post.text, 'Измененный текст')
        self.assertEqual(post.group, PostsFormsTests.group)
        self.assertRedirects(response, reverse('posts:post_detail',
                                               kwargs={'post_id': '1'}))

    def test_posts_forms_post_edit_guest_user(self):
        """
        [!] Неавторизованный пользователь не может изменить пост.
        """
        Post.objects.create(
            text='Тестовый пост',
            author=self.user,
        )
        form_data_edited = {
            'text': 'Измененный текст',
            'group': '1',
        }

        self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': '1'}),
            data=form_data_edited,
            follow=True
        )
        post = Post.objects.first()
        self.assertEqual(post.text, 'Тестовый пост')
        self.assertEqual(post.group, None)
