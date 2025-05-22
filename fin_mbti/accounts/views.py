from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomUserCreationForm
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from boards.models import Board, Comment

User = get_user_model()

def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect('boards:index')
    else:
        form = CustomUserCreationForm()
    context = {
        'form': form,
    }
    return render(request, 'accounts/signup.html', context)


def login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, request.POST)
        if form.is_valid():
            auth_login(request, form.get_user())
            return redirect("boards:index")
    else:
        form = AuthenticationForm()
    context = {
        'form': form,
    }
    return render(request, 'accounts/login.html', context)


def logout(request):
    auth_logout(request)
    return redirect('boards:index')


@login_required
@require_http_methods(["POST"])
def follow(request, user_pk):  # ✅ user_pk를 URL에서 받음
    target_user = get_object_or_404(User, pk=user_pk)
    me = request.user

    if me != target_user:
        if target_user in me.followings.all():
            me.followings.remove(target_user)
        else:
            me.followings.add(target_user)

    return redirect('accounts:profile', user_pk=user_pk)  # 프로필 페이지로 리다이렉트



def profile(request, user_pk):
    person = get_object_or_404(User, pk=user_pk) 
    posts = Board.objects.filter(author=person)  
    comments = Comment.objects.filter(author=person)
    context = {
        'person': person,  # 변수명을 person으로 맞춤
        'posts': posts,
        'comments': comments,
    }
    return render(request, 'accounts/profile.html', context)
