# savings/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import DepositProduct, AnnuityProduct
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.dateparse import parse_date
from django.urls import reverse as url_reverse
import pandas as pd
from datetime import datetime
import os
import requests, operator
from django.conf import settings
from .services import recommend_for_user, sync_companies, sync_deposit_products, sync_annuity_products
from itertools import groupby
import pandas as pd


def deposit_list(request):
    # DB에 예·적금 상품이 하나도 없으면 한 번만 동기화
    if DepositProduct.objects.count() == 0:
        groups = ['020000','030300','030900','040000','055000','060000']
        for grp in groups:
            sync_companies(top_fin_grp_no=grp)
            sync_deposit_products(top_fin_grp_no=grp)

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
    """
    템플릿에 Kakao JS API key 전달
    """
    return render(request, 'savings/bank_search.html', {
        'KAKAO_JS_KEY': settings.KAKAO_JS_KEY
    })


def banks_search_api(request):
    """
    GET parameters:
      - province: 시/도 이름 (예: '서울특별시')
      - district: 구/군/시 이름 (예: '강남구')
      - bank_name: 검색할 은행명 (기본 '은행')

    1) 시/도+구 조합으로 주소 검색 → 위경도 취득
    2) 취득한 위경도 기준으로 은행 키워드 검색 (반경 5km, 거리순)
    3) Kakao Local API 응답을 그대로 JSON 반환
    """
    prov      = request.GET.get('province')
    dist      = request.GET.get('district')
    bank_name = request.GET.get('bank_name', '은행')

    if not prov or not dist:
        return JsonResponse(
            {'error': 'province and district are required'}, 
            status=400
        )

    headers = {'Authorization': f'KakaoAK {settings.KAKAO_REST_KEY}'}
    region  = f"{prov} {dist}"

    # 1) 주소 → 위경도
    addr_url  = 'https://dapi.kakao.com/v2/local/search/address.json'
    addr_resp = requests.get(addr_url, params={'query': region}, headers=headers)
    if addr_resp.status_code != 200:
        return JsonResponse(
            {'error': 'failed to geocode region'},
            status=addr_resp.status_code
        )
    addr_data = addr_resp.json().get('documents', [])
    if not addr_data:
        return JsonResponse(
            {'error': f'could not find coordinates for "{region}"'},
            status=404
        )

    # 첫 번째 매칭 결과 사용
    longitude = addr_data[0]['x']
    latitude  = addr_data[0]['y']

    # 2) 은행 키워드 검색
    kw_url    = 'https://dapi.kakao.com/v2/local/search/keyword.json'
    params    = {
        'query':  bank_name,
        'x':      longitude,
        'y':      latitude,
        'radius': 5000,
        'sort':   'distance',
        'size':   15
    }
    kw_resp = requests.get(kw_url, params=params, headers=headers)

    # 3) 결과 반환
    return JsonResponse(kw_resp.json(), status=kw_resp.status_code)

@login_required
def recommendations_view(request):
    recommendations = recommend_for_user(request.user, top_n=5)
    return render(request, 'savings/recommendations.html', {
        'recommendations': recommendations
    })

def compare_deposits(request):
    # 정렬 기준 & 방향
    sort_by = request.GET.get('sort',  'interest')    # interest|period|limit
    order   = request.GET.get('order', 'desc')        # asc|desc
    is_desc = (order == 'desc')                       # Boolean

    items = []

    # --- 예·적금 데이터 수집 ---
    for p in DepositProduct.objects.all():
        try:
            rate = float(p.mtrt_int)
        except (TypeError, ValueError):
            rate = 0.0
        items.append({
            'category':   '예·적금',
            'bank':       p.bank,
            'name':       p.name,
            'join_way':   p.join_way,
            'interest':   rate,
            'period':     p.save_trm or 0,
            'limit':      p.max_limit or 0,
            'detail_url': url_reverse('savings:deposit_detail', args=[p.pk]),
        })

    # --- 연금저축 데이터 수집 ---
    for p in AnnuityProduct.objects.all():
        try:
            rate = float(getattr(p, 'avg_prft_rate', 0.0))
        except (TypeError, ValueError):
            rate = 0.0
        items.append({
            'category':   '연금저축',
            'bank':       p.bank,
            'name':       p.name,
            'join_way':   getattr(p, 'join_way', ''),
            'interest':   rate,
            'period':     getattr(p, 'save_trm', 0) or 0,
            'limit':      getattr(p, 'max_limit', 0) or 0,
            'detail_url': url_reverse('savings:annuity_detail', args=[p.pk]),
        })

    # 정렬 적용
    items.sort(key=lambda x: x.get(sort_by, 0), reverse=is_desc)

    # 카테고리별 그룹화
    grouped = {
        cat: list(group)
        for cat, group in groupby(items, key=lambda x: x['category'])
    }

    return render(request, 'savings/compare_deposits.html', {
        'grouped': grouped,
        'sort_by': sort_by,
        'order':   order,
    })

@require_POST
@staff_member_required
def finlife_sync(request):
    """
    POST 요청 시(관리자만) FinLife API로
    회사·예·적금·연금 데이터를 동기화하고 JSON 응답을 반환합니다.
    """
    groups = ['020000','030300','030900','040000','055000','060000']
    for grp in groups:
        sync_companies(top_fin_grp_no=grp)
        sync_deposit_products(top_fin_grp_no=grp)
        sync_annuity_products(top_fin_grp_no=grp)
    return JsonResponse({
        'status': 'success',
        'synced_groups': groups,
    })