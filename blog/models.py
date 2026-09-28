import math
import bleach
import markdown
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class Tag(models.Model):
    """Content tag for categorising blog posts."""
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=80, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name) or 'tag'
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog:tag_feed', kwargs={'slug': self.slug})


class Post(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_PUBLISHED = 'published'
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_PUBLISHED, 'Published'),
    ]

    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    excerpt = models.TextField(
        blank=True,
        max_length=500,
        help_text="Short summary shown on blog cards (optional, generated from content if blank)"
    )
    content = models.TextField(help_text="Blog post content in Markdown format")
    tags = models.ManyToManyField(Tag, blank=True, related_name='posts')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['-published_at']),
            models.Index(fields=['status']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Auto-generate unique slug if not present
        if not self.slug:
            base_slug = slugify(self.title) or 'post'
            slug_candidate = base_slug
            counter = 1
            while Post.objects.filter(slug=slug_candidate).exclude(pk=self.pk).exists():
                slug_candidate = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug_candidate

        # Auto-generate excerpt if empty
        if not self.excerpt and self.content:
            plain_text = bleach.clean(self.content, tags=[], strip=True)
            self.excerpt = plain_text[:200] + ('...' if len(plain_text) > 200 else '')

        # Set published_at timestamp when publishing
        if self.status == self.STATUS_PUBLISHED and not self.published_at:
            self.published_at = timezone.now()

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog:post_detail', kwargs={'slug': self.slug})

    @property
    def reading_time_minutes(self):
        word_count = len(self.content.split())
        return max(1, math.ceil(word_count / 200))

    @property
    def rendered_html(self):
        """Render Markdown content to sanitized safe HTML."""
        allowed_tags = [
            'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong', 'em', 'u', 's',
            'blockquote', 'code', 'pre', 'ul', 'ol', 'li', 'hr', 'br',
            'table', 'thead', 'tbody', 'tr', 'th', 'td', 'a', 'span'
        ]
        allowed_attrs = {
            'a': ['href', 'title', 'target', 'rel'],
            'code': ['class'],
            'span': ['class'],
            'th': ['align'],
            'td': ['align'],
        }
        raw_html = markdown.markdown(
            self.content,
            extensions=['fenced_code', 'tables', 'nl2br', 'codehilite', 'toc']
        )
        return bleach.clean(raw_html, tags=allowed_tags, attributes=allowed_attrs, strip=True)


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='replies'
    )
    content = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.username} on {self.post.title}"

    @property
    def is_parent(self):
        return self.parent is None


class Like(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')

    def __str__(self):
        return f"{self.user.username} liked {self.post.title}"


class PostView(models.Model):
    """Tracks unique post views for related-post scoring and analytics."""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='views')
    # user is nullable so anonymous views can be counted too
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='post_views')
    session_key = models.CharField(max_length=40, blank=True, default='')
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Prevent duplicate counts per session
        unique_together = [('post', 'session_key')]

    def __str__(self):
        return f"View of '{self.post.title}'"
