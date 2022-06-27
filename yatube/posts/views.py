from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from .forms import PostForm, CommentForm
from .models import Follow, Post, Group, User, Comment
from .utils import posts_on_page
from django.views.decorators.cache import cache_page
from django.core.cache import cache


@cache_page(20, key_prefix='index_page')
def index(request):
    """Главная страница - список постов."""
    posts = Post.objects.all().select_related('author', 'group')
    comments = Comment.objects.all().select_related('post', 'author')
    page_obj = posts_on_page(request, posts)
    return render(
        request,
        'posts/index.html',
        {'page_obj': page_obj, 'comments': comments,
         'is_index': True}
    )


def group_posts(request, slug):
    """Страница с постами одной группы."""
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all().select_related('author', 'group'
                                             ).order_by('pub_date')
    page_obj = posts_on_page(request, posts)
    comments = Comment.objects.all().select_related('post', 'author')
    return render(
        request,
        'posts/group_list.html',
        {'group': group, 'page_obj': page_obj,
         'comments': comments, 'is_group': True}
    )


def profile(request, username):
    """Список постов одного автора с подпиской на автора."""
    author = get_object_or_404(User, username=username)
    posts = author.posts.all().select_related('author', 'group')
    page_obj = posts_on_page(request, posts)
    following = (
        request.user.is_authenticated and request.user.follower.filter(
            user=request.user,
            author=author
        ).exists()
    )
    comments = Comment.objects.all().select_related('post', 'author')
    return render(
        request,
        'posts/profile.html',
        {'page_obj': page_obj, 'author': author, 'comments': comments,
         'is_profile': True, 'following': following}
    )


@login_required
def add_comment(request, post_id):
    """Добавление комментария к посту."""
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = get_object_or_404(Post, pk=post_id)
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


def post_detail(request, post_id):
    """Страница одного поста с добавлением комментариев и редактированием."""
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.all().select_related('author', 'post')
    form = CommentForm()
    return render(
        request,
        'posts/post_detail.html',
        {'post': post, 'comments': comments, 'form': form}
    )


@login_required
def post_create(request):
    """Форма создания нового поста."""
    if request.method == 'POST':
        form = PostForm(
            request.POST or None,
            files=request.FILES or None
        )
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', post.author.username)
        return render(
            request,
            'posts/create_post.html',
            {'form': form}
        )
    form = PostForm()
    return render(
        request,
        'posts/create_post.html',
        {'form': form}
    )


@login_required
def post_edit(request, post_id):
    """Форма редактирования поста."""
    post = get_object_or_404(Post, pk=post_id)
    if post.author == request.user:
        if request.method == 'POST':
            form = PostForm(
                request.POST or None,
                files=request.FILES or None,
                instance=post
            )
            if form.is_valid():
                form.save()
                return redirect('posts:post_detail', post_id)
            return render(
                request,
                'posts/create_post.html',
                {'form': form, 'is_edit': True}
            )
        form = PostForm(instance=post)
        return render(
            request,
            'posts/create_post.html',
            {'form': form, 'is_edit': True}
        )
    return redirect('posts:post_detail', post_id)


@login_required
def follow_index(request):
    """Список постов авторов на которых подписан."""
    posts = Post.objects.filter(
        author__following__user=request.user
    ).select_related('author', 'group')
    page_obj = posts_on_page(request, posts)
    comments = Comment.objects.all().select_related('post', 'author')
    return render(
        request,
        'posts/follow.html',
        {'page_obj': page_obj, 'is_follow': True, 'comments': comments}
    )


@login_required
def profile_follow(request, username):
    """Подписка на автора."""
    author = get_object_or_404(User, username=username)
    following = Follow.objects.filter(user=request.user, author=author)
    if author == request.user or following.exists():
        return redirect('posts:profile', author.username)
    Follow.objects.create(user=request.user, author=author)
    return redirect('posts:profile', author.username)


@login_required
def profile_unfollow(request, username):
    """Отписка от автора."""
    author = get_object_or_404(User, username=username)
    following = Follow.objects.filter(user=request.user, author=author)
    if following.exists():
        following.delete()
    return redirect('posts:profile', author.username)


@login_required
def comment_delete(request, post_id, comment_id, check):
    """Удаление комментария."""
    comment = get_object_or_404(Comment, pk=comment_id)
    if request.user == comment.author:
        if check == 'check':
            return render(
                request,
                'posts/comment_delete_check.html',
                {'post_id': post_id, 'comment_id': comment_id}
            )
        elif check == 'no':
            return redirect('posts:post_detail', post_id=post_id)
        else:
            comment.delete()
            return redirect('posts:post_detail', post_id=post_id)
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def post_delete(request, post_id, check):
    """Удаление поста."""
    post = get_object_or_404(Post, pk=post_id)
    if request.user == post.author:
        if check == 'check':
            return render(
                request,
                'posts/post_delete_check.html',
                {'post_id': post_id}
            )
        elif check == 'no':
            return redirect('posts:post_detail', post_id=post_id)
        else:
            post.delete()
            cache.clear()
            return redirect('posts:profile', username=request.user)
    return redirect('posts:post_detail', post_id=post_id)
