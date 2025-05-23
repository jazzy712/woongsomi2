import requests
from datetime import datetime
from django.conf import settings

from .models import (
    FinancialCompany,
    CompanyBranch,
    DepositProduct,
    AnnuityProduct,
)
from .recommendation import hybrid_recommend

BASE_URL = 'https://finlife.fss.or.kr/finlifeapi'


def sync_companies(top_fin_grp_no: str, page_no: int = 1):
    """금융회사 목록 & 지점 정보 동기화"""
    url = f'{BASE_URL}/companySearch.json'
    params = {
        'auth': settings.FINLIFE_API_KEY,
        'topFinGrpNo': top_fin_grp_no,
        'pageNo': page_no,
    }
    r = requests.get(url, params=params)
    data = r.json().get('result', {})

    # 1) 회사 기본정보
    for info in data.get('baseList', []):
        FinancialCompany.objects.update_or_create(
            fin_co_no=info['fin_co_no'],
            defaults={
                'kor_co_nm': info['kor_co_nm'],
                'homp_url': info.get('homp_url'),
                'cal_tel': info.get('cal_tel'),
                'dcls_chrg_man': info.get('dcls_chrg_man'),
            }
        )

    # 2) 지점 옵션
    for opt in data.get('optionList', []):
        comp = FinancialCompany.objects.get(fin_co_no=opt['fin_co_no'])
        CompanyBranch.objects.update_or_create(
            company=comp,
            area_cd=opt['area_cd'],
            defaults={
                'area_nm': opt['area_nm'],
                'exis_yn': (opt['exis_yn'] == 'Y'),
            }
        )

    # 3) 다음 페이지
    now = int(data.get('now_page_no', 1))
    maxp = int(data.get('max_page_no', 1))
    if now < maxp:
        sync_companies(top_fin_grp_no, page_no + 1)


def sync_deposit_products(top_fin_grp_no: str, page_no: int = 1):
    """정기예금 상품 동기화"""
    url = f'{BASE_URL}/savingProductsSearch.json'
    params = {
        'auth': settings.FINLIFE_API_KEY,
        'topFinGrpNo': top_fin_grp_no,
        'pageNo': page_no,
    }
    r = requests.get(url, params=params)
    data = r.json().get('result', {})

    for item in data.get('products', []):
        base = item['baseinfo']
        comp = FinancialCompany.objects.filter(fin_co_no=base['fin_co_no']).first()
        DepositProduct.objects.update_or_create(
            fin_prdt_cd=base['fin_prdt_cd'],
            defaults={
                'fin_co': comp,
                'name':        base.get('fin_prdt_nm'),
                'bank':        base.get('kor_co_nm'),
                'join_way':    base.get('join_way'),
                'intr_rate':   float(base.get('intr_rate') or 0),
                'intr_rate2':  float(base.get('intr_rate2') or 0),
                # ... 나머지 필드도 필요에 따라 매핑 ...
            }
        )

    now = int(data.get('now_page_no', 1))
    maxp = int(data.get('max_page_no', 1))
    if now < maxp:
        sync_deposit_products(top_fin_grp_no, page_no + 1)


def sync_annuity_products(top_fin_grp_no: str, page_no: int = 1):
    """연금저축 상품 동기화"""
    url = f'{BASE_URL}/annuitySavingProductsSearch.json'
    params = {
        'auth': settings.FINLIFE_API_KEY,
        'topFinGrpNo': top_fin_grp_no,
        'pageNo': page_no,
    }
    r = requests.get(url, params=params)
    data = r.json().get('result', {})

    for item in data.get('products', []):
        base = item['baseinfo']
        comp = FinancialCompany.objects.filter(fin_co_no=base['fin_co_no']).first()
        AnnuityProduct.objects.update_or_create(
            fin_prdt_cd=base['fin_prdt_cd'],
            defaults={
                'fin_co':       comp,
                'fin_prdt_nm':  base.get('fin_prdt_nm'),
                'avg_prft_rate': float(base.get('dcls_rate') or 0),
                'prdt_type_nm': base.get('prdt_type_nm'),
                'sale_strt_day': datetime.strptime(base['sale_strt_day'], '%Y%m%d').date()
                                  if base.get('sale_strt_day') else None,
                # ... 나머지 필드 매핑 ...
            }
        )

    now = int(data.get('now_page_no', 1))
    maxp = int(data.get('max_page_no', 1))
    if now < maxp:
        sync_annuity_products(top_fin_grp_no, page_no + 1)



def get_all_products_for_mbti(mbti_code: str) -> list[dict]:
    """
    MBTI 코드는 GPT 추천 프롬프트에만 쓰이므로,
    여기서는 DepositProduct와 AnnuityProduct를
    [{'id','provider','title','avg_rate'}, …] 형태로 반환합니다.
    """
    candidates = []

    # ── 예금 상품 (DepositProduct) ──
    for prod in DepositProduct.objects.all():
        candidates.append({
            'id':       prod.id,
            'provider': prod.bank,   # 은행명: bank 필드 사용
            'title':    prod.name,   # 상품명: name 필드 사용
            'avg_rate': 0,           # TODO: prod.options를 순회해 평균 금리를 계산
        })

    # ── 연금저축 상품 (AnnuityProduct) ──
    for prod in AnnuityProduct.objects.all():
        candidates.append({
            'id':       prod.id,
            'provider': prod.fin_co.kor_co_nm if prod.fin_co else '',
            'title':    prod.fin_prdt_nm,
            'avg_rate': prod.avg_prft_rate or 0,
        })

    return candidates


def recommend_for_user(user, top_n: int = 5) -> list[dict]:
    """
    1) 후보군 만들고
    2) hybrid_recommend 로 점수·이유 받아서
    3) 실제 model 인스턴스와 합쳐 반환
    """
    candidates = get_all_products_for_mbti(user.mbti_type.type_code)
    recs = hybrid_recommend(user.mbti_type.type_code, candidates, top_n)

    results = []
    for rec in recs:
        idx  = rec['index']
        data = candidates[idx]
        prod = (
            DepositProduct.objects.filter(pk=data['id']).first()
            or AnnuityProduct.objects.filter(pk=data['id']).first()
        )
        if not prod:
            continue

        results.append({
            'product':  prod,
            'provider': data['provider'],
            'title':    data['title'],
            'score':    rec['score'],
            'reason':   rec['reason'],
        })

    return results
