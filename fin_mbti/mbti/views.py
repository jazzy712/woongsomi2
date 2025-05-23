# mbti/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Count
from django.urls import reverse

from .services import calculate_financial_mbti
from savings.services import recommend_for_user
from savings.models import DepositProduct, AnnuityProduct


import requests
from django.conf import settings

from rest_framework.response import Response
from rest_framework.decorators import api_view

from .models import (
    Survey, SurveyQuestion, SurveyResponse,
    PersonalityType, Recommendation, UserShare
)
from .serializers import SurveyQuestionSerializer
from boards.models import Board

import openai
openai.api_key = settings.OPENAI_API_KEY


@login_required
def survey(request):
    current_survey = get_object_or_404(Survey, pk=1)
    questions = SurveyQuestion.objects.filter(survey=current_survey).order_by('order')

    if not questions.exists():
        return render(request, 'error.html', {
            'message': '등록된 설문 문항이 없습니다. 관리자에게 문의하세요.'
        })

    if request.method == 'POST':
        SurveyResponse.objects.filter(
            user=request.user,
            question__survey=current_survey
        ).delete()

        for q in questions:
            val = request.POST.get(f'question_{q.id}')
            if val and val.isdigit():
                SurveyResponse.objects.create(
                    user=request.user,
                    question=q,
                    answer_value=int(val)
                )

        mbti_type = calculate_financial_mbti(request.user, current_survey)
        request.user.mbti_type = mbti_type
        request.user.mbti_test_date = timezone.now()
        request.user.save()

        return redirect('mbti:result')

    return render(request, 'survey.html', {
        'survey': current_survey,
        'questions': questions,
    })


@login_required
def result(request):
    if not request.user.mbti_type:
        return redirect('mbti:survey')

    mbti_type = request.user.mbti_type

    # OpenAI + hybrid 추천 실행
    financial_recs = recommend_for_user(request.user, top_n=5)

    # 템플릿으로 넘길 형태로 가공
    recommendations = []
    for rec in financial_recs:
        prod     = rec['product']
        provider = rec['provider']
        title    = rec['title']
        score    = rec['score']
        reason   = rec['reason']

        # 상품 상세 URL
        if isinstance(prod, DepositProduct):
            link = reverse('savings:deposit_detail', args=[prod.id])
            desc = f"가입 방법: {prod.join_way}, 우대조건: {prod.spcl_cnd}, 한도: {prod.max_limit}"
        else:
            link = reverse('savings:annuity_detail', args=[prod.id])
            desc = (
                f"유형: {prod.prdt_type_nm}, "
                f"평균수익률: {prod.avg_prft_rate}%, "
                f"판매 시작일: {prod.sale_strt_day.strftime('%Y-%m-%d')}"
            )

        recommendations.append({
            'name': title,
            'provider': provider,
            'description': desc,
            'link': link,
            'score': score,
            'reason': reason,
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
        'mbti_type': mbti_type,
        'recommendations': recommendations,
        'similar_users_count': similar_users_count,
        'popular_posts': popular_posts,
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
        'mbti_type': mbti_type,
        'recommendations': recs,
    })


def personality_types(request):
    types = PersonalityType.objects.all()
    return render(request, 'types.html', {'types': types})


def personality_type_detail(request, type_code):
    mbti_type = get_object_or_404(PersonalityType, type_code=type_code)
    recs = Recommendation.objects.filter(personality_type=mbti_type)
    users_count = mbti_type.users.count()
    return render(request, 'type_detail.html', {
        'mbti_type': mbti_type,
        'recommendations': recs,
        'users_count': users_count,
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
            user=user,
            question_id=r['question'],
            answer_value=r['answer']
        )
    mbti_type = calculate_financial_mbti(user, Survey.objects.get(id=data['survey']))
    user.mbti_type = mbti_type
    user.save()
    return Response({'status': 'success', 'mbti_type': mbti_type.type_code})


def fetch_deposit_products():
    url = 'https://finlife.fss.or.kr/finlifeapi/v1/fdrmDpstApi/list.json'
    params = {
        'auth': settings.FINLIFE_API_KEY,
        'topFinGrpNo': '020000',
        'pageNo': 1,
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.json()['result']


def main_page(request):
    return render(request, 'main.html')
