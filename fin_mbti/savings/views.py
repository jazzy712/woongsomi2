# savings/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import DepositProduct
from django.contrib.auth.decorators import login_required
import pandas as pd
from datetime import datetime
import os
import requests
from django.conf import settings
from .services import recommend_for_user

def deposit_list(request):
    products = DepositProduct.objects.all().order_by('-created_at')
    return render(request, 'savings/deposit_list.html', {'products': products})

def deposit_detail(request, pk):
    product = get_object_or_404(DepositProduct, pk=pk)
    return render(request, 'savings/deposit_detail.html', {'product': product})

@login_required
def subscribe_deposit(request, pk):
    product = get_object_or_404(DepositProduct, pk=pk)
    user = request.user

    if user.joined_products:
        if product.name not in user.joined_products:
            user.joined_products += f",{product.name}"
    else:
        user.joined_products = product.name
    user.save()
    
    return redirect('savings:deposit_detail', pk=pk)

def spot_prices_page(request):
    return render(request, 'savings/gold_silver.html')

def get_spot_data(request, metal):
    # 날짜 필터 받기
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if not start_date or not end_date:
        return JsonResponse({'error': 'Invalid date range'}, status=400)

    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')

    # 경로 설정
    if metal == 'gold':
        filepath = os.path.join(settings.BASE_DIR, 'savings', 'excel', 'Gold_prices.xlsx')
    elif metal == 'silver':
        filepath = os.path.join(settings.BASE_DIR, 'savings', 'excel', 'Silver_prices.xlsx')
    else:
        return JsonResponse({'error': 'Invalid metal type'}, status=400)

    # 파일 읽기
    try:
        df = pd.read_excel(filepath, engine='openpyxl')
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    # 날짜와 종가 열 추출 및 정제
    df = df[['Date', 'Close/Last']]
    df['Date'] = pd.to_datetime(df['Date'])

    # --- 쉼표 제거 및 숫자 변환 처리 ---
    # "1,967.10" 같은 문자열에서 ','를 없애고 float로 변환
    df['Close/Last'] = (
        df['Close/Last']
        .astype(str)
        .str.replace(',', '', regex=False)
    )
    df['Close/Last'] = pd.to_numeric(df['Close/Last'], errors='coerce')
    

    df = df[(df['Date'] >= start) & (df['Date'] <= end)].sort_values(by='Date')

    # 응답 형태 구성
    data = {
        'dates': df['Date'].dt.strftime('%Y-%m-%d').tolist(),
        'prices': df['Close/Last'].astype(float).tolist(),
    }

    return JsonResponse(data)

def video_search_page(request):
    """검색창이 있는 HTML 페이지 렌더링"""
    return render(request, 'savings/video_search.html')


def youtube_search_api(request):
    q = request.GET.get('q')
    if not q:
        return JsonResponse({'error':'no query'}, status=400)
    api_key = settings.YOUTUBE_API_KEY
    url = 'https://www.googleapis.com/youtube/v3/search'
    params = {
      'part': 'snippet',
      'q': q,
      'type': 'video',
      'maxResults': 9,
      'key': api_key,
    }
    resp = requests.get(url, params=params)
    data = resp.json()
    return JsonResponse(data)

def bank_search_page(request):
    # 템플릿에 JS 키만 넘겨 줍니다
    return render(request, 'savings/bank_search.html', {
        'KAKAO_JS_KEY': settings.KAKAO_JS_KEY
    })

def banks_search_api(request):
    q = request.GET.get('q')
    if not q:
        return JsonResponse({'error': 'no query'}, status=400)

    url = 'https://dapi.kakao.com/v2/local/search/address.json'
    headers = {'Authorization': f'KakaoAK {settings.KAKAO_REST_KEY}'}
    resp = requests.get(url, params={'query': q}, headers=headers)
    return JsonResponse(resp.json())

@login_required
def recommendations_view(request):
    recommendations = recommend_for_user(request.user, top_n=5)
    return render(request, 'savings/recommendations.html', {
        'recommendations': recommendations
    })