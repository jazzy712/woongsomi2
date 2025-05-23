# accounts/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.http import require_POST
from django.http  import HttpResponseForbidden
from django.contrib  import messages
from django.urls   import reverse
from .models  import User

from .forms import CustomUserCreationForm, ProfileUpdateForm
from boards.models import Board, Comment
from savings.models       import DepositProduct, AnnuityProduct
from savings.services import recommend_for_user

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
    return render(request, 'accounts/signup.html', {'form': form})

def login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, request.POST)
        if form.is_valid():
            auth_login(request, form.get_user())
            return redirect('boards:index')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

def logout(request):
    auth_logout(request)
    return redirect('boards:index')

@login_required
@require_http_methods(["POST"])
def follow(request, user_pk):
    target_user = get_object_or_404(User, pk=user_pk)
    me = request.user
    if me != target_user:
        if target_user in me.followings.all():
            me.followings.remove(target_user)
        else:
            me.followings.add(target_user)
    return redirect('accounts:profile', user_pk=user_pk)

@login_required
def profile(request, user_pk):
    person = get_object_or_404(User, pk=user_pk)

    # --- MBTI & 추천상품 로직 (결과 페이지와 동일) ---
    mbti_type = person.mbti_type
    recommendations = []
    if mbti_type:
        recs = recommend_for_user(person, top_n=5)
        for rec in recs:
            prod     = rec['product']
            title    = rec['title']
            provider = rec['provider']
            score    = rec['score']
            reason   = rec['reason']

            # 상세링크 만들기
            if isinstance(prod, DepositProduct):
                link = reverse('savings:deposit_detail', args=[prod.id])
                raw_rate = getattr(prod, 'intr_rate', None) or getattr(prod, 'mtrt_int', None)
                rate_display = f"{raw_rate:.2f}%" if raw_rate is not None else "—"
                info = {
                    'interest': rate_display,
                    'term':     f"{prod.save_trm}개월" if getattr(prod, 'save_trm', None) else None,
                }
            else:
                link = reverse('savings:annuity_detail', args=[prod.id])
                raw_rate = getattr(prod, 'avg_prft_rate', None)
                rate_display = f"{raw_rate:.2f}%" if raw_rate is not None else "—"
                info = {
                    'interest':   rate_display,
                    'start_date': prod.sale_strt_day.strftime('%Y-%m-%d') if prod.sale_strt_day else None,
                }

            recommendations.append({
                'name':     title,
                'provider': provider,
                'reason':   reason,
                'link':     link,
                'score':    score,
                'info':     info,
            })
    # -----------------------------------------------

    # 기존 프로필 컨텍스트
    posts    = Board.objects.filter(author=person)
    comments = Comment.objects.filter(author=person)

    return render(request, 'accounts/profile.html', {
        'person':           person,
        'posts':            posts,
        'comments':         comments,
        'mbti_type':        mbti_type,
        'recommendations':  recommendations,
    })

@login_required
@require_http_methods(["GET", "POST"])
def update(request, user_pk):
    person = get_object_or_404(User, pk=user_pk)
    if request.user != person:
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=person)
        if form.is_valid():
            form.save()
            return redirect('accounts:profile', user_pk=person.pk)
    else:
        form = ProfileUpdateForm(instance=person)

    return render(request, 'accounts/update.html', {
        'form': form,
        'person': person,
    })

@login_required
@require_POST
def avatar_upload(request, user_pk):
    # 본인만 가능
    if request.user.pk != user_pk:
        return redirect('accounts:profile', user_pk=user_pk)
    avatar = request.FILES.get('profile_image')
    if avatar:
        request.user.profile_image = avatar
        request.user.save()
    return redirect('accounts:profile', user_pk=user_pk)