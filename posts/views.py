from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from .models import Post, Group, Follow, Comment
from .forms import PostForm, CommentForm

User = get_user_model()


def index(request):
    search_query = request.GET.get('search', '')
    if search_query:
        posts = Post.objects.filter(text__icontains=search_query)
    else:
        posts = Post.objects.all()
    paginator = Paginator(posts, 10)
    page_num = request.GET.get('page', 1)
    page = paginator.get_page(page_num)
    return render(request, 'index.html', {'page': page,
                                          'paginator': paginator,
                                          'search_query': search_query,
                                          })


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    search_query = request.GET.get('search', '')
    if search_query:
        posts = Post.objects.filter(text__icontains=search_query,
                                    group=group)
    else:
        posts = group.group_posts.all()
    paginator = Paginator(posts, 10)
    page_num = request.GET.get('page', 1)
    page = paginator.get_page(page_num)
    context = {"group": group,
               "page": page,
               'paginator': paginator,
               'search_query': search_query,
               }
    return render(request, "group.html", context)


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == "POST":
        if form.is_valid():
            new_post = form.save(commit=False)
            new_post.author = request.user
            new_post.save()
            return redirect('index')
    return render(request, 'new_post.html', {'form': form,
                                             'edit': False,
                                             })


def profile_view(request, username):
    user = get_object_or_404(User, username=username)
    posts = user.posts.all()
    paginator = Paginator(posts, 10)
    page_num = request.GET.get('page', 1)
    page = paginator.get_page(page_num)
    if request.user.is_authenticated:
        following = user.following.filter(user=request.user)
    else:
        following = ''
    return render(request, 'profile.html', {'author': user,
                                            'posts': page,
                                            'paginator': paginator,
                                            'following': following,
                                            })


def post_view(request, username, post_id):
    post = get_object_or_404(Post, id=post_id,
                             author__username=username)
    comments = post.comments.all()
    form = CommentForm(request.POST)
    if request.user.is_authenticated:
        following = post.author.following.filter(user=request.user)
    else:
        following = ''
    return render(request, 'post.html', {'post': post,
                                         'author': post.author,
                                         'comments': comments,
                                         'form': form,
                                         'show': True,
                                         'following': following,
                                         })


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, id=post_id,
                             author__username=username)
    form = PostForm(request.POST or None, files=request.FILES or None,
                    instance=post)
    if request.user != post.author:
        return redirect('post', username=username, post_id=post.id)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('post', username=post.author,
                            post_id=post.id)
    return render(request, 'new_post.html', {'form': form,
                                             'post': post,
                                             'edit': True,
                                             })


@login_required
def post_delete(request, username, post_id):
    post = get_object_or_404(Post, id=post_id,
                             author__username=username)
    if request.user != post.author:
        return redirect('post', username=username, post_id=post.id)
    if request.method == 'POST':
        post.delete()
        return redirect('index')
    return render(request, 'post_delete.html', {'author': post.author,
                                                'post': post})


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, author__username=username,
                             id=post_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        new_comment = form.save(commit=False)
        new_comment.post = post
        new_comment.author = request.user
        new_comment.save()
        messages.warning(request, 'Комментарий добавлен')
    return redirect('post', username=post.author,
                    post_id=post.id)


@login_required
def edit_comment(request, username, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id,
                                post__id=post_id,
                                post__author__username=username)
    form = CommentForm(request.POST or None, instance=comment)
    if request.user != comment.author:
        return redirect('post', username=comment.post.author,
                        post_id=post_id)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Комментарий изменен успешно')
            return redirect('post', username=comment.post.author,
                            post_id=post_id)
    return render(request, 'post.html', {'form': form,
                                         'author': comment.post.author,
                                         'post': comment.post,
                                         'edit': True,
                                         'comment': comment
                                         })


@login_required
def delete_comment(request, username, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user != comment.author:
        return redirect('post', username=username, post_id=post_id)
    comment.delete()
    messages.warning(request, 'Комментраий успешно удален')
    return redirect('post', username=username, post_id=post_id)


@login_required
def follow_index(request):
    search_query = request.GET.get('search', '')
    if search_query:
        posts = Post.objects.filter(text__icontains=search_query,
                                    author__following__user=request.user
                                    )
    else:
        posts = Post.objects.filter(
            author__following__user=request.user)
    paginator = Paginator(posts, 10)
    page_num = request.GET.get('page', 1)
    page = paginator.get_page(page_num)
    return render(request, "follow.html", {'page': page,
                                           'paginator': paginator,
                                           'search_query': search_query,
                                           })


@login_required
def profile_follow(request, username):
    user = get_object_or_404(User, username=username)
    if user != request.user:
        Follow.objects.get_or_create(user=request.user, author=user)
    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    user = get_object_or_404(User, username=username)
    if user != request.user:
        relation = Follow.objects.filter(user=request.user, author=user)
        relation.delete()
    return redirect('profile', username=username)


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)
