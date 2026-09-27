from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.utils import timezone
from .models import Post, Comment, Like
from .forms import PostForm, CommentForm


def home_view(request):
    """Public home feed showing all published posts."""
    query = request.GET.get('q', '').strip()
    sort = request.GET.get('sort', 'latest')

    posts = Post.objects.filter(status=Post.STATUS_PUBLISHED).select_related('author')

    if query:
        posts = posts.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(excerpt__icontains=query) |
            Q(author__username__icontains=query) |
            Q(author__first_name__icontains=query) |
            Q(author__last_name__icontains=query)
        )

    if sort == 'popular':
        posts = posts.annotate(num_likes=Count('likes')).order_by('-num_likes', '-published_at')
    elif sort == 'discussed':
        posts = posts.annotate(num_comments=Count('comments')).order_by('-num_comments', '-published_at')
    elif sort == 'oldest':
        posts = posts.order_by('published_at')
    else:  # default latest
        posts = posts.order_by('-published_at')

    paginator = Paginator(posts, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'sort': sort,
        'total_count': posts.count(),
    }
    return render(request, 'blog/home.html', context)


def post_detail_view(request, slug):
    """Post detail page with reading view, like counter, and comment thread."""
    post = get_object_or_404(Post.objects.select_related('author'), slug=slug)

    # Draft protection: only author or superuser can view drafts
    if post.status == Post.STATUS_DRAFT:
        if not (request.user.is_authenticated and (request.user == post.author or request.user.is_superuser)):
            messages.warning(request, "This post is a draft and is not publicly visible.")
            return redirect('blog:home')

    has_liked = False
    if request.user.is_authenticated:
        has_liked = post.likes.filter(user=request.user).exists()

    comments = post.comments.filter(parent__isnull=True).select_related('author', 'author__profile').prefetch_related('replies__author', 'replies__author__profile')
    comment_form = CommentForm()

    context = {
        'post': post,
        'has_liked': has_liked,
        'comments': comments,
        'comment_form': comment_form,
        'like_count': post.likes.count(),
        'comment_count': post.comments.count(),
    }
    return render(request, 'blog/post_detail.html', context)


def author_posts_view(request, username):
    """Public author profile displaying all published posts by a specific user."""
    author = get_object_or_404(User.objects.select_related('profile'), username=username)
    published_posts = Post.objects.filter(
        author=author,
        status=Post.STATUS_PUBLISHED
    ).order_by('-published_at')

    total_likes_received = Like.objects.filter(post__author=author).count()

    paginator = Paginator(published_posts, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'author_user': author,
        'page_obj': page_obj,
        'total_published': published_posts.count(),
        'total_likes_received': total_likes_received,
    }
    return render(request, 'blog/author_posts.html', context)


@login_required
def dashboard_view(request):
    """User dashboard to manage their own blog posts (drafts and published)."""
    user_posts = Post.objects.filter(author=request.user)

    published_posts = user_posts.filter(status=Post.STATUS_PUBLISHED).order_by('-published_at')
    draft_posts = user_posts.filter(status=Post.STATUS_DRAFT).order_by('-updated_at')

    total_likes = Like.objects.filter(post__author=request.user).count()
    total_comments = Comment.objects.filter(post__author=request.user).count()

    context = {
        'published_posts': published_posts,
        'draft_posts': draft_posts,
        'total_posts': user_posts.count(),
        'total_published': published_posts.count(),
        'total_drafts': draft_posts.count(),
        'total_likes': total_likes,
        'total_comments': total_comments,
    }
    return render(request, 'blog/dashboard.html', context)


@login_required
def post_create_view(request):
    """Create a new blog post."""
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            if post.status == Post.STATUS_PUBLISHED:
                post.published_at = timezone.now()
            post.save()
            messages.success(request, f"Post '{post.title}' created successfully!")
            return redirect('blog:post_detail', slug=post.slug)
    else:
        form = PostForm()

    return render(request, 'blog/post_form.html', {'form': form, 'action': 'Create'})


@login_required
def post_update_view(request, slug):
    """Edit an existing blog post. Only the author may edit."""
    post = get_object_or_404(Post, slug=slug)

    if post.author != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("You do not have permission to edit this post.")

    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            updated_post = form.save(commit=False)
            # If changing from draft to published, set published_at if not set
            if updated_post.status == Post.STATUS_PUBLISHED and not updated_post.published_at:
                updated_post.published_at = timezone.now()
            updated_post.save()
            messages.success(request, f"Post '{updated_post.title}' updated successfully!")
            return redirect('blog:post_detail', slug=updated_post.slug)
    else:
        form = PostForm(instance=post)

    return render(request, 'blog/post_form.html', {'form': form, 'action': 'Edit', 'post': post})


@login_required
def post_delete_view(request, slug):
    """Delete a blog post. Only the author may delete."""
    post = get_object_or_404(Post, slug=slug)

    if post.author != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("You do not have permission to delete this post.")

    if request.method == 'POST':
        title = post.title
        post.delete()
        messages.success(request, f"Post '{title}' was deleted successfully.")
        return redirect('blog:dashboard')

    return render(request, 'blog/post_confirm_delete.html', {'post': post})


@login_required
def toggle_like_view(request, slug):
    """Toggle like on a post. Supports both AJAX/Fetch JSON response and standard form submit."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST request required'}, status=405)

    post = get_object_or_404(Post, slug=slug)
    like, created = Like.objects.get_or_create(post=post, user=request.user)

    if not created:
        like.delete()
        liked = False
    else:
        liked = True

    like_count = post.likes.count()

    # Check if request was made via fetch/AJAX
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
        return JsonResponse({'liked': liked, 'count': like_count})

    return redirect('blog:post_detail', slug=post.slug)


@login_required
def add_comment_view(request, slug):
    """Add a comment or reply to a published post."""
    if request.method != 'POST':
        return redirect('blog:post_detail', slug=slug)

    post = get_object_or_404(Post, slug=slug)

    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user

        # Support replying to an existing comment
        parent_id = request.POST.get('parent_id')
        if parent_id:
            try:
                parent_comment = Comment.objects.get(id=parent_id, post=post)
                # Attach to top-level parent if replying to a reply for clean 2-tier threading
                comment.parent = parent_comment.parent if parent_comment.parent else parent_comment
            except Comment.DoesNotExist:
                pass

        comment.save()
        messages.success(request, "Your reply has been posted!" if comment.parent else "Your comment has been posted!")
        anchor = f"comment-{comment.id}"
    else:
        messages.error(request, "Unable to post comment. Please provide valid text.")
        anchor = "comments"

    return redirect(f"{post.get_absolute_url()}#{anchor}")


@login_required
def delete_comment_view(request, comment_id):
    """Delete a comment. Permitted for comment author or post author."""
    if request.method != 'POST':
        return HttpResponseForbidden("Method not allowed.")

    comment = get_object_or_404(Comment, id=comment_id)
    post_slug = comment.post.slug

    if request.user != comment.author and request.user != comment.post.author and not request.user.is_superuser:
        return HttpResponseForbidden("You do not have permission to delete this comment.")

    comment.delete()
    messages.success(request, "Comment deleted.")
    return redirect(f"{reverse('blog:post_detail', kwargs={'slug': post_slug})}#comments")
