from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    nickname = models.CharField(max_length=30)
    followings = models.ManyToManyField(
        'self', 
        symmetrical=False, 
        related_name='followers', 
        blank=True,
    )
    mbti_type = models.ForeignKey('mbti.PersonalityType', on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    mbti_badge_visible = models.BooleanField(default=True)  # 배지 표시 여부
    profile_image = models.ImageField(upload_to='profiles/', null=True, blank=True)
