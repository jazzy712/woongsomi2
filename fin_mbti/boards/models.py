from django.db import models
from django.conf import settings

class Board(models.Model):
    CATEGORY_CHOICES = [
        ('general', '일반 토론'),
        ('investment', '투자 정보'),
        ('mbti_type', 'MBTI 유형별 토론'),
        ('recommendation', '상품 추천/후기'),
    ]
    
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    title = models.CharField(max_length=100)
    content = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    related_mbti_type = models.ForeignKey(
        'mbti.PersonalityType', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='related_boards'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    view_count = models.PositiveIntegerField(default=0)  # 조회수
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liked_boards', blank=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']


class Comment(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    board = models.ForeignKey(
        Board, on_delete=models.CASCADE, related_name='comments'
    )
    parent_comment = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
    )
    content = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liked_comments', blank=True)
    
    def __str__(self):
        return f"Comment by {self.author.username if self.author else 'Unknown'}: {self.content[:20]}"
