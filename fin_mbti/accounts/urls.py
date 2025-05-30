# accounts/urls.py
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('signup/',          views.signup,  name='signup'),
    path('login/',           views.login,   name='login'),
    path('logout/',          views.logout,  name='logout'),
    path('<int:user_pk>/',   views.profile, name='profile'),
    path('<int:user_pk>/follow/', views.follow, name='follow'),
    path('<int:user_pk>/update/', views.update, name='update'),
    path('<int:user_pk>/avatar/', views.avatar_upload, name='avatar_upload'),
]
