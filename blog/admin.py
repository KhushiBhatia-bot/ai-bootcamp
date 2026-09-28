from django.contrib import admin
from .models import Post, Comment, Like, Tag, PostView


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'post_count', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

    def post_count(self, obj):
        return obj.posts.filter(status=Post.STATUS_PUBLISHED).count()
    post_count.short_description = 'Published Posts'


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'published_at', 'tag_list', 'like_count', 'view_count')
    list_filter = ('status', 'tags')
    search_fields = ('title', 'content', 'author__username')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('tags',)
    raw_id_fields = ('author',)

    def tag_list(self, obj):
        return ', '.join(obj.tags.values_list('name', flat=True)) or '-'
    tag_list.short_description = 'Tags'

    def like_count(self, obj):
        return obj.likes.count()
    like_count.short_description = 'Likes'

    def view_count(self, obj):
        return obj.views.count()
    view_count.short_description = 'Views'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'parent', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('content', 'author__username')


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'created_at')


@admin.register(PostView)
class PostViewAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'session_key', 'viewed_at')
    list_filter = ('viewed_at',)
