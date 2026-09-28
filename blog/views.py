import json
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.text import slugify
from .models import Post, Comment, Like, Tag, PostView
from .forms import PostForm, CommentForm
from accounts.models import Follow


# ──────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────

def _save_tags(post, tags_input: str):
    """Parse comma-separated tag names and attach them to the post."""
    names = [t.strip().lower() for t in tags_input.split(',') if t.strip()]
    tag_objects = []
    for name in names:
        tag, _ = Tag.objects.get_or_create(name=name, defaults={'slug': slugify(name) or 'tag'})
        tag_objects.append(tag)
    post.tags.set(tag_objects)


def _record_view(request, post):
    """Record a unique page view for a post (throttled per session)."""
    try:
        request.session.save()  # ensure key exists
        session_key = request.session.session_key or ''
        if session_key:
            PostView.objects.get_or_create(
                post=post,
                session_key=session_key,
                defaults={'user': request.user if request.user.is_authenticated else None},
            )
    except Exception:
        pass  # never let view tracking break the page


# ──────────────────────────────────────────────────────────────
# PUBLIC VIEWS
# ──────────────────────────────────────────────────────────────

def home_view(request):
    """Public home feed with search, sort, tag filter, and personalised 'For You' tab."""
    query = request.GET.get('q', '').strip()
    sort = request.GET.get('sort', 'latest')
    tag_slug = request.GET.get('tag', '').strip()
    feed = request.GET.get('feed', 'all')  # 'all' | 'following'

    posts = Post.objects.filter(status=Post.STATUS_PUBLISHED).select_related('author').prefetch_related('tags')

    # 'For You' feed — posts from authors the user follows
    if feed == 'following' and request.user.is_authenticated:
        followed_ids = Follow.objects.filter(follower=request.user).values_list('following_id', flat=True)
        posts = posts.filter(author_id__in=followed_ids)

    if tag_slug:
        posts = posts.filter(tags__slug=tag_slug)

    if query:
        posts = posts.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(excerpt__icontains=query) |
            Q(author__username__icontains=query) |
            Q(author__first_name__icontains=query) |
            Q(author__last_name__icontains=query) |
            Q(tags__name__icontains=query)
        ).distinct()

    if sort == 'popular':
        posts = posts.annotate(num_likes=Count('likes')).order_by('-num_likes', '-published_at')
    elif sort == 'discussed':
        posts = posts.annotate(num_comments=Count('comments')).order_by('-num_comments', '-published_at')
    elif sort == 'oldest':
        posts = posts.order_by('published_at')
    else:
        posts = posts.order_by('-published_at')

    paginator = Paginator(posts, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Popular tags for sidebar/filter chips
    popular_tags = Tag.objects.filter(posts__status=Post.STATUS_PUBLISHED).annotate(
        post_count=Count('posts')
    ).order_by('-post_count')[:15]

    active_tag = Tag.objects.filter(slug=tag_slug).first() if tag_slug else None

    context = {
        'page_obj': page_obj,
        'query': query,
        'sort': sort,
        'total_count': posts.count(),
        'popular_tags': popular_tags,
        'active_tag': active_tag,
        'feed': feed,
    }
    return render(request, 'blog/home.html', context)


def post_detail_view(request, slug):
    """Post detail page with reading view, like counter, comment thread, related posts, and view tracking."""
    post = get_object_or_404(
        Post.objects.select_related('author').prefetch_related('tags'),
        slug=slug
    )

    # Draft protection
    if post.status == Post.STATUS_DRAFT:
        if not (request.user.is_authenticated and (request.user == post.author or request.user.is_superuser)):
            messages.warning(request, "This post is a draft and is not publicly visible.")
            return redirect('blog:home')

    # Record view
    _record_view(request, post)

    has_liked = False
    if request.user.is_authenticated:
        has_liked = post.likes.filter(user=request.user).exists()

    comments = post.comments.filter(parent__isnull=True).select_related(
        'author', 'author__profile'
    ).prefetch_related('replies__author', 'replies__author__profile')
    comment_form = CommentForm()

    # Related posts: same tags, exclude current, order by shared tag count
    tag_ids = list(post.tags.values_list('id', flat=True))
    related_posts = []
    if tag_ids:
        related_posts = (
            Post.objects.filter(status=Post.STATUS_PUBLISHED, tags__in=tag_ids)
            .exclude(pk=post.pk)
            .annotate(shared_tags=Count('tags'))
            .order_by('-shared_tags', '-published_at')
            .select_related('author')
            .prefetch_related('tags')[:4]
        )

    context = {
        'post': post,
        'has_liked': has_liked,
        'comments': comments,
        'comment_form': comment_form,
        'like_count': post.likes.count(),
        'comment_count': post.comments.count(),
        'view_count': post.views.count(),
        'related_posts': related_posts,
    }
    return render(request, 'blog/post_detail.html', context)


def tag_feed_view(request, slug):
    """Public feed for a specific tag."""
    tag = get_object_or_404(Tag, slug=slug)
    sort = request.GET.get('sort', 'latest')

    posts = Post.objects.filter(
        status=Post.STATUS_PUBLISHED,
        tags=tag
    ).select_related('author').prefetch_related('tags')

    if sort == 'popular':
        posts = posts.annotate(num_likes=Count('likes')).order_by('-num_likes', '-published_at')
    elif sort == 'discussed':
        posts = posts.annotate(num_comments=Count('comments')).order_by('-num_comments', '-published_at')
    else:
        posts = posts.order_by('-published_at')

    paginator = Paginator(posts, 9)
    page_obj = paginator.get_page(request.GET.get('page'))

    # Related tags (tags that co-occur with this tag)
    related_tags = Tag.objects.filter(
        posts__tags=tag,
        posts__status=Post.STATUS_PUBLISHED
    ).exclude(pk=tag.pk).annotate(cnt=Count('posts')).order_by('-cnt')[:8]

    context = {
        'tag': tag,
        'page_obj': page_obj,
        'sort': sort,
        'total_count': posts.count(),
        'related_tags': related_tags,
    }
    return render(request, 'blog/tag_feed.html', context)


def author_posts_view(request, username):
    """Public author profile displaying all published posts by a specific user."""
    author = get_object_or_404(User.objects.select_related('profile'), username=username)
    published_posts = Post.objects.filter(
        author=author,
        status=Post.STATUS_PUBLISHED
    ).order_by('-published_at').prefetch_related('tags')

    total_likes_received = Like.objects.filter(post__author=author).count()
    follower_count = Follow.objects.filter(following=author).count()
    following_count = Follow.objects.filter(follower=author).count()

    is_following = False
    if request.user.is_authenticated and request.user != author:
        is_following = Follow.objects.filter(follower=request.user, following=author).exists()

    paginator = Paginator(published_posts, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'author_user': author,
        'page_obj': page_obj,
        'total_published': published_posts.count(),
        'total_likes_received': total_likes_received,
        'follower_count': follower_count,
        'following_count': following_count,
        'is_following': is_following,
    }
    return render(request, 'blog/author_posts.html', context)


# ──────────────────────────────────────────────────────────────
# AUTHENTICATED – DASHBOARD & CRUD
# ──────────────────────────────────────────────────────────────

@login_required
def dashboard_view(request):
    """User dashboard to manage their own blog posts (drafts and published)."""
    user_posts = Post.objects.filter(author=request.user)

    published_posts = user_posts.filter(status=Post.STATUS_PUBLISHED).order_by('-published_at').prefetch_related('tags')
    draft_posts = user_posts.filter(status=Post.STATUS_DRAFT).order_by('-updated_at').prefetch_related('tags')

    total_likes = Like.objects.filter(post__author=request.user).count()
    total_comments = Comment.objects.filter(post__author=request.user).count()
    total_views = PostView.objects.filter(post__author=request.user).count()

    follower_count = Follow.objects.filter(following=request.user).count()

    context = {
        'published_posts': published_posts,
        'draft_posts': draft_posts,
        'total_posts': user_posts.count(),
        'total_published': published_posts.count(),
        'total_drafts': draft_posts.count(),
        'total_likes': total_likes,
        'total_comments': total_comments,
        'total_views': total_views,
        'follower_count': follower_count,
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
            _save_tags(post, form.cleaned_data.get('tags_input', ''))
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
            if updated_post.status == Post.STATUS_PUBLISHED and not updated_post.published_at:
                updated_post.published_at = timezone.now()
            updated_post.save()
            _save_tags(updated_post, form.cleaned_data.get('tags_input', ''))
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


# ──────────────────────────────────────────────────────────────
# AJAX ENDPOINTS
# ──────────────────────────────────────────────────────────────

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

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
        return JsonResponse({'liked': liked, 'count': like_count})

    return redirect('blog:post_detail', slug=post.slug)


@login_required
def toggle_follow_view(request, username):
    """Follow / unfollow an author. Returns JSON for AJAX or redirects."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST request required'}, status=405)

    target = get_object_or_404(User, username=username)

    if target == request.user:
        return JsonResponse({'error': 'You cannot follow yourself.'}, status=400)

    follow, created = Follow.objects.get_or_create(follower=request.user, following=target)
    if not created:
        follow.delete()
        is_following = False
    else:
        is_following = True

    follower_count = Follow.objects.filter(following=target).count()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
        return JsonResponse({'is_following': is_following, 'follower_count': follower_count})

    return redirect('blog:author_posts', username=username)


@login_required
def ai_assist_view(request):
    """
    AI Writing Assistant powered by Groq (LLaMA 3.1 70B).
    POST body: { "action": "summarize"|"improve"|"suggest_tags"|"suggest_title", "content": "...", "title": "..." }
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)

    action = body.get('action', '')
    content = body.get('content', '').strip()
    title = body.get('title', '').strip()

    if not content and not title:
        return JsonResponse({'error': 'No content provided'}, status=400)

    # Build prompt based on action
    if action == 'summarize':
        prompt = (
            f"You are a professional blog editor. "
            f"Write a compelling 2-sentence excerpt for a blog post titled '{title}'. "
            f"The post content is:\n\n{content[:3000]}\n\n"
            f"Return only the excerpt text, no extra explanation."
        )
    elif action == 'improve':
        prompt = (
            f"You are a professional blog editor. "
            f"Improve the following blog post content to make it more engaging, clear, and well-structured. "
            f"Keep the same ideas but improve clarity, flow, and impact. Return only the improved markdown content.\n\n"
            f"{content[:4000]}"
        )
    elif action == 'suggest_tags':
        prompt = (
            f"You are a blog categorization expert. "
            f"Given this blog post titled '{title}' with content:\n\n{content[:2000]}\n\n"
            f"Suggest 3-6 relevant, short, lowercase tags (comma-separated, no hashtags, no spaces within a tag). "
            f"Return only the comma-separated tags, nothing else."
        )
    elif action == 'suggest_title':
        prompt = (
            f"You are a headline writing expert. "
            f"Given this blog post content:\n\n{content[:2000]}\n\n"
            f"Suggest 3 compelling, SEO-friendly blog post titles. "
            f"Return them as a numbered list (1. Title, 2. Title, 3. Title), nothing else."
        )
    else:
        return JsonResponse({'error': f'Unknown action: {action}'}, status=400)

    # Call Groq API (free tier, LLaMA 3.1 70B)
    try:
        import os
        from groq import Groq

        api_key = os.getenv('GROQ_API_KEY', '')
        if not api_key:
            return JsonResponse({'error': 'GROQ_API_KEY is not set. Get a free key at https://console.groq.com'}, status=500)

        client = Groq(api_key=api_key)
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful writing assistant for a blog platform called Chronicle."},
                {"role": "user", "content": prompt},
            ],
            model="openai/gpt-oss-120b",
            temperature=0.7,
            max_tokens=1024,
        )
        result_text = chat_completion.choices[0].message.content
    except Exception as exc:
        return JsonResponse({'error': f'AI service error: {str(exc)}'}, status=500)

    return JsonResponse({'result': result_text.strip()})


# ──────────────────────────────────────────────────────────────
# COMMENTS
# ──────────────────────────────────────────────────────────────

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

        parent_id = request.POST.get('parent_id')
        if parent_id:
            try:
                parent_comment = Comment.objects.get(id=parent_id, post=post)
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
