# accounts/forms.py

from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
from django.forms.widgets import ClearableFileInput

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model  = User
        fields = ('username', 'nickname', 'email', 'password1', 'password2')


# 위젯 서브클래스 정의
class CustomClearableFileInput(ClearableFileInput):
    initial_text = ''               # "Currently" 텍스트 제거
    input_text = '사진 선택'         # 파일 선택 버튼 옆 텍스트
    clear_checkbox_label = ''       # "Clear" 라벨 제거


class ProfileUpdateForm(forms.ModelForm):
    password1 = forms.CharField(
        label='새 비밀번호',
        widget=forms.PasswordInput,
        required=False,
        help_text=password_validation.password_validators_help_text_html()
    )
    password2 = forms.CharField(
        label='비밀번호 확인',
        widget=forms.PasswordInput,
        required=False,
    )

    class Meta:
        model  = User
        fields = (
            'nickname',
            'email',
            'mbti_badge_visible',
            'profile_image',
        )
        widgets = {
            'profile_image': CustomClearableFileInput(
                attrs={'class': 'form-control-file'}
            ),
        }

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 or p2:
            if p1 != p2:
                raise ValidationError("두 비밀번호가 일치하지 않습니다.")
            password_validation.validate_password(p1, self.instance)
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        p1 = self.cleaned_data.get('password1')
        if p1:
            user.set_password(p1)
        if commit:
            user.save()
        return user
    
    
class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = (
            'username',
            'nickname',
            'email',
            'mbti_badge_visible',
            'profile_image',
        )
