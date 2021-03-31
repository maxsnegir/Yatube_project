from .models import Post, Comment
from django import forms


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['text', 'group', 'image']
        labels = {'text': 'Текст поста',
                  'group': 'Группы',
                  'image': 'Изображение',
                  }
        help_texts = {
            'group': 'Группа, к которой принадлежит данный пост',
            'image': 'Изображение для вашей записи',
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text', ]
