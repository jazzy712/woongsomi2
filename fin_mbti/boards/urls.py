from django.urls import path
from . import views

app_name = 'boards'
urlpatterns = [
    path('',                             views.index,               name='index'),
    path('create/',                      views.create,              name='create'),
    path('<int:pk>/',                    views.detail,              name='detail'),
    path('<int:pk>/update/',             views.update,              name='update'),
    path('<int:pk>/like/',               views.like_board,          name='like_board'),
    path('<int:board_pk>/comment/',      views.comment,             name='comment'),
    path('<int:board_pk>/comment/<int:comment_pk>/like/',
                                         views.like_comment,        name='like_comment'),

    # MBTI 유형별 필터
    path('mbti-type/<str:type_code>/',   views.mbti_type_filter,    name='mbti_type_filter'),
    # (원하시면 카테고리별 필터도)
    path('category/<str:category>/',     views.category_filter,     name='category_filter'),
]
