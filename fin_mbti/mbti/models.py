from django.db import models
from django.conf import settings
from django.utils import timezone

class Survey(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title

class SurveyQuestion(models.Model):
    CATEGORY_CHOICES = [
        ('consumption', '소비 습관'),
        ('investment', '투자 습관'),
        ('risk', '위험 선호도'),
        ('analysis', '정보 탐색/분석'),
        ('goal', '목표/동기'),
    ]
    
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='questions')
    question_text = models.CharField(max_length=200)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return self.question_text

class SurveyResponse(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(SurveyQuestion, on_delete=models.CASCADE)
    answer_value = models.IntegerField()  # 1-5 점수
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'question']
    
    def __str__(self):
        return f"{self.user.username}: {self.question.question_text[:20]} - {self.answer_value}"

class PersonalityType(models.Model):
    type_code = models.CharField(max_length=4, primary_key=True)  # SPM, RPI 등 
    name = models.CharField(max_length=50)
    description = models.TextField()
    
    # 각 축별 특성
    risk_preference = models.CharField(max_length=20, help_text="안정형(S)/도전형(R)")
    consumption_style = models.CharField(max_length=20, help_text="계획형(P)/즉흥형(I)")
    goal_orientation = models.CharField(max_length=20, help_text="장기형(M)/단기형(D)")
    
    def __str__(self):
        return f"{self.type_code} - {self.name}"

class Character(models.Model):
    personality_type = models.OneToOneField(PersonalityType, on_delete=models.CASCADE, related_name='character')
    name = models.CharField(max_length=50)
    image = models.ImageField(upload_to='characters/', blank=True)
    emoji = models.CharField(max_length=10, blank=True)  # 이모지 표시
    
    def __str__(self):
        return f"{self.name} ({self.personality_type.type_code})"

class FinancialProduct(models.Model):
    PRODUCT_TYPES = [
        ('deposit', '예금'),
        ('saving', '적금'),
        ('fund', '펀드'),
        ('stock', '주식'),
        ('etf', 'ETF'),
        ('pension', '연금'),
        ('insurance', '보험'),
        ('loan', '대출'),
    ]
    
    RISK_LEVELS = [
        ('very_low', '매우 낮음'),
        ('low', '낮음'),
        ('medium', '보통'),
        ('high', '높음'),
        ('very_high', '매우 높음'),
    ]
    
    name = models.CharField(max_length=100)
    provider = models.CharField(max_length=50, help_text="상품 제공 금융사")
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPES)
    risk_level = models.CharField(max_length=20, choices=RISK_LEVELS)
    interest_rate = models.FloatField(null=True, blank=True)
    description = models.TextField()
    link = models.URLField(blank=True)
    api_source = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.provider})"

class Recommendation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    personality_type = models.ForeignKey(PersonalityType, on_delete=models.CASCADE, related_name='recommendations')
    product = models.ForeignKey(FinancialProduct, on_delete=models.CASCADE)
    priority = models.PositiveIntegerField(default=0, help_text="추천 우선순위 (낮은 숫자가 높은 우선순위)")
    reason = models.TextField(blank=True)
    recommended_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['priority']
    
    def __str__(self):
        return f"{self.personality_type.type_code} -> {self.product.name}"

class UserShare(models.Model):
    PLATFORM_CHOICES = [
        ('twitter', 'Twitter'),
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        ('kakaotalk', 'KakaoTalk'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shares')
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    shared_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} shared to {self.platform} at {self.shared_at}"
