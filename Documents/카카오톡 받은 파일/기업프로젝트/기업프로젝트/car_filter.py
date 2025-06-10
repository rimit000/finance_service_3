import pandas as pd

# CSV 파일 불러오기
df = pd.read_csv("naver_car_prices.csv")

# 데이터 확인
print(df.head())
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.font_manager as fm
plt.rc('font', family='Malgun Gothic')

# 시각화를 위해 차량명 + 연식으로 그룹핑
df["모델+연식"] = df["모델명"] + " " + df["연식"].astype(str)

# 그래프 설정
plt.figure(figsize=(12, 6))
sns.barplot(x="모델+연식", y="평균가", hue="차종", data=df)
plt.xticks(rotation=45, ha="right")
plt.title("차량별 연식에 따른 평균 중고차 가격")
plt.ylabel("평균가 (만원)")
plt.xlabel("모델 + 연식")
plt.tight_layout()
plt.show()
