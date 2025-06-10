import pandas as pd

# CSV 로드
df = pd.read_csv('정리된_정기예금_API_버전.csv')

# 1금융권 기준 (인터넷 전문은행 포함)
tier1_banks = [
    '국민은행', '신한은행', '우리은행', '하나은행', '농협은행주식회사',
    '중소기업은행', '수협은행', '한국산업은행', '한국스탠다드차타드은행',
    '주식회사 카카오뱅크', '주식회사 케이뱅크', '토스뱅크 주식회사', '아이엠뱅크'
]

# 2금융권 기준 (명칭에 '저축은행' 또는 '상호저축은행' 포함시 2금융권 처리)
tier2_keywords = ['저축은행', '상호저축은행']

# 금융권 구분 함수
def classify_bank(bank_name):
    if bank_name in tier1_banks:
        return '1금융권'
    elif any(keyword in bank_name for keyword in tier2_keywords):
        return '2금융권'
    else:
        return '기타'

# 금융권 구분 컬럼 생성
df['금융권'] = df['금융회사명'].apply(classify_bank)

# 기타를 1금융권으로 강제 변경
df['금융권'] = df['금융권'].replace('기타', '1금융권')

# 데이터 나누기
df_tier1 = df[df['금융권'] == '1금융권']
df_tier2 = df[df['금융권'] == '2금융권']

# CSV 저장
df_tier1.to_csv('예금_1금융권_포함.csv', index=False, encoding='utf-8-sig')
df_tier2.to_csv('예금_2금융권.csv', index=False, encoding='utf-8-sig')

print(f' 저장 완료: 1금융권({df_tier1.shape[0]}건), 2금융권({df_tier2.shape[0]}건)')
