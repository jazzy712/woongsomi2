from django.urls import path
from . import views

app_name = 'mbti'
urlpatterns = [
    # 웹 인터페이스
    path('', views.main_page, name='main'),
    path('survey/', views.survey, name='survey'),
    path('result/', views.result, name='result'),
    path('share/', views.share_result, name='share'),
    path('recommendations/', views.recommendations, name='recommendations'),
    path('types/', views.personality_types, name='types'),
    path('types/<str:type_code>/', views.personality_type_detail, name='type_detail'),
    # path('calculate_mbti_type/', views.calculate_mbti_type, name='calculate_mbti_type'),
    # API 엔드포인트
    # path('api/surveys/', views.SurveyListView.as_view(), name='api_surveys'),
    # path('api/questions/', views.SurveyQuestionListView.as_view(), name='api_questions'),
    # path('api/responses/', views.SurveyResponseCreateView.as_view(), name='api_responses'),
    # path('api/types/', views.PersonalityTypeListView.as_view(), name='api_types'),
    # path('api/products/', views.FinancialProductListView.as_view(), name='api_products'),
    # path('api/recommendations/', views.RecommendationListView.as_view(), name='api_recommendations'),
]
