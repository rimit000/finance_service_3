from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import pandas as pd
import time

# ✅ 크롬드라이버 경로
driver_path = "C:/Users/kdp/Downloads/chromedriver-win64/chromedriver.exe"
service = Service(driver_path)
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=service, options=options)

# 결과 저장 리스트
data = []

# 1 ~ 5 페이지 반복
for page in range(1, 6):
    print(f"📄 {page}페이지 수집 중...")
    url = f"https://search.naver.com/search.naver?query=주택담보대출&sm=tab_pge&where=nexearch&start={(page-1)*10 + 1}"
    driver.get(url)
    time.sleep(3)

    cards = driver.find_elements(By.CSS_SELECTOR, "div.card_item.deposit_type")

    for card in cards:
        try:
            bank = card.find_element(By.CSS_SELECTOR, "strong.this_text").text.strip()
        except:
            bank = ""

        try:
            # 상품명: "상품\n상품명\n금리\nx.xx~x.xx%" 형식에서 상품명만 추출
            char_info = card.find_element(By.CSS_SELECTOR, "div.character_info").text.split("\n")
            product = ""
            for line in char_info:
                if "상품" not in line and "금리" not in line and "~" not in line:
                    product = line.strip()
        except:
            product = ""

        try:
            # 금리: 가장 마지막에 있는 "~%" 포함한 줄만 추출
            full_text = card.text
            rate = next((line for line in full_text.split("\n") if "~" in line and "%" in line), "")
        except:
            rate = ""

        try:
            # 대출한도는 '최대', '제한', '상환' 같은 키워드 포함한 줄들만 추출
            lines = card.text.split("\n")
            limit_lines = [line for line in lines if any(k in line for k in ["최대", "제한", "가능", "우대", "상환"])]
            limit = " ".join(limit_lines).strip()
        except:
            limit = ""

        data.append({
            "은행명": bank,
            "상품명": product,
            "금리": rate,
            "대출한도": limit
        })

# 브라우저 종료
driver.quit()

# 빈 행 제거
df = pd.DataFrame(data)
df = df[df["은행명"] != ""]

# CSV 저장
df.to_csv("주택담보대출_상품_정제완료.csv", index=False, encoding='utf-8-sig')
print("✅ CSV 저장 완료!")
