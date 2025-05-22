from django.db.models import Count
from .models import SurveyResponse, PersonalityType
import logging

logger = logging.getLogger(__name__)

def calculate_financial_mbti(user, survey):
    """
    사용자 설문 결과 기반 MBTI 유형 계산
    - 'investment' 카테고리를 'info'와 동일하게 취급함
    """
    try:
        responses = SurveyResponse.objects.filter(
            user=user,
            question__survey=survey
        ).select_related('question')

        category_data = {
            'risk': {'total': 0, 'count': 0},
            'consumption': {'total': 0, 'count': 0},
            'info': {'total': 0, 'count': 0},
            'goal': {'total': 0, 'count': 0}
        }

        thresholds = {
            'risk': 3.0,
            'consumption': 3.0,
            'info': 3.0,
            'goal': 3.0
        }

        mbti_map = {
            'risk': lambda avg: 'R' if avg > thresholds['risk'] else 'S',
            'consumption': lambda avg: 'I' if avg > thresholds['consumption'] else 'P',
            'info': lambda avg: 'N' if avg > thresholds['info'] else 'T',
            'goal': lambda avg: 'D' if avg > thresholds['goal'] else 'L',
        }

        for res in responses:
            cat = res.question.category
            if cat in ['info', 'analysis', 'investment']:
                category_data['info']['total'] += res.answer_value
                category_data['info']['count'] += 1
            elif cat in category_data:
                category_data[cat]['total'] += res.answer_value
                category_data[cat]['count'] += 1

        # 디버깅 출력
        print("[DEBUG] 사용자:", user.username)
        print("[DEBUG] 설문 ID:", survey.id)
        print("[DEBUG] 응답 수:", responses.count())
        for cat in category_data:
            total = category_data[cat]['total']
            count = category_data[cat]['count']
            avg = total / count if count > 0 else 3
            print(f" - {cat}: 총합={total}, 개수={count}, 평균={avg:.2f}")

        type_code = []
        for cat in ['risk', 'consumption', 'info', 'goal']:
            data = category_data[cat]
            avg = data['total'] / data['count'] if data['count'] > 0 else 3.0
            type_code.append(mbti_map[cat](avg))

        final_code = ''.join(type_code)
        logger.info(f"[계산 완료] 사용자: {user.username}, 코드: {final_code}")

        return PersonalityType.objects.get(type_code=final_code)

    except PersonalityType.DoesNotExist:
        logger.warning(f"[유형 없음] 사용자: {user.username}, 반환코드: {final_code}")
        return PersonalityType.objects.first()

    except Exception as e:
        logger.critical(f"[계산 실패] 사용자: {user.username}, 오류: {str(e)}")
        return PersonalityType.objects.first()
