from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('boards/', include('boards.urls')),
    path('accounts/', include('accounts.urls')),
    path('mbti/', include('mbti.urls')),
    path('savings/', include('savings.urls')),
    path('', RedirectView.as_view(pattern_name='mbti:survey'), name='home'),  # 루트 URL은 설문으로 리다이렉트
]

# 미디어 파일 제공
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
