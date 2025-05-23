# savings/urls.py

from django.urls import path
from . import views
from .views import recommendations_view

app_name = 'savings'

urlpatterns = [
    path('', views.deposit_list, name='deposit_list'),
    path('<int:pk>/', views.deposit_detail, name='deposit_detail'),
    path('<int:pk>/subscribe/', views.subscribe_deposit, name='subscribe'),
    path('spot/', views.spot_prices_page, name='spot_prices'),
    path('spot/data/<str:metal>/', views.get_spot_data, name='spot_data'),
    path('videos/', views.video_search_page, name='video_search_page'),
    path('api/videos/', views.youtube_search_api, name='youtube_search_api'),
    path('banks/', views.bank_search_page, name='bank_search'),
    path('api/banks/', views.banks_search_api, name='banks_search_api'),
    path('recommendations/', recommendations_view, name='recommendations'),
    path('compare/', views.compare_deposits, name='compare_deposits'),
]   
