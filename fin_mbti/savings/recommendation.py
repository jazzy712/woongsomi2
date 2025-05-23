import json
import re
from openai import OpenAI 
from django.conf import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def hybrid_recommend(mbti_code: str, candidates: list[dict], top_n: int = 5) -> list[dict]:
    """
    MBTI 코드와 candidates 리스트를 GPT에 넘겨,
    top_n개의 index/score/reason을 JSON 배열로 돌려받습니다.
    candidates 요소 예시:
      {'id': 12, 'provider': '우리은행', 'title': 'OO 정기예금', 'avg_rate': 2.1}
    """
    # 1) 후보 상품을 텍스트로 직렬화
    lines = []
    for i, prod in enumerate(candidates):
        lines.append(
            f"{i}. {prod['title']} (회사: {prod['provider']}, 평균이율: {prod.get('avg_rate', 'N/A')}%)"
        )
    products_str = "\n".join(lines)

    # 2) 프롬프트 조합
    prompt = (
        f"사용자 MBTI: {mbti_code}\n"
        f"다음은 후보 금융상품 목록입니다:\n{products_str}\n\n"
        f"이 중 상위 {top_n}개를 점수(0~10)와 간단한 이유와 함께 JSON 배열로 추천해주세요.\n"
        "각 요소는 {\"index\": 목록번호, \"score\": 점수, \"reason\": 이유} 형태여야 합니다."
    )

    # 3) OpenAI ChatCompletion 새 인터페이스 호출
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "당신은 금융상품 전문가 추천 엔진입니다."},
            {"role": "user",   "content": prompt},
        ],
        temperature=0,
    )
    # 새 인터페이스도 choices[0].message.content 형태로 동일하게 접근합니다
    text = resp.choices[0].message.content

    # 4) JSON 파싱 (기존 코드 그대로)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"```json\s*(\{.+?\}|\[.+?\])\s*```", text, re.S)
        if m:
            return json.loads(m.group(1))
        raise
