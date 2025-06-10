import requests

params = {
    "apiType": "json",
    "authKey": "cff37d5c55297a5bf3a395c72b63e707",
    "fncEngnCode": "1",          # 금융감독원
    "eduTrgtCntnt": "Y",         # 청년기
    "eduMthdCode": "1",          # 온라인 학습
    "eduLrgClsfcCntnt": "200",   # 자산관리
    "pageIndex": 1,
    "pageRow": 100
}

r = requests.get("https://www.fss.or.kr/edu/openApi/api/eduProgram.jsp", params=params)
if r.headers.get('Content-Type') == 'application/json':
    try:
        js = r.json()
        print(f"✅ 응답 데이터 수: {len(js.get('list', []))}")
    except Exception as e:
        print("⚠ JSON 파싱 중 예외:", str(e))
else:
    print("❌ JSON이 아닌 응답입니다. 내용:")
    print(r.text[:500])