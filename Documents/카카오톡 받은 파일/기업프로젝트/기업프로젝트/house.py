import pandas as pd

# 1) 오피스텔 보증금 데이터 로드 (전체 구분만)
apt = pd.read_csv(
    '오피스텔 보증금가격.csv',
    skiprows=[1, 2],           # 상위 헤더 2줄 건너뛰기
    encoding='cp949',          # 파일 인코딩
    usecols=[1, 2, 3, 4],      # 필요한 열만 선택 (권역, 시도, 구분, 2025년 4월)
    dtype=str
)
apt.columns = ['권역', '시도', '구분', '가격']
# '전체' 구분 행만 남기기
apt = apt[apt['구분'] == '전체'].copy()
# 숫자형으로 변환
apt['가격'] = apt['가격'].str.replace(r'[^0-9]', '', regex=True).astype(int)
# 시도별로 인덱스 설정
apt_result = apt.set_index('시도')[['가격']]

# 2) 주택 보증금 데이터 로드
house = pd.read_csv(
    '주택 보증금가격.csv',
    skiprows=[1, 2],           # 상위 헤더 2줄 건너뛰기
    encoding='cp949',
    usecols=[0, 3],            # 시도, 2025년 4월 열만 선택
    dtype=str
)
house.columns = ['시도', '가격']
house['가격'] = house['가격'].str.replace(r'[^0-9]', '', regex=True).astype(int)
house_result = house.set_index('시도')
apt_result.to_csv('오피스텔_시도별_보증금.csv', encoding='utf-8-sig')
house_result.to_csv('주택_시도별_보증금.csv', encoding='utf-8-sig')
# 3) 결과 출력
print("=== 오피스텔 시도별 보증금 (전체) ===")
print(apt_result)
print("\n=== 주택 시도별 보증금 ===")
print(house_result)
print("오피스텔_시도별_보증금.csv")
print("주택_시도별_보증금.csv")