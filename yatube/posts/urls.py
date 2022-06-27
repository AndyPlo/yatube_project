from django.urls import path
from . import views

app_name = 'posts'

urlpatterns = [
    # Посты
    path('', views.index, name='index'),
    path('posts/<int:post_id>/', views.post_detail, name='post_detail'),
    # По группам
    path('group/<slug:slug>/', views.group_posts, name='group_list'),
    # По пользователю
    path('profile/<str:username>/', views.profile, name='profile'),
    # Создание, редактирование и удаление постов
    path('create/', views.post_create, name='post_create'),
    path('posts/<int:post_id>/edit/', views.post_edit, name='post_edit'),
    path(
        'posts/<int:post_id>/delete/<slug:check>/',
        views.post_delete,
        name='post_delete'
    ),
    # Подписки на авторов
    path('follow/', views.follow_index, name='follow_index'),
    path(
        'profile/<str:username>/follow/',
        views.profile_follow,
        name='profile_follow'
    ),
    path(
        'profile/<str:username>/unfollow/',
        views.profile_unfollow,
        name='profile_unfollow'
    ),
    # Комментарии
    path(
        'posts/<int:post_id>/comment/',
        views.add_comment,
        name='add_comment'
    ),
    path(
        'posts/<int:post_id>/comment/<int:comment_id>/delete/<slug:check>/',
        views.comment_delete, name='comment_delete'
    ),
]
