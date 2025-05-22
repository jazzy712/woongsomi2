# savings/management/commands/fetch_deposit_products.py

import requests
from django.core.management.base import BaseCommand
from savings.models import DepositProduct
from django.conf import settings

class Command(BaseCommand):
    help = '예금 상품 정보를 금융감독원 오픈 API에서 가져와 저장합니다.'

    def handle(self, *args, **kwargs):
        API_KEY = settings.FINLIFE_API_KEY  # 실제 키로 교체하거나 settings.py에서 불러오기
        url = f'https://finlife.fss.or.kr/finlifeapi/depositProductsSearch.json?auth={API_KEY}&topFinGrpNo=020000&pageNo=1'

        response = requests.get(url)
        if response.status_code != 200:
            self.stdout.write(self.style.ERROR('API 요청 실패'))
            return

        data = response.json()

        base_list = data.get('result', {}).get('baseList', [])
        for item in base_list:
            DepositProduct.objects.update_or_create(
                fin_prdt_cd=item['fin_prdt_cd'],
                defaults={
                    'name': item['fin_prdt_nm'],
                    'bank': item['kor_co_nm'],
                    'join_way': item['join_way'],
                }
            )

        self.stdout.write(self.style.SUCCESS(f'{len(base_list)}개의 예금 상품을 저장했습니다.'))
