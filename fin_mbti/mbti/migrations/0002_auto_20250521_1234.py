from django.db import migrations

def create_default_survey(apps, schema_editor):
    Survey = apps.get_model('mbti', 'Survey')
    SurveyQuestion = apps.get_model('mbti', 'SurveyQuestion')
    
    # 기본 설문 생성
    survey = Survey.objects.create(
        title="2025 금융 성향 진단 설문",
        description="나의 금융 MBTI를 알아보는 기본 설문입니다."
    )
    
    # 설문 문항 추가 (예시 10개)
    questions = [
        ("나는 지출 계획을 세우고 소비하는 편이다", "consumption"),
        ("높은 수익을 위해 위험을 감수할 수 있다", "risk"),
        ("매달 저축을 꾸준히 한다", "goal"),
        ("투자 정보를 꼼꼼히 분석한다", "analysis"),
        ("단기 수익보다 장기 성장을 선호한다", "goal"),
        ("충동적인 소비를 자주 한다", "consumption"),
        ("금융 상품 선택 시 전문가 조언을 따른다", "analysis"),
        ("예산을 초과하는 경우가 많다", "consumption"),
        ("변동성이 큰 상품을 피한다", "risk"),
        ("5년 이상의 장기 계획을 세운다", "goal")
    ]
    
    for idx, (text, category) in enumerate(questions):
        SurveyQuestion.objects.create(
            survey=survey,
            question_text=f"{idx+1}. {text}",
            category=category,
            order=idx+1
        )

class Migration(migrations.Migration):
    dependencies = [
        ('mbti', '0001_initial'),
    ]
    operations = [
        migrations.RunPython(create_default_survey),
    ]
