from django.urls import path
from . import views

app_name="boards"
urlpatterns = [
    path('', views.index, name="index"),
    path('create/', views.create, name='create'),
    path('<int:pk>/', views.detail, name='detail'), 
    path('<int:pk>/update/', views.update, name='update'),   
    path('<int:pk>/like/', views.like_board, name='like_board'),   
    path('category/<str:category>/', views.category_filter, name='category_filter'),
    path('mbti-type/<str:type_code>/', views.mbti_type_filter, name='mbti_type_filter'),
    path('user/<int:user_pk>/', views.user_filter, name='user_filter'),
    path('<int:board_pk>/comment/', views.comment, name='comment'),
    path('<int:board_pk>/comment/<int:comment_pk>/', views.comment_detail, name='comment_detail'),
    path('<int:board_pk>/comment/<int:comment_pk>/like/', views.like_comment, name='like_comment'),
    path('comment/<int:comment_pk>/', views.create_reply, name='create_reply'),
]
