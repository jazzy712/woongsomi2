# accounts/forms.py
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'nickname', 'email', 'password1', 'password2')

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        # 프로필 수정 시 변경할 필드
        fields = ('nickname', 'email', 'profile_image', 'mbti_badge_visible')
