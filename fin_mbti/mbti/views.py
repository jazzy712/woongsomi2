# mbti/views.py
import random
import requests
import openai

from django.shortcuts            import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils               import timezone
from django.db.models           import Count
from django.urls                import reverse
from django.http                import JsonResponse
from collections import defaultdict

from rest_framework.response    import Response
from rest_framework.decorators  import api_view

from django.conf                import settings

from .models       import (
    Survey,
    SurveyQuestion,
    SurveyResponse,
    PersonalityType,
    Recommendation,
    UserShare
)
from .serializers  import SurveyQuestionSerializer
from .services     import calculate_financial_mbti
from boards.models import Board
from savings.services     import recommend_for_user
from savings.models       import DepositProduct, AnnuityProduct

# OpenAI 키 설정
openai.api_key = settings.OPENAI_API_KEY

@login_required
def survey(request):
    # 1) 현재 활성 설문
    current_survey = get_object_or_404(Survey, pk=1)

    # 2) 카테고리별로 4개씩 랜덤 추출
    categories = [
        'consumption',  # 소비 습관/계획성
        'investment',   # 저축/투자 습관
        'risk',         # 위험 선호/회피 성향
        'analysis',     # 정보 탐색/분석/계획
        'goal',         # 목표/동기/감정/기타
    ]
    picked = []
    for cat in categories:
        qs = list(SurveyQuestion.objects.filter(survey=current_survey, category=cat))
        if len(qs) >= 4:
            picked.extend(random.sample(qs, 4))
        else:
            picked.extend(qs)
    random.shuffle(picked)

    if request.method == 'POST':
        # 기존 응답 삭제
        SurveyResponse.objects.filter(
            user=request.user,
            question__survey=current_survey
        ).delete()
        # 새 응답 저장
        for q in picked:
            val = request.POST.get(f'question_{q.id}')
            if val and val.isdigit():
                SurveyResponse.objects.create(
                    user=request.user,
                    question=q,
                    answer_value=int(val)
                )
        # MBTI 계산 후 사용자 업데이트
        mbti_type = calculate_financial_mbti(request.user, current_survey)
        request.user.mbti_type = mbti_type
        request.user.mbti_test_date = timezone.now()
        request.user.save()
        # 결과 페이지로 이동
        return redirect('mbti:result')

    # GET일 때 설문 폼 렌더링
    return render(request, 'survey.html', {
        'survey':    current_survey,
        'questions': picked,
    })


@login_required
def result(request):
    if not request.user.mbti_type:
        return redirect('mbti:survey')
    mbti_type = request.user.mbti_type

    recs = recommend_for_user(request.user, top_n=5)

    recommendations = []
    for rec in recs:
        prod     = rec['product']
        title    = rec['title']
        provider = rec['provider']
        score    = rec['score']
        reason   = rec['reason']

        link = (
            reverse('savings:deposit_detail', args=[prod.id])
            if isinstance(prod, DepositProduct)
            else reverse('savings:annuity_detail', args=[prod.id])
        )

        if isinstance(prod, DepositProduct):
            raw_rate = getattr(prod, 'intr_rate', None) or getattr(prod, 'mtrt_int', None)
            rate_display = f"{raw_rate:.2f}%" if raw_rate is not None else "—"
            info = {
                'interest': rate_display,
                'term':     f"{prod.save_trm}개월" if getattr(prod, 'save_trm', None) else None,
            }
        else:
            raw_rate = getattr(prod, 'avg_prft_rate', None)
            rate_display = f"{raw_rate:.2f}%" if raw_rate is not None else "—"
            info = {
                'interest':   rate_display,
                'start_date': prod.sale_strt_day.strftime('%Y-%m-%d') if prod.sale_strt_day else None,
            }

        recommendations.append({
            'name':       title,
            'provider':   provider,
            'reason':     reason,
            'link':       link,
            'score':      score,
            'info':       info,
        })

    similar_users_count = request.user.__class__.objects.filter(
        mbti_type=mbti_type
    ).count()

    popular_posts = (
        Board.objects
             .filter(author__mbti_type=mbti_type)
             .annotate(comment_count=Count('comments'))
             .order_by('-comment_count')[:3]
    )

    return render(request, 'result.html', {
        'mbti_type':           mbti_type,
        'recommendations':     recommendations,
        'similar_users_count': similar_users_count,
        'popular_posts':       popular_posts,
    })


@login_required
@require_POST
def share_result(request):
    if not request.user.mbti_type:
        return JsonResponse({'error': 'No MBTI type found'}, status=400)
    platform = request.POST.get('platform')
    if platform:
        UserShare.objects.create(user=request.user, platform=platform)
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Platform required'}, status=400)


@login_required
def recommendations(request):
    if not request.user.mbti_type:
        return redirect('mbti:survey')
    mbti_type = request.user.mbti_type
    recs = Recommendation.objects.filter(personality_type=mbti_type)
    return render(request, 'recommendations.html', {
        'mbti_type':      mbti_type,
        'recommendations': recs,
    })


def personality_types(request):
    types = PersonalityType.objects.all()
    return render(request, 'types.html', {'types': types})


def personality_type_detail(request, type_code):
    mbti_type  = get_object_or_404(PersonalityType, type_code=type_code)
    recs       = Recommendation.objects.filter(personality_type=mbti_type)
    users_count = mbti_type.users.count()
    return render(request, 'type_detail.html', {
        'mbti_type':      mbti_type,
        'recommendations': recs,
        'users_count':    users_count,
    })


@api_view(['GET'])
def api_questions(request):
    survey_id = request.GET.get('survey')
    qs = SurveyQuestion.objects.filter(survey=survey_id).order_by('order')
    serializer = SurveyQuestionSerializer(qs, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def api_submit_responses(request):
    user = request.user
    data = request.data
    SurveyResponse.objects.filter(user=user, question__survey=data['survey']).delete()
    for r in data['responses']:
        SurveyResponse.objects.create(
            user=request.user,
            question_id=r['question'],
            answer_value=r['answer']
        )
    mbti_type = calculate_financial_mbti(user, Survey.objects.get(id=data['survey']))
    user.mbti_type = mbti_type
    user.save()
    return Response({'status': 'success', 'mbti_type': mbti_type.type_code})


def main_page(request):
    return render(request, 'main.html')
