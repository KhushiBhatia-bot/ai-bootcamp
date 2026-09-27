from django import forms
from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'excerpt', 'content', 'status']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 text-lg font-semibold text-slate-800 border border-slate-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition placeholder-slate-400',
                'placeholder': 'Enter an inspiring blog title...'
            }),
            'excerpt': forms.Textarea(attrs={
                'rows': 2,
                'class': 'w-full px-4 py-2.5 text-sm text-slate-700 border border-slate-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition placeholder-slate-400 resize-y',
                'placeholder': 'A brief summary of your post for previews (optional)...'
            }),
            'content': forms.Textarea(attrs={
                'rows': 14,
                'class': 'w-full px-4 py-3 text-slate-800 font-mono text-sm border border-slate-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition placeholder-slate-400 resize-y',
                'placeholder': '# Write your post here...\n\nSupports **Markdown**, `code blocks`, lists, tables, and blockquotes!'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-4 py-2.5 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition'
            }),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full px-4 py-2.5 text-sm text-slate-800 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition placeholder-slate-400 resize-y bg-slate-50 focus:bg-white',
                'placeholder': 'Write a respectful and constructive comment...'
            }),
        }
        labels = {
            'content': ''
        }
