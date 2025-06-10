import pandas as pd

# 원본 정부 대출 상품 로드
df = pd.read_csv('정부대출상품_정리.csv')

# ✔ 필요한 컬럼 정리 및 이름 변경
# 존재하지 않는 컬럼 보완
expected_columns = {
    '금융회사명': '금융회사명',
    '상품명': '상품명',
    '최저금리': '기본금리(%)',
    '대출한도': '대출한도',
    '상환방식': '만기이자',
    '가입대상': '가입대상',
    '대출기간': '저축기간(개월)'
}

for col in expected_columns.values():
    if col not in df.columns:
        df[col] = '정보없음'

# ✔ 컬럼명 표준화
df = df.rename(columns={
    '최저금리': '기본금리(%)',
    '상환방식': '만기이자',
    '대출기간': '저축기간(개월)'
})

# ✔ 불필요 컬럼 제거 (필요 컬럼만 유지)
df = df[list(expected_columns.values())]

# ✔ 누락/결측 처리
df = df.dropna(subset=['금융회사명', '상품명'])
df = df.fillna('정보없음')

# ✔ 최종 CSV 저장
df.to_csv('대출상품_전체_최저금리기준_정리.csv', index=False, encoding='utf-8-sig')

print("✅ 정부대출상품 기반 '대출상품_전체_최저금리기준_정리.csv' 저장 완료")
