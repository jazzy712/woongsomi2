from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Count
from .services import calculate_financial_mbti
import requests
from django.conf import settings

from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import (
    Survey, SurveyQuestion, SurveyResponse, 
    PersonalityType, FinancialProduct, 
    Recommendation, UserShare
)
from .serializers import (
    SurveyQuestionSerializer,
)

from boards.models import Board

@login_required
def survey(request):
    # 최신 설문을 가져오거나 404
    current_survey = get_object_or_404(Survey, pk=1)  # pk=1 번 설문을 사용 중이라면 1, 
    # 아니면 Survey.objects.latest('created_at') 로 변경 가능
    questions = SurveyQuestion.objects.filter(survey=current_survey).order_by('order')
    
    if not questions.exists():
        return render(request, 'error.html', {
            'message': '등록된 설문 문항이 없습니다. 관리자에게 문의하세요.'
        })

    if request.method == 'POST':
        # 기존 응답 전부 삭제
        SurveyResponse.objects.filter(
            user=request.user,
            question__survey=current_survey
        ).delete()
        
        # 새 응답 생성
        for question in questions:
            val = request.POST.get(f'question_{question.id}')
            if val and val.isdigit():
                SurveyResponse.objects.create(
                    user=request.user,
                    question=question,
                    answer_value=int(val)
                )

        # 유형 계산 및 저장
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
    recommendations = Recommendation.objects.filter(personality_type=mbti_type)[:5]
    similar_users_count = request.user._meta.model.objects.filter(mbti_type=mbti_type).count()

    popular_posts = Board.objects.filter(
        author__mbti_type=mbti_type
    ).annotate(comment_count=Count('comments')).order_by('-comment_count')[:3]

    context = {
        'mbti_type': mbti_type,
        'recommendations': recommendations,
        'similar_users_count': similar_users_count,
        'popular_posts': popular_posts,
    }
    return render(request, 'result.html', context)


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
    recommendations = Recommendation.objects.filter(personality_type=mbti_type)

    context = {'mbti_type': mbti_type, 'recommendations': recommendations}
    return render(request, 'recommendations.html', context)


def personality_types(request):
    types = PersonalityType.objects.all()
    return render(request, 'types.html', {'types': types})


def personality_type_detail(request, type_code):
    mbti_type = get_object_or_404(PersonalityType, type_code=type_code)
    recommendations = Recommendation.objects.filter(personality_type=mbti_type)
    users_count = mbti_type.users.count()

    context = {
        'mbti_type': mbti_type,
        'recommendations': recommendations,
        'users_count': users_count,
    }
    return render(request, 'type_detail.html', context)


@api_view(['GET'])
def api_questions(request):
    survey_id = request.GET.get('survey')
    questions = SurveyQuestion.objects.filter(survey=survey_id).order_by('order')
    serializer = SurveyQuestionSerializer(questions, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def api_submit_responses(request):
    user = request.user
    data = request.data

    SurveyResponse.objects.filter(user=user, question__survey=data['survey']).delete()

    for response in data['responses']:
        SurveyResponse.objects.create(
            user=user,
            question_id=response['question'],
            answer_value=response['answer']
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
    data = resp.json()
    return data['result']


def main_page(request):
    return render(request, 'main.html')