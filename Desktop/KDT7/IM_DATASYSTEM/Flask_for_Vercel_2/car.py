import time
import re
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service

# ✅ 크롬드라이버 경로
driver_path = "C:/Users/kdp/Downloads/chromedriver-win64/chromedriver.exe"
service = Service(driver_path)
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=service, options=options)

# ✅ 차량 목록
car_list = [
    {"type": "경차", "name": "레이"},
    {"type": "경차", "name": "캐스퍼"},
    {"type": "경차", "name": "모닝"},
    {"type": "세단", "name": "기아 K3"},
    {"type": "세단", "name": "현대 쏘나타"},
    {"type": "세단", "name": "현대 아반떼"},
    {"type": "소형 SUV", "name": "기아 셀토스"},
    {"type": "소형 SUV", "name": "현대 코나"},
    {"type": "소형 SUV", "name": "르노코리아 XM3"},
]

results = []

# ✅ 차량별 네이버 검색 → 연식+가격대 추출
for car in car_list:
    query = f"{car['name']} 중고차 가격"
    print(f"🚗 {car['name']} 검색 중...")

    driver.get(f"https://search.naver.com/search.naver?query={query}")
    time.sleep(5)

    # 연식별 시세 정보 추출
    items = driver.find_elements(By.CSS_SELECTOR, "div.cycle_list_wrap._cycle_list li")

    for item in items:
        text = item.text.strip()
        match = re.search(r"(20\d{2})년식\s+([\d,]+)~([\d,]+)만원", text)
        if match:
            year = match.group(1)
            low = int(match.group(2).replace(",", ""))
            high = int(match.group(3).replace(",", ""))
            avg = (low + high) // 2
            results.append([car["type"], car["name"], year, f"{low}~{high}만원", avg])
            print(f"  ✅ {year}년 | {low}~{high}만원 → 평균: {avg}만원")

# ✅ CSV 저장
csv_filename = "naver_car_prices.csv"
with open(csv_filename, mode="w", encoding="utf-8-sig", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["차종", "모델명", "연식", "가격대", "평균가"])
    writer.writerows(results)

driver.quit()
print(f"\n✅ 저장 완료: {csv_filename}")
