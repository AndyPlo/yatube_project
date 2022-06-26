from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostsModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='testslug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост' * 20,
        )

    def test_posts_models_group_have_correct_object_names(self):
        """
        [!] Работа метода __str__ у модели Group.
        """
        self.assertEqual(
            PostsModelTest.group.title,
            str(PostsModelTest.group)
        )

    def test_posts_models_post_have_correct_object_names(self):
        """
        [!] Работа метода __str__ у модели Post.
        """
        self.assertEqual(
            PostsModelTest.post.text[:15],
            str(PostsModelTest.post)
        )

    def test_posts_models_verbose_name(self):
        """
        [!] Поля verbose_name у модели Post.
        """
        field_verboses = [
            ('text', 'Текст'),
            ('pub_date', 'Дата публикации'),
            ('author', 'Автор'),
            ('group', 'Группа'),
        ]
        for value, expected in field_verboses:
            with self.subTest(value=value):
                self.assertEqual(
                    PostsModelTest.post._meta.get_field(value).verbose_name,
                    expected
                )

    def test_posts_models_help_text(self):
        """
        [!] Поля help_text у модели Post.
        """
        field_help_texts = [
            ('text', 'Текст нового поста'),
            ('group', 'Группа, к которой будет относиться пост'),
        ]
        for value, expected in field_help_texts:
            with self.subTest(value=value):
                self.assertEqual(
                    PostsModelTest.post._meta.get_field(value).help_text,
                    expected
                )
