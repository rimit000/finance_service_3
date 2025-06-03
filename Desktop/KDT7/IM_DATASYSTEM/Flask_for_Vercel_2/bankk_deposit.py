import requests
import pandas as pd
import time
from tqdm import tqdm
from urllib.parse import quote

#  인증키와 API 설정
AUTH_KEY = quote("a355601851b9873cfad9438ad4325ce4")  # URL 인코딩 처리
BASE_URL = "http://finlife.fss.or.kr/finlifeapi/depositProductsSearch.json"
GROUP_CODES = ["020000", "030300"]  # 은행, 저축은행

#  1. 전체 페이지 수 확인
def get_max_page(auth_key, group_code):
    params = {
        "auth": auth_key,
        "topFinGrpNo": group_code,
        "pageNo": 1
    }
    res = requests.get(BASE_URL, params=params)
    print(f"응답 상태 코드({group_code}):", res.status_code)
    if res.status_code != 200:
        print(" 요청 실패")
        return 0
    try:
        data = res.json()
        return int(data["result"]["max_page_no"])
    except Exception as e:
        print(" 응답 파싱 실패:", e)
        print("응답 내용:", res.text[:300])
        return 0

#  2. 전체 정기예금 상품 수집
def collect_deposit_products(auth_key, group_code):
    all_products = []
    max_page = get_max_page(auth_key, group_code)

    for page in tqdm(range(1, max_page + 1), desc=f"[{group_code}] 전체 페이지 수집 중"):
        params = {
            "auth": auth_key,
            "topFinGrpNo": group_code,
            "pageNo": page
        }
        res = requests.get(BASE_URL, params=params)
        if res.status_code != 200:
            print(f"[경고] {page}페이지 응답 실패")
            continue
        try:
            data = res.json()
        except Exception as e:
            print(f"[에러] {page}페이지 JSON 파싱 실패:", e)
            continue

        base_list = data["result"].get("baseList", [])
        option_list = data["result"].get("optionList", [])

        for base in base_list:
            matched_options = [opt for opt in option_list if opt["fin_prdt_cd"] == base["fin_prdt_cd"]]
            for opt in matched_options:
                product = base.copy()
                product.update(opt)
                all_products.append(product)

        time.sleep(0.1)  # 과도한 요청 방지

    return pd.DataFrame(all_products)

#  3. 실행 및 저장
if __name__ == "__main__":
    all_data = pd.DataFrame()
    for code in GROUP_CODES:
        df = collect_deposit_products(AUTH_KEY, code)
        all_data = pd.concat([all_data, df], ignore_index=True)

    all_data.to_csv("정기예금_상품정보_API.csv", index=False, encoding="utf-8-sig")
    print(f" 저장 완료! 총 {len(all_data)}개 상품 수집됨.")
