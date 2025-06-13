import pandas as pd
import re

# 🔽 ① 엑셀 또는 CSV 파일 불러오기 (파일명에 맞게 수정)
# df = pd.read_excel("주택담보대출_raw.xlsx")  # 엑셀인 경우
df = pd.read_csv("주택담보대출.csv")      # CSV인 경우

# 🔽 ② 빈 값이거나 페이지 없는 행 제거
df = df.dropna(subset=["페이지", "은행명", "상품명", "금리"]).copy()

# 🔽 ③ 상품명/금리 정제 함수 정의
def clean_product(text):
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if '상품' in line and i + 1 < len(lines):
            return lines[i + 1].strip()
    return ""

def clean_rate(text):
    match = re.search(r"\d+\.\d+\s*~\s*\d+\.\d+%|\d+\.\d+%", text)
    return match.group(0) if match else ""

# 🔽 ④ 적용
df['상품명'] = df['금리'].apply(clean_product)
df['금리'] = df['금리'].apply(clean_rate)

# 🔽 ⑤ 최종 정리된 파일 저장
df = df[["페이지", "은행명", "상품명", "금리", "대출한도"]]  # 컬럼 순서 정리
df.to_excel("주택담보대출_정리본.xlsx", index=False)

print("✅ 정리 완료! → '주택담보대출_정리본.xlsx'")
