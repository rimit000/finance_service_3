from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd

# 1. Selenium 브라우저 열기
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
url = 'https://www.gov.kr/portal/onestopSvc/lonGoods#searchList'
driver.get(url)

# 2. 페이지 로딩 대기
try:
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.lc3_finance_product_list > li'))
    )
except:
    print("페이지 로딩 실패")

# 3. BeautifulSoup 파싱
soup = BeautifulSoup(driver.page_source, 'html.parser')

# 4. 상품 리스트 추출
products = soup.select('ul.lc3_finance_product_list > li')

# 5. 데이터 저장용 리스트
data_list = []

for product in products:
    # 상품명
    title = product.select_one('.lc3_logo_tit_wrap .tit')
    # 금리
    rate = product.select_one('span[id^=inrstP]')
    # 한도
    limit = product.select_one('span[id^=lonLmtP]')
    # 대출기간
    period = product.select_one('span[id^=totLonPdP]')
    # 대상 (텍스트 기준으로 '대상' 찾기)
    target_block = product.select_one('.finance_product_detail_list')
    target = None
    if target_block:
        target_li = target_block.select('li')
        for li in target_li:
            if '대상' in li.text:
                target = li.select_one('p.txt').get_text(strip=True)

    data = {
        '상품명': title.get_text(strip=True) if title else '없음',
        '금리': rate.get_text(strip=True) if rate else '없음',
        '최대한도': limit.get_text(strip=True) if limit else '없음',
        '대출기간': period.get_text(strip=True) if period else '없음',
        '대상': target if target else '없음'
    }

    data_list.append(data)

# 6. DataFrame 변환 및 출력
df = pd.DataFrame(data_list)
print(df)

# 7. 엑셀 저장
df.to_excel('정부지원대출_상품목록.xlsx', index=False)

# 8. 브라우저 닫기
driver.quit()
