from django import forms
from .models import Board, Comment
from mbti.models import PersonalityType

class BoardForm(forms.ModelForm):
    related_mbti_type = forms.ModelChoiceField(
        queryset=PersonalityType.objects.all(),
        required=False,
        label="관련 MBTI 유형",
        help_text="이 게시글과 관련된 MBTI 유형을 선택해주세요."
    )

    class Meta:
        model = Board
        fields = ('title', 'content', 'category', 'related_mbti_type')
        widgets = {
            'content': forms.Textarea(attrs={'rows': 6, 'placeholder': '본문을 입력하세요...'}),
        }


class CommentForm(forms.ModelForm):
    # 대댓글 구현을 위해 parent_comment 필드를 숨김으로 추가
    parent_comment = forms.ModelChoiceField(
        queryset=Comment.objects.all(),
        required=False,
        widget=forms.HiddenInput()
    )

    class Meta:
        model = Comment
        fields = ('content', 'parent_comment')
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': '댓글을 입력하세요...'
            }),
        }
