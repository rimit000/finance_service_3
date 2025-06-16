from flask import Flask, render_template, request, jsonify, redirect
import pandas as pd
import random
import re
from urllib.parse import unquote
import logging
import os
from flask import make_response
app = Flask(__name__)

# ============================================
# 1. 공통 유틸 – 은행 로고 경로 -----------------------------------
# ============================================
LOGO_DIR = "bank_logos"          # static/bank_logos/ 하위 폴더명

def _slug(bank_name: str) -> str:
    """공백‧괄호 제거 → 파일명 슬러그"""
    return re.sub(r"[\s()]+", "", str(bank_name))

def logo_filename(bank_name):
    filename = bank_logo_map.get(bank_name)
    return f"bank_logos/{filename}" if filename else "bank_logos/default.png"

# ✔ 예금/적금 데이터 로드
try:
    deposit_tier1 = pd.read_csv('예금_1금융권_포함.csv')
    deposit_tier2 = pd.read_csv('예금_2금융권.csv')
    savings_tier1 = pd.read_csv('적금_1금융권_포함.csv')
    savings_tier2 = pd.read_csv('적금_2금융권.csv')
    print("✅ CSV 파일 로드 성공")
except Exception as e:
    print(f"❌ CSV 파일 로드 실패: {e}")
    # 빈 DataFrame으로 초기화
    deposit_tier1 = pd.DataFrame()
    deposit_tier2 = pd.DataFrame()
    savings_tier1 = pd.DataFrame()
    savings_tier2 = pd.DataFrame()

# 안전한 unique 리스트 생성
def safe_get_unique(df, column):
    try:
        if not df.empty and column in df.columns:
            return sorted(df[column].dropna().unique())
        return []
    except:
        return []

tier1_list = sorted(set(
    safe_get_unique(deposit_tier1, '금융회사명') + 
    safe_get_unique(savings_tier1, '금융회사명')
))
tier2_list = sorted(set(
    safe_get_unique(deposit_tier2, '금융회사명') + 
    safe_get_unique(savings_tier2, '금융회사명')
))

# ✔ 지역 컬럼 매핑 추가
def normalize_name(name):
    try:
        s = str(name)
        s = re.sub(r'[㈜\s\-()]', '', s)  # 괄호, 공백, 하이픈 제거
        s = s.replace('저축은행', '').replace('은행', '').lower()
        return s
    except:
        return str(name)

region_map_raw = {
    # 1금융권
    '국민은행':'서울','신한은행':'서울','우리은행':'서울','하나은행':'서울','농협은행':'서울',
    'SC제일은행':'서울','씨티은행':'서울','카카오뱅크':'경기','케이뱅크':'서울','토스뱅크':'서울',
    '아이엠은행':'대구','부산은행':'부산','경남은행':'경남','광주은행':'광주','전북은행':'전북','제주은행':'제주',
    # 2금융권 저축은행
    'BNK저축은행':'부산','CK저축은행':'강원','DH저축은행':'부산','HB저축은행':'서울',
    'IBK저축은행':'서울','JT저축은행':'서울','JT친애저축은행':'서울','KB저축은행':'서울',
    'MS저축은행':'서울','OK저축은행':'서울','OSB저축은행':'서울','SBI저축은행':'서울',
    '고려저축은행':'부산','국제저축은행':'부산','금화저축은행':'경기','남양저축은행':'경기',
    '다올저축은행':'서울','대명상호저축은행':'대구','대백저축은행':'대구','대신저축은행':'부산',
    '대아상호저축은행':'부산','대원저축은행':'부산','대한저축은행':'서울','더블저축은행':'서울',
    '더케이저축은행':'서울','동양저축은행':'서울','동원제일저축은행':'부산','드림저축은행':'대구',
    '디비저축은행':'서울','라온저축은행':'대전','머스트삼일저축은행':'서울','모아저축은행':'인천',
    '민국저축은행':'경기','바로저축은행':'서울','부림저축은행':'부산','삼정저축은행':'부산',
    '삼호저축은행':'서울','상상인저축은행':'서울','상상인플러스저축은행':'서울','세람저축은행':'전북',
    '센트럴저축은행':'서울','솔브레인저축은행':'대전','스마트저축은행':'광주','스카이저축은행':'서울',
    '스타저축은행':'서울','신한저축은행':'서울','아산저축은행':'충남','안국저축은행':'서울',
    '안양저축은행':'경기','애큐온저축은행':'서울','에스앤티저축은행':'경남','엔에이치저축은행':'서울',
    '영진저축은행':'대구','예가람저축은행':'서울','오성저축은행':'경기','오투저축은행':'서울',
    '우리금융저축은행':'서울','우리저축은행':'서울','웰컴저축은행':'서울','유니온저축은행':'서울',
    '유안타저축은행':'서울','융창저축은행':'서울','인성저축은행':'부산','인천저축은행':'인천',
    '조은저축은행':'광주','조흥저축은행':'서울','진주저축은행':'경남','참저축은행':'대전',
    '청주저축은행':'충북','키움예스저축은행':'서울','키움저축은행':'서울','페퍼저축은행':'서울',
    '평택저축은행':'경기','푸른저축은행':'서울','하나저축은행':'서울','한국투자저축은행':'서울',
    '한성저축은행':'서울','한화저축은행':'서울','흥국저축은행':'서울'
}
region_map = {normalize_name(k): v for k, v in region_map_raw.items()}

# 로고 매핑 딕셔너리 생성
try:
    logo_df = pd.read_csv('logo_bank.csv')
    bank_logo_map = dict(zip(logo_df['은행명'], logo_df['로고파일명']))
    print("✅ 로고 매핑 로드 성공")
except Exception as e:
    print(f"❌ 로고 매핑 로드 실패: {e}")
    bank_logo_map = {}

# 안전한 컬럼 추가 함수
def safe_add_columns(df, df_name):
    try:
        print(f"{df_name} 처리 시작")
        
        if df.empty:
            print(f"{df_name}이 비어있습니다")
            return
            
        print(f"{df_name} 컬럼:", df.columns.tolist())
        
        if '금융회사명' in df.columns:
            df['정제명'] = df['금융회사명'].apply(normalize_name)
            df['지역'] = df['정제명'].map(region_map).fillna('기타')
            df['logo'] = df['금융회사명'].apply(logo_filename)
            print(f"{df_name} 컬럼 추가 완료")
        else:
            print(f"{df_name}에 금융회사명 컬럼이 없습니다")
            df['지역'] = '기타'
            df['logo'] = 'default.png'
    except Exception as e:
        print(f"{df_name} 처리 중 오류: {e}")
        if not df.empty:
            df['지역'] = '기타'
            df['logo'] = 'default.png'

# 각 데이터프레임에 안전하게 컬럼 추가
safe_add_columns(deposit_tier1, "deposit_tier1")
safe_add_columns(deposit_tier2, "deposit_tier2") 
safe_add_columns(savings_tier1, "savings_tier1")
safe_add_columns(savings_tier2, "savings_tier2")

def clean_loan_data(file):
    try:
        df = pd.read_csv(file)
        df = df.rename(columns=lambda x: x.strip())
        df = df.rename(columns={
            '금리': '최저 금리(%)',
            '한도': '대출한도',
            '상환 방식': '상환 방식',  
            '가입 대상': '가입대상',
            '만기이자': '만기이자',
            '저축기간(개월)': '저축기간(개월)'
        })
        required = ['금융회사명', '상품명', '최저 금리(%)', '대출한도', '상환 방식', '가입대상', '저축기간(개월)', '만기이자']
        for c in required:
            if c not in df:
                df[c] = '정보 없음'
        df.dropna(subset=['금융회사명', '상품명'], inplace=True)
        df.fillna('정보 없음', inplace=True)
        return df
    except Exception as e:
        print(f"대출 데이터 정리 오류: {e}")
        return pd.DataFrame()

# 대출 파일 목록
loan_files = [
    '새희망홀씨_정리완료.csv',
    '소액_비상금대출_정리완료.csv',
    '무직자대출_정리완료.csv',
    '사잇돌_정리완료.csv',
    '햇살론_정제완료_v3.csv'
]

# 수창 버전의 데이터 전처리 방식 적용
try:
    loan_data = pd.concat(
        [clean_loan_data(f) for f in loan_files if os.path.exists(f)], 
        ignore_index=True
    )
    print("✅ 대출 데이터 로드 성공")
except Exception as e:
    print(f"❌ 대출 데이터 로드 실패: {e}")
    loan_data = pd.DataFrame()

def classify_loan_type(name):
    """상품명을 기반으로 대출유형을 분류합니다."""
    try:
        if pd.isna(name):
            return '기타'
        
        name = str(name).lower()
        
        # 특수문자 제거 전에 먼저 햇살론_ 체크
        if '햇살론_' in name:
            return '햇살론'
        
        # 비상금대출 키워드 확장
        if any(keyword in name for keyword in ['비상금', '소액대출', '간편대출', '스피드대출', '여성비상금', 'fi비상금', 'fi 비상금']):
            return '비상금대출'
        
        # 무직자대출 키워드 확장 (순서 중요!)
        if any(keyword in name for keyword in ['신용대출', '대환대출', '카드대출', '가계신용대출', '위풍', '뉴플랜', '참신한']):
            return '무직자대출'
        
        # 특수문자 제거
        name_clean = re.sub(r'[^가-힣a-z0-9]', '', name)
        
        if '새희망홀씨' in name_clean:
            return '새희망홀씨'
        elif '사잇돌' in name_clean:
            return '사잇돌'
        elif '햇살' in name_clean or '햇살론' in name_clean:
            return '햇살론'
        # 추가 비상금대출 키워드 (특수문자 제거 후)
        elif any(keyword in name_clean for keyword in ['비상금', '소액대출', '간편대출', '스피드대출', '여성비상금', 'fi비상금']):
            return '비상금대출'
        # 추가 무직자대출 키워드 (특수문자 제거 후)
        elif any(keyword in name_clean for keyword in ['신용대출', '대환대출', '카드대출', '가계신용대출', '위풍', '뉴플랜', '참신한']):
            return '무직자대출'
        # 접근 경로나 정보 없음은 무시
        elif name_clean in ['모바일인터넷영업점', '모바일웹app', '정보없음']:
            return '기타'
        else:
            # 디버깅을 위해 분류되지 않은 상품명 출력
            print(f"분류 실패: '{name}' -> 기타")
            return '기타'
    except:
        return '기타'

# 상품명 기반으로 대출유형 분류
if not loan_data.empty:
    loan_data['대출유형'] = loan_data['상품명'].apply(classify_loan_type)

    # 컬럼명 매핑 추가
    # dtype 오류 방지를 위해 먼저 object로 변환
    loan_data['최저 금리(%)'] = loan_data['최저 금리(%)'].astype(str)
    loan_data['금리'] = loan_data['최저 금리(%)'] + '%'  # 금리에 % 추가
    loan_data['금융권'] = loan_data['금융회사명'].apply(lambda x: '1금융권' if any(bank in str(x) for bank in ['은행', 'KB', '신한', '우리', 'SC', 'BNK', '부산', 'iM뱅크']) else '2금융권')
    loan_data['대출조건'] = loan_data.get('상환 방식', '정보 없음')  # 대출조건은 상환방식으로
    loan_data['상환방법'] = loan_data.get('상환 방식', '정보 없음')
    loan_data['대출기간'] = loan_data.get('저축기간(개월)', '정보 없음')
    loan_data['가입대상'] = loan_data.get('가입대상', '정보 없음')  # 가입대상은 그대로

    # 기존 logo 설정
    loan_data["logo"] = loan_data["금융회사명"].apply(logo_filename)

    # 분류 결과 확인 (디버깅용)
    print("✔ 대출유형 분포:")
    print(loan_data['대출유형'].value_counts())

# 메인 대출 페이지 라우트
@app.route('/loans')
def loans_page():
    breadcrumb = [{'name': '홈', 'url': '/'}, {'name': '대출', 'current': True}]
    selected_types = request.args.getlist('loanType')
    input_amount = request.args.get('amount', type=int)
    max_limit = request.args.get('maxLimit', type=int)  # 

    if loan_data.empty:
        return render_template('loans_list.html', ...)

    df = loan_data.copy()
    df['상품유형'] = df['대출유형']

    if input_amount:
        def compute_total(row):
            try:
                rate = float(str(row['최저 금리(%)']).replace('%', '').strip()) / 100
                return int(input_amount * (1 + rate))
            except:
                return None
        df['계산금액'] = df.apply(compute_total, axis=1)
    else:
        df['계산금액'] = None

    # ✅ 최대한도 숫자화
    def parse_loan_limit(val):
        try:
            val = str(val).replace(',', '').replace(' ', '')
            if '억원' in val:
                return int(float(val.replace('억원', '')) * 10000)
            elif '천만원' in val:
                return int(float(val.replace('천만원', '')) * 1000)
            elif '백만원' in val:
                return int(float(val.replace('백만원', '')) * 100)
            elif '만원' in val:
                return int(float(val.replace('만원', '')))
            else:
                return int(val)
        except:
            return 0
    df['한도정수'] = df['대출한도'].apply(parse_loan_limit)

    if max_limit:
        df = df[df['한도정수'] >= max_limit]  

    if selected_types and '전체' not in selected_types:
        filtered_df = df[df['상품유형'].isin(selected_types)]
    else:
        filtered_df = df

    # 페이지네이션
    page = request.args.get('page', 1, type=int)
    page_size = 15
    start = (page - 1) * page_size
    end = start + page_size
    total_pages = (len(filtered_df) + page_size - 1) // page_size

    return render_template(
        'loans_list.html',
        breadcrumb=breadcrumb,
        products=filtered_df.iloc[start:end].to_dict('records'),
        selected_types=selected_types,
        input_amount=input_amount,
        current_page=page,
        total_pages=total_pages,
        product_type='대출',
        product_type_url='loans',
        max_limit=max_limit  
    )


# 동림 버전의 API 엔드포인트
@app.route('/api/loans')
def api_loans():
    try:
        loan_type = request.args.get('loanType', '전체')
        amount    = request.args.get('amount', type=int, default=1000000)

        if loan_data.empty:
            return jsonify(products=[])

        df = loan_data.copy()
        
        if loan_type != '전체':
            df = df[df['대출유형'] == loan_type]
        # 전체 조회 시 모든 상품 포함

        # (금액이 있으면 계산금액 컬럼 추가)
        if amount:
            rate_series = (
                df['최저 금리(%)']
                  .astype(str).str.replace('%','').str.strip().astype(float) / 100
            )
            df['계산금액'] = (amount * (1 + rate_series)).round().astype(int)

        # 필요하면 정렬·페이지네이션도 여기서 처리
        return jsonify(products=df.to_dict('records'))
    except Exception as e:
        print(f"대출 API 오류: {e}")
        return jsonify(products=[])

# 금융용어사전 로드 및 초성 기준
try:
    terms_df = pd.read_excel('통계용어사전.xlsx')
    print("✅ 금융용어사전 로드 성공")
except Exception as e:
    print(f"❌ 금융용어사전 로드 실패: {e}")
    terms_df = pd.DataFrame(columns=['용어', '설명'])

def get_initial_consonant(word):
    try:
        if not word: return ''
        c = word[0]
        if '가' <= c <= '힣':
            cho=['ㄱ','ㄲ','ㄴ','ㄷ','ㄸ','ㄹ','ㅁ','ㅂ','ㅃ','ㅅ','ㅆ','ㅇ','ㅈ','ㅉ','ㅊ','ㅋ','ㅌ','ㅍ','ㅎ']
            return cho[(ord(c)-ord('가'))//588]
        return 'A-Z' if re.match(r'[A-Za-z]', c) else c
    except:
        return ''

if not terms_df.empty:
    terms_df['초성'] = terms_df['용어'].apply(get_initial_consonant)

try:
    car_df = pd.read_csv('naver_car_prices.csv')
    print("✅ 자동차 가격 데이터 로드 성공")
except Exception as e:
    print(f"❌ 자동차 가격 데이터 로드 실패: {e}")
    car_df = pd.DataFrame()

# 필터 유틸 함수
def filter_products(df, period, bank, region):
    try:
        if period:
            df = df[df['저축기간(개월)'] == int(period)]
        if bank:
            keys = bank.split('|')
            df = df[df['금융회사명'].isin(keys)]
        if region and '지역' in df.columns:
            df = df[df['지역'] == region]
        return df
    except Exception as e:
        print(f"필터 처리 오류: {e}")
        return df

# ✔ 홈 (브레드크럼 없음)
@app.route('/')
def home():
    return render_template('home_menu.html')

# ✔ 예금 라우트
@app.route('/deposits')
def deposits_page():
    breadcrumb = [
        {'name': '홈', 'url': '/'},
        {'name': '예금', 'current': True}
    ]
    
    try:
        periods = sorted(pd.concat([deposit_tier1, deposit_tier2])['저축기간(개월)'].unique())
    except:
        periods = [6, 12, 24, 36]
    
    try:
        banks = {
            '1금융권': sorted(deposit_tier1['금융회사명'].unique()),
            '2금융권': sorted(deposit_tier2['금융회사명'].unique())
        }
    except:
        banks = {'1금융권': [], '2금융권': []}
    
    # 지역은 일단 고정값으로 처리
    regions = ['서울', '부산', '대구', '인천', '광주', '대전', '울산', '경기', '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주', '기타']
    
    return render_template('filter_page.html',
                           breadcrumb=breadcrumb, 
                           product_type='예금', 
                           product_type_url='deposits', 
                           periods=periods, 
                           banks=banks, 
                           regions=regions)

@app.route('/deposits/detail/<bank>/<product_name>')
def deposits_detail(bank, product_name):
    bank = unquote(bank)
    product_name = unquote(product_name)
    
    breadcrumb = [
        {'name': '홈', 'url': '/'},
        {'name': '예금', 'url': '/deposits'},
        {'name': f'{bank} {product_name}', 'current': True}
    ]

    try:
        df = pd.concat([deposit_tier1, deposit_tier2])
        matched = df[(df['상품명'] == product_name) & (df['금융회사명'] == bank)]

        if matched.empty:
            return "상품을 찾을 수 없습니다.", 404

        prod = matched.iloc[0]
        return render_template('product_detail.html',
                               breadcrumb=breadcrumb, 
                               product=prod, 
                               product_type='예금', 
                               product_type_url='deposits')
    except Exception as e:
        print(f"예금 상세 페이지 오류: {e}")
        return "오류가 발생했습니다.", 500

@app.route('/api/deposits')
def api_deposits():
    try:
        period = request.args.get('period')
        bank = request.args.get('bank')
        region = request.args.get('region')

        data = pd.concat([deposit_tier1, deposit_tier2], ignore_index=True)
        filtered = filter_products(data, period, bank, region)

        # 중복 제거: 상품명 + 금융회사명 기준
        filtered = filtered.drop_duplicates(subset=['상품명', '금융회사명'])

        products = filtered.sort_values(by='최고우대금리(%)', ascending=False).to_dict('records')
        return jsonify({'products': products, 'total': len(products)})
    except Exception as e:
        print(f"예금 API 오류: {e}")
        return jsonify({'products': [], 'total': 0})

# ✔ 적금 라우트
@app.route('/savings')
def savings_page():
    breadcrumb = [
        {'name': '홈', 'url': '/'},
        {'name': '적금', 'current': True}
    ]
    
    try:
        periods = sorted(pd.concat([savings_tier1, savings_tier2])['저축기간(개월)'].unique())
    except:
        periods = [6, 12, 24, 36]
    
    try:
        banks = {
            '1금융권': sorted(savings_tier1['금융회사명'].unique()),
            '2금융권': sorted(savings_tier2['금융회사명'].unique())
        }
    except:
        banks = {'1금융권': [], '2금융권': []}
    
    # 지역은 일단 고정값으로 처리
    regions = ['서울', '부산', '대구', '인천', '광주', '대전', '울산', '경기', '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주', '기타']
    
    return render_template('filter_page.html',
                           breadcrumb=breadcrumb, 
                           product_type='적금', 
                           product_type_url='savings', 
                           periods=periods, 
                           banks=banks, 
                           regions=regions)

@app.route('/savings/detail/<bank>/<product_name>')
def savings_detail(bank, product_name):
    bank = unquote(bank)
    product_name = unquote(product_name)
    
    breadcrumb = [
        {'name': '홈', 'url': '/'},
        {'name': '적금', 'url': '/savings'},
        {'name': f'{bank} {product_name}', 'current': True}
    ]

    try:
        df = pd.concat([savings_tier1, savings_tier2])
        matched = df[(df['상품명'] == product_name) & (df['금융회사명'] == bank)]

        if matched.empty:
            return "상품을 찾을 수 없습니다.", 404

        prod = matched.iloc[0]
        return render_template('product_detail.html',
                               breadcrumb=breadcrumb, 
                               product=prod, 
                               product_type='적금', 
                               product_type_url='savings')
    except Exception as e:
        print(f"적금 상세 페이지 오류: {e}")
        return "오류가 발생했습니다.", 500

@app.route('/api/savings')
def api_savings():
    try:
        period = request.args.get('period')
        bank = request.args.get('bank')
        region = request.args.get('region')

        print("적금 요청 - 기간:", period, "| 은행:", bank, "| 지역:", region)

        data = pd.concat([savings_tier1, savings_tier2], ignore_index=True)
        print("전체 적금 상품 수:", len(data))

        filtered = filter_products(data, period, bank, region)
        print("필터 후 적금 수:", len(filtered))

        filtered = filtered.drop_duplicates(subset=['상품명', '금융회사명'])

        # NaN 처리 필수!
        filtered = filtered.fillna("정보 없음")

        products = filtered.sort_values(by='최고우대금리(%)', ascending=False).to_dict('records')
        return jsonify({'products': products, 'total': len(products)})
    except Exception as e:
        print(f"적금 API 오류: {e}")
        return jsonify({'products': [], 'total': 0})

@app.route('/loans/detail/<product_name>')
def loans_detail(product_name):
    breadcrumb = [
        {'name': '홈', 'url': '/'},
        {'name': '대출', 'url': '/loans'},
        {'name': product_name, 'current': True}
    ]
    try:
        if loan_data.empty:
            return "대출 데이터가 없습니다.", 404
        prod = loan_data[loan_data['상품명'] == product_name].iloc[0]
        return render_template('product_detail.html',
                               breadcrumb=breadcrumb, 
                               product=prod, 
                               product_type='대출', 
                               product_type_url='loans')
    except Exception as e:
        print(f"대출 상세 페이지 오류: {e}")
        return "대출 상품을 찾을 수 없습니다.", 404

@app.route('/api/product_detail/<product_type>/<product_key>')
def api_product_detail(product_type, product_key):
    try:
        product_key = unquote(product_key)
        product_name, bank_name = product_key.split('--')

        # 데이터프레임 선택
        if product_type == 'deposits':
            df = pd.concat([deposit_tier1, deposit_tier2])
        elif product_type == 'savings':
            df = pd.concat([savings_tier1, savings_tier2])
        elif product_type == 'loans':
            df = loan_data
        else:
            return "잘못된 product_type입니다.", 400

        # 상품 검색
        matched = df[(df['상품명'] == product_name) & (df['금융회사명'] == bank_name)]
        if matched.empty:
            return "상품을 찾을 수 없습니다.", 404

        product = matched.iloc[0]
        return render_template('product_modal.html', product=product, product_type=product_type)
    except Exception as e:
        print(f"상품 상세 API 오류: {e}")
        return "오류가 발생했습니다.", 500

@app.route('/savings/page/<int:page>')
def savings_page_list(page):
    breadcrumb = [
        {'name': '홈', 'url': '/'},
        {'name': '적금', 'url': '/savings'},
        {'name': f'{page}페이지', 'current': True}
    ]
    
    try:
        page_size = 15
        df = pd.concat([savings_tier1, savings_tier2], ignore_index=True)
        total_products = len(df)
        total_pages = (total_products + page_size - 1) // page_size
        start = (page - 1) * page_size
        end = start + page_size

        page_products = df.iloc[start:end].to_dict('records')
        return render_template(
            'products_list.html',
            breadcrumb=breadcrumb,
            product_type='적금',
            product_type_url='savings',
            products=page_products,
            current_page=page,
            total_pages=total_pages
        )
    except Exception as e:
        print(f"적금 페이지 리스트 오류: {e}")
        return render_template(
            'products_list.html',
            breadcrumb=breadcrumb,
            product_type='적금',
            product_type_url='savings',
            products=[],
            current_page=page,
            total_pages=1
        )

@app.route('/deposits/page/<int:page>')
def deposits_page_list(page):
    breadcrumb = [
        {'name': '홈', 'url': '/'},
        {'name': '예금', 'url': '/deposits'},
        {'name': f'{page}페이지', 'current': True}
    ]
    
    try:
        page_size = 15
        df = pd.concat([deposit_tier1, deposit_tier2], ignore_index=True)
        total_products = len(df)
        total_pages = (total_products + page_size - 1) // page_size
        start = (page - 1) * page_size
        end = start + page_size

        page_products = df.iloc[start:end].to_dict('records')
        return render_template(
            'products_list.html',
            breadcrumb=breadcrumb,
            product_type='예금',
            product_type_url='deposits',
            products=page_products,
            current_page=page,
            total_pages=total_pages
        )
    except Exception as e:
        print(f"예금 페이지 리스트 오류: {e}")
        return render_template(
            'products_list.html',
            breadcrumb=breadcrumb,
            product_type='예금',
            product_type_url='deposits',
            products=[],
            current_page=page,
            total_pages=1
        )

# ✔ 모아플러스 홈
@app.route('/plus')
def plus_home():
    breadcrumb = [
        {'name': '홈', 'url': '/'},
        {'name': 'MOA PLUS', 'current': True}
    ]
    return render_template('plus_home.html', breadcrumb=breadcrumb)

# ✔ 모아플러스 - 금융사전
@app.route('/plus/terms')
def terms_home():
    breadcrumb = [
        {'name': '홈', 'url': '/'},
        {'name': 'MOA PLUS', 'url': '/plus'},
        {'name': '금융, 이제는 쉽고 재미있게', 'current': True}
    ]
    
    try:
        query = request.args.get('query', '').strip()
        initial = request.args.get('initial', '').strip()
        selected = request.args.get('selected', '').strip()
        page = int(request.args.get('page', 1))

        # 필터링 로직을 먼저 처리
        if query:
            filtered = terms_df[terms_df['용어'].str.contains(query, na=False)]
            category = f"검색결과: {query}"
        elif initial:
            filtered = terms_df[terms_df['초성'] == initial]
            category = initial
        else:
            filtered = terms_df.copy()
            category = "전체"

        filtered = filtered[['용어', '설명']].sort_values('용어')
        terms = filtered.to_dict('records')

        # 페이징 처리
        page_size = 15
        total_pages = (len(terms) + page_size - 1) // page_size
        start = (page - 1) * page_size
        end = start + page_size

        # 선택된 용어 처리 - 필터링된 결과에서만 찾기
        selected_term = None
        if selected:
            # 필터링된 terms에서 선택된 용어 찾기
            selected_term = next((t for t in terms if t['용어'] == selected), None)
        
        # 선택된 용어가 없거나 필터링된 결과에 없으면 랜덤 선택
        if not selected_term and terms:
            selected_term = random.choice(terms)
            selected = selected_term['용어']

        categories = sorted(terms_df['초성'].unique()) if not terms_df.empty else []

        return render_template(
            'terms_home.html',
            breadcrumb=breadcrumb,
            categories=categories,
            terms=terms,
            category=category,
            query=query,
            initial=initial,
            selected=selected,
            selected_term=selected_term,
            current_page=page,
            total_pages=total_pages,
            end=end
        )
    except Exception as e:
        print(f"금융용어사전 오류: {e}")
        return render_template(
            'terms_home.html',
            breadcrumb=breadcrumb,
            categories=[],
            terms=[],
            category="전체",
            query="",
            initial="",
            selected="",
            selected_term=None,
            current_page=1,
            total_pages=1,
            end=0
        )

@app.route('/plus/youth')
def plus_youth_policy():
    breadcrumb = [
        {'name': '홈', 'url': '/'},
        {'name': 'MOA PLUS', 'url': '/plus'},
        {'name': '청년 금융, 기회를 잡다', 'current': True}
    ]
    return render_template('youth_policy.html', breadcrumb=breadcrumb)

# 수정된 계산기 라우트 - 가이드 페이지 없이 바로 연결
@app.route('/plus/calculator')
def plus_calculator():
    breadcrumb = [
        {'name': '홈', 'url': '/'},
        {'name': 'MOA PLUS', 'url': '/plus'},
        {'name': '한눈에 비교하기 쉬운 상품', 'url': '/plus/calculator'},
        {'name': '내 상품, 이자 얼MOA?', 'current': True}
    ]
    return render_template('calculator_home.html', breadcrumb=breadcrumb)

@app.route('/plus/region-data')
def region_data():
    try:
        import re  # 정규표현식 사용을 위해 추가
        
        region = request.args.get('region')
        print(f"요청된 지역: {region}")  # 디버깅용
        
        # CSV 파일 읽기
        house_df = pd.read_csv('주택_시도별_보증금.csv')
        
        # 지역별 평균 가격 계산
        avg_prices = house_df.groupby('시도')['가격'].mean().round(0).astype(int).to_dict()
        price = avg_prices.get(region, '정보없음')

        # 주택담보대출 상품 데이터
        loan_products = pd.read_csv('주택담보대출_정리본.csv')
        
        # 금리에서 최소값 추출하여 정렬 (예: "2.88~9.70%" → 2.88)
        def extract_min_rate(rate_str):
            try:
                # "2.88~9.70%" 형태에서 최소값만 추출
                rate = str(rate_str).replace('%', '').split('~')[0]
                return float(rate)
            except:
                return 999  # 파싱 실패시 큰 값으로 설정
        
        loan_products['최소금리'] = loan_products['금리'].apply(extract_min_rate)
        
        # 금리 기준 오름차순 정렬하여 상위 6개 선택
        top_loans = loan_products.sort_values(by='최소금리', ascending=True).head(6)

        product_list = []
        for _, row in top_loans.iterrows():
            # 대출 한도 처리 (문자열에서 숫자 추출)
            limit_str = str(row['대출한도'])
            
            # 대출한도에서 숫자 추출
            def extract_limit_amount(limit_str):
                try:
                    if '억원' in limit_str:
                        # "최대 10억원" → 10억 = 100000만원
                        num = re.findall(r'(\d+(?:\.\d+)?)', limit_str)[0]
                        return int(float(num) * 10000)
                    elif '천만원' in limit_str:
                        # "최대 4억 2천만원" → 42000만원
                        numbers = re.findall(r'(\d+)', limit_str)
                        if len(numbers) >= 2:
                            return int(numbers[0]) * 10000 + int(numbers[1]) * 1000
                        return int(numbers[0]) * 10000
                    elif '만원' in limit_str:
                        num = re.findall(r'(\d+)', limit_str)[0]
                        return int(num)
                    elif '제한없음' in limit_str or '감정가' in limit_str:
                        return 999999  # 매우 큰 값으로 설정
                    else:
                        return 50000  # 기본값 5억
                except:
                    return 50000
            
            max_limit = extract_limit_amount(limit_str)
            
            # 실제 대출 가능 금액 (전세가의 80% 또는 상품 최대 한도 중 작은 값)
            if price != '정보없음':
                loan_limit = min(int(price * 0.8), max_limit)
            else:
                loan_limit = max_limit
                
            product_list.append({
                '상품명': row['상품명'],
                '금융회사명': row['은행명'],
                '금리': row['금리'],
                '대출한도(만원)': loan_limit if loan_limit != 999999 else '제한없음',
                '상품타입': '정부지원' if row['은행명'] == '정부' else '일반'
            })

        return jsonify({'price': price, 'products': product_list})
    except Exception as e:
        print(f"지역 데이터 오류: {e}")
        return jsonify({'price': '정보없음', 'products': []})

@app.template_filter('extract_rate')
def extract_rate(val):
    if isinstance(val, str):
        m = re.search(r'[\d.]+', val)
        return m.group(0) if m else '0'
    return str(val)

# ✔ car-roadmap 라우트에 적금 가입 가능 기간도 추가
@app.route('/plus/car-roadmap')
def car_roadmap():
    breadcrumb = [
        {'name': '홈', 'url': '/'},
        {'name': 'MOA PLUS', 'url': '/plus'},
        {'name': '당신의 미래를 모으는 시간', 'url': '/plus/roadmap'},
        {'name': 'CAR MOA', 'current': True}
    ]
    
    try:
        # 평균가 계산
        grouped = car_df.groupby(['차종', '모델명'])['평균가'].mean().round(0).astype(int).reset_index()

        # 이미지 매핑 딕셔너리
        image_map = {
            'Ray': 'ray.png',
            'Casper': 'kester.png',
            'Morning': 'moring.png',
            'K3': 'kia_k3.png',
            'Avante': 'avante.png',
            'Sonata': 'sonata.png',
            'XM3': 'renault_xm3.png',
            'Kona': 'kona.png',
            'Seltos': 'seltos.png',
        }

        # car_list 구성
        car_list = []
        for _, row in grouped.iterrows():
            name = row['모델명']
            car_list.append({
                '카테고리': row['차종'],
                '모델명': name,
                '평균가격': row['평균가'],
                '이미지파일명': image_map.get(name, 'default.png')
            })

        savings_df = pd.concat([savings_tier1, savings_tier2], ignore_index=True)
        savings_df = savings_df.dropna(subset=['상품명', '금융회사명', '최고우대금리(%)', '저축기간(개월)'])
        savings_df['금리'] = savings_df['최고우대금리(%)'].astype(float)
        savings_df['기간'] = savings_df['저축기간(개월)'].astype(int)
        savings_products = savings_df[['상품명', '금융회사명', '금리', '기간']].drop_duplicates().to_dict('records')
        period_options = sorted(savings_df['기간'].unique().tolist())

        return render_template('car_roadmap.html',
                               breadcrumb=breadcrumb,
                               car_list=car_list,
                               savings_products=savings_products,
                               period_options=period_options)
    except Exception as e:
        print(f"자동차 로드맵 오류: {e}")
        return render_template('car_roadmap.html',
                               breadcrumb=breadcrumb,
                               car_list=[],
                               savings_products=[],
                               period_options=[])

@app.route('/plus/region')
def plus_region_map():
    breadcrumb = [
        {'name': '홈', 'url': '/'},
        {'name': 'MOA PLUS', 'url': '/plus'},
        {'name': '당신의 미래를 모으는 시간', 'url': '/plus/roadmap'},
        {'name': 'HOUSE MOA', 'current': True}
    ]
    return render_template('region_map.html', breadcrumb=breadcrumb)

## ------------------------------------------------------------
## 트립모아 (여행) trip travel 수정본
## ------------------------------------------------------------

CITY_IMAGES = {
    # 일본
    '오사카': 'https://images.unsplash.com/photo-1743242328615-85e551fae33c?q=80&w=1480&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 오사카성
    '교토': 'https://images.unsplash.com/photo-1582752438560-621fcca4da3a?q=80&w=1480&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 후시미 이나리 신사
    
    # 대만
    '타이베이': 'https://plus.unsplash.com/premium_photo-1661963920742-f5b23a6a1b44?q=80&w=1471&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 타이베이 101
    '가오슝': 'https://plus.unsplash.com/premium_photo-1661950064135-5be0fa2d3595?q=80&w=1471&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 가오슝 도시 야경
    '화롄': 'https://images.unsplash.com/photo-1600622249586-63b1e556dd1c?q=80&w=1470&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 타로코 협곡
    
    # 베트남
    '하노이': 'https://plus.unsplash.com/premium_photo-1690960644375-6f2399a08ebc?q=80&w=1332&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 호안끼엠 호수
    '다낭': 'https://images.unsplash.com/photo-1693282815001-0471e68d3bc0?q=80&w=871&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 다낭 해변
    '호치민': 'https://images.unsplash.com/photo-1583417319070-4a69db38a482?q=80&w=870&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 호치민 시내
    '푸꾸옥': 'https://images.unsplash.com/photo-1673093781382-766228925b01?q=80&w=774&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 푸꾸옥 해변
    
    # 태국
    '치앙마이': 'https://images.unsplash.com/photo-1578157695179-d7b7ddeb2f53?q=80&w=1031&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 치앙마이 사원
    '방콕': 'https://images.unsplash.com/photo-1508009603885-50cf7c579365?w=800&q=80',  # 방콕 왕궁
    
    # 말레이시아
    '쿠알라룸푸르': 'https://images.unsplash.com/photo-1596422846543-75c6fc197f07?w=800&q=80',  # 페트로나스 타워
    '조호르바루': 'https://images.unsplash.com/photo-1521317925431-c2256dd4fe2a?q=80&w=774&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 조호르바루 시내
    
    # 싱가포르
    '싱가포르': 'https://images.unsplash.com/photo-1525625293386-3f8f99389edd?w=800&q=80',  # 마리나베이 샌즈
    '센토사': 'https://images.unsplash.com/photo-1650434048812-572363b3a121?q=80&w=774&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 센토사 해변
    
    # 홍콩
    '홍콩': 'https://images.unsplash.com/photo-1536599018102-9f803c140fc1?w=800&q=80',  # 홍콩 야경
    
    # 인도네시아
    '자카르타': 'https://images.unsplash.com/photo-1555899434-94d1368aa7af?q=80&w=870&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 자카르타 스카이라인
    '발리': 'https://images.unsplash.com/photo-1604999333679-b86d54738315?q=80&w=1025&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 발리 우붓 라이스테라스
    
    # 필리핀
    '마닐라': 'https://images.unsplash.com/photo-1556537185-48d80b9596c0?q=80&w=1332&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 마닐라 인트라무로스
    '보라카이': 'https://images.unsplash.com/photo-1495031451303-d8ab59c8df37?q=80&w=1470&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 보라카이 화이트 비치
    '세부': 'https://images.unsplash.com/photo-1637851686615-ba01bfb883f2?q=80&w=1371&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 세부 해변
    
    # 터키
    '이스탄불': 'https://images.unsplash.com/photo-1524231757912-21f4fe3a7200?w=800&q=80',  # 술탄 아흐메드 모스크
    '카파도키아': 'https://images.unsplash.com/photo-1641128324972-af3212f0f6bd?q=80&w=1470&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 카파도키아 열기구
    '안탈리아': 'https://images.unsplash.com/photo-1593238738950-01f243cac6fc?q=80&w=1374&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 안탈리아 해안
    
    ## 북미
    # 미국
    '뉴욕': 'https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=800&q=80',  # 뉴욕 스카이라인
    '샌프란시스코': 'https://images.unsplash.com/photo-1719858403364-83f7442a197e?q=80&w=1470&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 금문교
    '포틀랜드': 'https://plus.unsplash.com/premium_photo-1675122317418-8b7324d93272?q=80&w=1453&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 포틀랜드 다운타운
    
    # 캐나다
    '퀘벡시티': 'https://images.unsplash.com/photo-1600229876145-bf6b400a2c9b?q=80&w=1325&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 퀘벡 구시가지
    '몬트리올': 'https://images.unsplash.com/photo-1470181942237-78ce33fec141?q=80&w=1470&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 몬트리올 구시가지
    
    ## 유럽
    # 스페인
    '바르셀로나': 'https://images.unsplash.com/photo-1539037116277-4db20889f2d4?w=800&q=80',  # 사그라다 파밀리아
    
    # 이탈리아
    '시칠리아': 'https://images.unsplash.com/photo-1523365154888-8a758819b722?q=80&w=1469&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 시칠리아 타오르미나
    '토스카나': 'https://images.unsplash.com/photo-1518098268026-4e89f1a2cd8e?q=80&w=1374&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 토스카나 언덕
    
    # 프랑스
    '파리': 'https://images.unsplash.com/photo-1569949381669-ecf31ae8e613?q=80&w=1470&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 에펠탑
    '리옹': 'https://plus.unsplash.com/premium_photo-1661957705604-15f37be44856?q=80&w=1373&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 리옹 구시가지
    
    # 포르투갈
    '리스본': 'https://images.unsplash.com/photo-1555881400-74d7acaacd8b?w=800&q=80',  # 리스본 전차
    
    # 체코
    '프라하': 'https://images.unsplash.com/photo-1519677100203-a0e668c92439?w=800&q=80',  # 프라하 성
    
    # 조지아
    '트빌리시': 'https://images.unsplash.com/photo-1565008576549-57569a49371d?q=80&w=1558&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 트빌리시 구시가지
    
    ## 오세아니아
    # 호주
    '시드니': 'https://images.unsplash.com/photo-1616128618694-96e9e896ecb7?q=80&w=1290&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 시드니 오페라하우스
    '멜버른': 'https://plus.unsplash.com/premium_photo-1733338816344-1a21444a646f?q=80&w=1374&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 멜버른 플린더스 스트리트
    '골드코스트': 'https://images.unsplash.com/photo-1607309843659-f4ad95cf3277?q=80&w=1471&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 골드코스트 해변
    
    # 뉴질랜드
    '오클랜드': 'https://images.unsplash.com/photo-1693807010837-5d849a65fe00?q=80&w=1470&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 오클랜드 스카이타워
    '퀸스타운': 'https://plus.unsplash.com/premium_photo-1661964091508-b77d484a3003?q=80&w=1332&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 퀸스타운 와카티푸 호수
    '크라이스트처치': 'https://images.unsplash.com/photo-1634348407697-393e5b24a52d?q=80&w=1475&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 크라이스트처치 대성당
    
    ## 남미
    # 브라질
    '리우데자네이루': 'https://images.unsplash.com/photo-1483729558449-99ef09a8c325?w=800&q=80',  # 코르코바도 예수상
    '상파울루': 'https://images.unsplash.com/photo-1696708430962-d303db58fbc6?q=80&w=1470&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 상파울루 시내
    
    # 아르헨티나
    '부에노스아이레스': 'https://plus.unsplash.com/premium_photo-1697729901052-fe8900e24993?q=80&w=1333&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 부에노스아이레스 까미니토
    '바릴로체': 'https://images.unsplash.com/photo-1581836499506-4a660b39478a?w=800&q=80',  # 바릴로체 나우엘 우아피 호수
    
    # 페루
    '리마': 'https://images.unsplash.com/photo-1580530719806-99398637c403?q=80&w=1470&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D0',  # 리마 미라플로레스 해안
    '쿠스코': 'https://images.unsplash.com/photo-1526392060635-9d6019884377?w=800&q=80',  # 쿠스코 마추픽추
    
    # 칠레
    '산티아고': 'https://images.unsplash.com/photo-1597006438013-0f0cca2c1a03?q=80&w=1374&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 산티아고 안데스 산맥
    '발파라이소': 'https://images.unsplash.com/photo-1517956918805-bbacc31d5f81?q=80&w=1477&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 발파라이소 컬러풀한 언덕
    
    # 볼리비아
    '라파스': 'https://images.unsplash.com/photo-1641736047736-020e658328a5?q=80&w=1470&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 라파스 전경
    '우유니': 'https://images.unsplash.com/photo-1529963183134-61a90db47eaf?w=800&q=80',  # 우유니 소금사막
    
    ## 아프리카
    # 남아프리카공화국
    '케이프타운': 'https://images.unsplash.com/photo-1580060839134-75a5edca2e99?w=800&q=80',  # 테이블 마운틴
    '요하네스버그': 'https://images.unsplash.com/photo-1654575998971-4f467c8a89c1?q=80&w=1332&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 요하네스버그 스카이라인
    
    # 케냐
    '나이로비': 'https://images.unsplash.com/photo-1635595358293-03620e36be48?q=80&w=1470&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 나이로비 사파리
    '마사이마라': 'https://images.unsplash.com/photo-1535082623926-b39352a03fb7?q=80&w=1491&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 마사이마라 사파리
    
    # 탄자니아
    '다르에스살람': 'https://images.unsplash.com/photo-1589177900326-900782f88a55?q=80&w=1473&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 다르에스살람 시내
    '아루샤': 'https://images.unsplash.com/photo-1571950484792-c2cbbee9c88b?q=80&w=1374&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 아루샤 킬리만자로
    
    # 이집트
    '카이로': 'https://images.unsplash.com/photo-1670352690010-d39ed2fe465c?q=80&w=1470&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 피라미드
    '룩소르': 'https://images.unsplash.com/photo-1671483331000-5affba8ca1b0?q=80&w=1470&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 룩소르 신전
    
    # 모로코
    '마라케시': 'https://images.unsplash.com/photo-1587974928442-77dc3e0dba72?q=80&w=1524&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 마라케시 마조렐 정원
    '페스': 'https://images.unsplash.com/photo-1553898439-93ac04cfe972?q=80&w=1374&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',  # 페스 메디나
}


# 여행 계획 메인 라우트 (기존 함수 대체)
@app.route('/plus/travel-plan', methods=['GET', 'POST'])
def travel_plan():
    breadcrumb = [
        {'name': '홈', 'url': '/'},
        {'name': 'MOA PLUS', 'url': '/plus'},
        {'name': '당신의 미래를 모으는 시간', 'url': '/plus/roadmap'},
        {'name': 'TRIP MOA', 'current': True}
    ]
    
    try:
        travel_df = pd.read_csv("travel.csv")
        
        # CSV에서 실제 국가 목록 추출
        available_countries = travel_df['국가'].unique().tolist()
        
        # 대륙별 국가 매핑 (GeoJSON의 7개 대륙에 맞춤)
        continent_mapping = {
            'asia': ['일본', '대만', '베트남', '태국', '말레이시아', '싱가포르', '홍콩', '인도네시아', '필리핀', '터키'],
            'europe': ['스페인', '이탈리아', '프랑스', '포르투갈', '체코', '조지아'],
            'oceania': ['호주', '뉴질랜드'],
            'north-america': ['미국', '캐나다'],
            'south-america': ['브라질', '아르헨티나', '페루', '칠레', '볼리비아'],
            'africa': ['남아프리카공화국', '케냐', '탄자니아', '이집트', '모로코']
        }
        
        # GET 요청일 때는 세계지도 기반 페이지 렌더링
        return render_template('travel_worldmap.html', 
                             breadcrumb=breadcrumb, 
                             continent_mapping=continent_mapping,
                             available_countries=available_countries)
    
    except Exception as e:
        print(f"여행 계획 오류: {e}")
        return render_template('travel_worldmap.html', 
                             breadcrumb=breadcrumb, 
                             continent_mapping={},
                             available_countries=[])

# 적금 만기 수령액 계산 함수 (단리)
def calculate_savings_maturity(monthly_amount, months, annual_rate):
    """
    적금 만기 수령액 계산 (단리 방식)
    """
    # 적금 단리 공식: 월납입액 × 납입개월수 × (1 + 연이자율 × (납입개월수 + 1) / 24)
    principal = monthly_amount * months
    interest = monthly_amount * months * (annual_rate / 100) * (months + 1) / 24
    total = principal + interest
    
    # 세후 이자 계산 (일반과세 15.4%)
    tax = interest * 0.154
    after_tax_total = total - tax
    
    return {
        'principal': int(principal),          # 원금
        'interest': int(interest),            # 세전 이자
        'tax': int(tax),                     # 세금
        'total': int(total),                 # 세전 만기수령액
        'after_tax_total': int(after_tax_total)  # 세후 만기수령액
    }

# 새로운 라우트: 여행지 선택 후 저축 기간 선택 페이지
@app.route('/plus/travel-plan/savings', methods=['GET', 'POST'])
def travel_savings_plan():
    breadcrumb = [
        {'name': '홈', 'url': '/'},
        {'name': 'MOA PLUS', 'url': '/plus'},
        {'name': '당신의 미래를 모으는 시간', 'url': '/plus/roadmap'},
        {'name': 'TRIP MOA', 'url': '/plus/travel-plan'},
        {'name': '저축 계획', 'current': True}
    ]
    
    try:
        travel_df = pd.read_csv("travel.csv")
        
        if request.method == 'POST':
            # 2단계: 저축 기간 선택 후 결과 업데이트 (AJAX 응답)
            selected_city = request.form['city']
            months = int(request.form['months'])

            # 선택된 도시의 정보 필터링
            info = travel_df[travel_df['도시'] == selected_city].iloc[0]
            total_cost = int(info['총예상경비'])
            monthly_saving = total_cost // months

            # 추천 적금 상품: 기간 일치 + 금리 높은 순으로 상위 5개
            savings_df = pd.concat([savings_tier1, savings_tier2], ignore_index=True)
            recommended_products = savings_df[savings_df['저축기간(개월)'] == months] \
                .sort_values(by='최고우대금리(%)', ascending=False) \
                .drop_duplicates(subset=['상품명', '금융회사명']) \
                .head(5).to_dict('records')
            
            # JSON 응답으로 적금 상품 정보 반환
            return jsonify({
                'success': True,
                'months': months,
                'monthly_saving': monthly_saving,
                'products': recommended_products
            })
        else:
            # 1단계: 여행지 선택 후 저축 기간 선택 페이지 표시
            selected_city = request.args.get('city')
            
            if not selected_city:
                # 도시가 선택되지 않은 경우 첫 페이지로 리다이렉트
                return redirect(url_for('travel_plan'))
            
            # 선택된 도시의 정보 가져오기
            city_info = travel_df[travel_df['도시'] == selected_city].iloc[0]
            
            travel_info = {
                'city': selected_city,
                'country': city_info['국가'],
                'theme': city_info['테마'],
                'reason': city_info['추천이유'],
                'days': city_info['추천일정'],
                'total_cost': int(city_info['총예상경비']),
                'airfare': int(city_info['예상항공료']),
                'accommodation': int(city_info['숙박비']),
                'food': int(city_info['식비']),
                'image_url': CITY_IMAGES.get(selected_city, 'https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=800&q=80')
            }
            
            # 모든 저축 기간에 대한 추천 적금 상품 미리 계산
            all_products = {}
            savings_df = pd.concat([savings_tier1, savings_tier2], ignore_index=True)
            
            for months in [6, 12, 24, 36]:
                monthly_saving = travel_info['total_cost'] // months
                recommended_products = savings_df[savings_df['저축기간(개월)'] == months] \
                    .sort_values(by='최고우대금리(%)', ascending=False) \
                    .drop_duplicates(subset=['상품명', '금융회사명']) \
                    .head(5).to_dict('records')
                
                # 각 상품에 대해 올바른 적금 계산 추가
                for product in recommended_products:
                    calculation = calculate_savings_maturity(
                        monthly_saving, 
                        months, 
                        float(product['최고우대금리(%)'])
                    )
                    product['calculation'] = calculation
                
                all_products[str(months)] = {
                    'monthly_saving': monthly_saving,
                    'products': recommended_products
                }
            
            return render_template('travel_savings.html',
                                 breadcrumb=breadcrumb,
                                 travel_info=travel_info,
                                 all_products=all_products)
    
    except Exception as e:
        print(f"저축 계획 오류: {e}")
        return redirect(url_for('travel_plan'))
    
    
# 대륙별 국가 정보 API
@app.route('/api/continent/<continent_id>')
def get_continent_countries(continent_id):
    try:
        travel_df = pd.read_csv("travel.csv")
        
        # GeoJSON의 7개 대륙에 맞춘 매핑
        continent_mapping = {
            'asia': ['일본', '대만', '베트남', '태국', '말레이시아', '싱가포르', '홍콩', '인도네시아', '필리핀', '터키'],
            'europe': ['스페인', '이탈리아', '프랑스', '포르투갈', '체코', '조지아'],
            'oceania': ['호주', '뉴질랜드'],
            'north-america': ['미국', '캐나다'],
            'south-america': ['브라질', '아르헨티나', '페루', '칠레', '볼리비아'],
            'africa': ['남아프리카공화국', '케냐', '탄자니아', '이집트', '모로코']
        }
        
        if continent_id not in continent_mapping:
            return jsonify({'error': '해당 대륙을 찾을 수 없습니다.'}), 404
            
        countries = continent_mapping[continent_id]
        
        # 빈 대륙의 경우 빈 배열 반환
        if not countries:
            return jsonify([])
        
        # 해당 대륙의 국가들 데이터 필터링
        continent_data = travel_df[travel_df['국가'].isin(countries)]
        
        # 기본 이미지 URL
        default_image = 'https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=800&q=80'
        
        result = []
        for _, row in continent_data.iterrows():
            city_name = row['도시']
            result.append({
                'country': row['국가'],
                'city': city_name,
                'theme': row['테마'],
                'reason': row['추천이유'],
                'days': row['추천일정'],
                'total_cost': int(row['총예상경비']),
                'airfare': int(row['예상항공료']),
                'accommodation': int(row['숙박비']),
                'food': int(row['식비']),
                'image_url': CITY_IMAGES.get(city_name, default_image)
            })
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'데이터 로딩 중 오류: {str(e)}'}), 500

# GeoJSON 파일 서빙
@app.route('/static/geojson/continent-low.geo.json')
def serve_world_map_data():
    try:
        import json

        file_path = os.path.join(app.root_path, 'static', 'geojson', 'continent-low.geo.json')

        if not os.path.exists(file_path):
            return jsonify({
                "error": "GeoJSON 파일을 찾을 수 없습니다.",
                "path": file_path
            }), 404
        
        # 파일을 직접 읽어서 JSON으로 반환
        with open(file_path, 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)
        
        return jsonify(geojson_data)
    
    except Exception as e:
        return jsonify({
            "error": f"파일 서빙 중 오류 발생: {str(e)}"
        }), 500





# =========================================
# 적금‧예금 비교 결과 계산 헬퍼
# =========================================

def safe_float_conversion(value, default=0.0):
    """안전한 float 변환 함수"""
    if pd.isna(value):
        return default
    try:
        if isinstance(value, str):
            # 문자열에서 숫자만 추출
            import re
            numbers = re.findall(r'\d+\.?\d*', str(value))
            if numbers:
                return float(numbers[0])
        return float(value)
    except (ValueError, TypeError):
        return default

def calculate_interest_with_tax(principal, rate, months, is_savings=True):
    """이자 계산 및 세금 적용 함수"""
    try:
        monthly_rate = rate / 100 / 12
        total_principal = principal * months  # 총 납입액
        
        if is_savings:
            # 적금: 매월 납입
            if monthly_rate == 0:
                total_amount = total_principal
            else:
                # 적금 복리 계산
                total_amount = principal * (((1 + monthly_rate) ** months - 1) / monthly_rate) * (1 + monthly_rate)
        else:
            # 예금: 일시납입
            total_amount = total_principal * (1 + monthly_rate) ** months
        
        # 세전 이자 계산
        gross_interest = total_amount - total_principal
        
        # 이자 과세 계산 (15.4%)
        tax_rate = 0.154
        interest_tax = gross_interest * tax_rate
        
        # 세후 이자 계산
        net_interest = gross_interest - interest_tax
        
        # 실수령액 계산
        final_amount = total_principal + net_interest
        
        return {
            '총납입액': total_principal,
            '세전이자': gross_interest,
            '이자과세': interest_tax,
            '세후이자': net_interest,
            '실수령액': final_amount
        }
            
    except Exception as e:
        print(f"이자 계산 중 오류: {e}")
        total_principal = principal * months
        return {
            '총납입액': total_principal,
            '세전이자': 0,
            '이자과세': 0,
            '세후이자': 0,
            '실수령액': total_principal
        }

def get_bank_logo(bank_name):
    """은행명으로 로고 파일명을 찾습니다."""
    # 정확한 매칭 시도
    if bank_name in bank_logo_map:
        return bank_logo_map[bank_name]
    
    # 부분 매칭 시도 (은행명이 포함된 경우)
    for logo_bank, logo_file in bank_logo_map.items():
        if bank_name in logo_bank or logo_bank in bank_name:
            return logo_file
    
    # 특별한 경우 처리
    bank_mapping = {
        '카카오뱅크': 'kakaobank.png',
        '토스뱅크': 'toss.png',
        '케이뱅크': 'kbank.png',
        'iM뱅크': 'imbank.png',
        '아이엠뱅크': 'imbank.png',
        '국민은행': 'kb.png',
        'KB국민은행': 'kb.png',
        '신한은행': 'shinhan.png',
        '우리은행': 'woori.png',
        '하나은행': 'keb.png',
        '농협은행': 'nh.png',
        '기업은행': 'ibk.png',
        'IBK기업은행': 'ibk.png'
    }
    
    return bank_mapping.get(bank_name, None)

def build_result(df, mode, bank_name, product_name, manual_rate, amount, months):
    """결과 생성 함수"""
    try:
        if mode == 'manual':
            # 직접 입력 모드
            is_savings = '적금' in request.form.get('product_type', 'savings')
            calc_result = calculate_interest_with_tax(amount, manual_rate, months, is_savings)
            
            return {
                '금융회사명': '직접입력',
                '상품명': f'직접입력 ({manual_rate}%)',
                '금리': manual_rate,
                '로고파일명': None,
                **calc_result
            }
        else:
            # 목록 선택 모드
            if df.empty or not bank_name or not product_name:
                calc_result = calculate_interest_with_tax(amount, 0, months, True)
                return {
                    '금융회사명': bank_name or '선택없음',
                    '상품명': product_name or '선택없음',
                    '금리': 0.0,
                    '로고파일명': get_bank_logo(bank_name) if bank_name else None,
                    **calc_result
                }
            
            # 상품 찾기
            product_data = df[
                (df['금융회사명'] == bank_name) & 
                (df['상품명'] == product_name)
            ]
            
            if product_data.empty:
                calc_result = calculate_interest_with_tax(amount, 0, months, True)
                return {
                    '금융회사명': bank_name,
                    '상품명': product_name,
                    '금리': 0.0,
                    '로고파일명': get_bank_logo(bank_name),
                    **calc_result
                }
            
            # 금리 추출 (최고우대금리 우선)
            rate = 0.0
            if '최고우대금리(%)' in product_data.columns:
                rate = safe_float_conversion(product_data['최고우대금리(%)'].iloc[0])
            elif '기본금리(%)' in product_data.columns:
                rate = safe_float_conversion(product_data['기본금리(%)'].iloc[0])
            elif '최고우대금리' in product_data.columns:
                rate = safe_float_conversion(product_data['최고우대금리'].iloc[0])
            elif '기본금리' in product_data.columns:
                rate = safe_float_conversion(product_data['기본금리'].iloc[0])
            
            # 상품 타입 판단
            is_savings = request.form.get('product_type', 'savings') == 'savings'
            calc_result = calculate_interest_with_tax(amount, rate, months, is_savings)
            
            return {
                '금융회사명': bank_name,
                '상품명': product_name,
                '금리': rate,
                '로고파일명': get_bank_logo(bank_name),
                **calc_result
            }
            
    except Exception as e:
        print(f"결과 생성 중 오류: {e}")
        calc_result = calculate_interest_with_tax(amount, 0, months, True)
        return {
            '금융회사명': bank_name or '오류',
            '상품명': product_name or '오류',
            '금리': 0.0,
            '로고파일명': get_bank_logo(bank_name) if bank_name else None,
            **calc_result
        }

def create_product_map():
    """상품 맵 생성 함수"""
    try:
        product_map = {}
        
        # 예금 상품 맵
        deposit_df = pd.concat([deposit_tier1, deposit_tier2], ignore_index=True)
        if not deposit_df.empty and '금융회사명' in deposit_df.columns and '상품명' in deposit_df.columns:
            deposit_grouped = deposit_df.groupby('금융회사명')['상품명'].apply(
                lambda x: x.dropna().unique().tolist()
            ).to_dict()
            product_map['deposit'] = deposit_grouped
        else:
            product_map['deposit'] = {}
        
        # 적금 상품 맵
        savings_df = pd.concat([savings_tier1, savings_tier2], ignore_index=True)
        if not savings_df.empty and '금융회사명' in savings_df.columns and '상품명' in savings_df.columns:
            savings_grouped = savings_df.groupby('금융회사명')['상품명'].apply(
                lambda x: x.dropna().unique().tolist()
            ).to_dict()
            product_map['savings'] = savings_grouped
        else:
            product_map['savings'] = {}
        
        return product_map
        
    except Exception as e:
        print(f"상품 맵 생성 중 오류: {e}")
        return {'deposit': {}, 'savings': {}}

# 수정된 비교 페이지 라우트 - breadcrumb 수정
@app.route('/plus/compare', methods=['GET', 'POST'], endpoint='compare_savings')
def compare_savings():
    breadcrumb = [
        {'name': '홈', 'url': '/'},
        {'name': 'MOA PLUS', 'url': '/plus'},
        {'name': '한눈에 비교하기 쉬운 상품', 'url': '/plus/calculator'},
        {'name': '한눈에 싹 MOA', 'current': True}
    ]
    """상품 비교 페이지"""
    
    if request.method == 'POST':
        try:
            # 폼 데이터 추출
            product_type = request.form.get('product_type', 'savings')
            
            # 좌·우 패널 데이터
            mode_l = request.form.get('mode_left', 'list')
            mode_r = request.form.get('mode_right', 'list')
            tier_l = request.form.get('tier_left', 'all')
            tier_r = request.form.get('tier_right', 'all')
            
            # 금리 (직접입력 모드용)
            rate_l = safe_float_conversion(request.form.get('rate_left', '0'))
            rate_r = safe_float_conversion(request.form.get('rate_right', '0'))
            
            # 은행 및 상품
            bank_l = request.form.get('bank_left', '')
            bank_r = request.form.get('bank_right', '')
            prod_l = request.form.get('product_left', '')
            prod_r = request.form.get('product_right', '')
            
            # 계산 조건
            amount = int(request.form.get('amount', 100000))
            months = int(request.form.get('months', 12))
            
            # 데이터프레임 선택
            if product_type == 'deposit':
                base_df = pd.concat([deposit_tier1, deposit_tier2], ignore_index=True)
            else:
                base_df = pd.concat([savings_tier1, savings_tier2], ignore_index=True)
            
            # 티어 필터링
            df_l = base_df.copy()
            if tier_l == 'tier1':
                df_l = df_l[df_l['금융회사명'].isin(tier1_list)]
            elif tier_l == 'tier2':
                df_l = df_l[df_l['금융회사명'].isin(tier2_list)]
            
            df_r = base_df.copy()
            if tier_r == 'tier1':
                df_r = df_r[df_r['금융회사명'].isin(tier1_list)]
            elif tier_r == 'tier2':
                df_r = df_r[df_r['금융회사명'].isin(tier2_list)]
            
            # 결과 계산
            res1 = build_result(df_l, mode_l, bank_l, prod_l, rate_l, amount, months)
            res2 = build_result(df_r, mode_r, bank_r, prod_r, rate_r, amount, months)
            
            # 비교 결과
            gap = abs(res1['실수령액'] - res2['실수령액'])
            better = res1['금융회사명'] if res1['실수령액'] > res2['실수령액'] else res2['금융회사명']
            
            # 템플릿용 데이터 준비
            product_map = create_product_map()
            bank_list = sorted(list(set(tier1_list + tier2_list)))
            bank_tier_map = {b: ('tier1' if b in tier1_list else 'tier2') for b in bank_list}
            
            return render_template(
                    'compare_form.html',
                    breadcrumb=breadcrumb,
                    product_map=product_map,
                    bank_list=bank_list,
                    bank_tier_map=bank_tier_map,
                    result1=res1,
                    result2=res2,
                    gap=gap,
                    better=better
                )
        except Exception as e:
            print(f"POST 처리 중 오류: {e}")
            # 오류 발생 시 기본 GET 처리로 fallback
            pass
        
    # GET 요청 처리
    try:
        product_map = create_product_map()
        bank_list = sorted(list(set(tier1_list + tier2_list)))
        bank_tier_map = {b: ('tier1' if b in tier1_list else 'tier2') for b in bank_list}
        
        return render_template(
            'compare_form.html',
            breadcrumb=breadcrumb,
            product_map=product_map,
            bank_list=bank_list,
            bank_tier_map=bank_tier_map,
            result1=None,
            result2=None,
            gap=None,
            better=None
        )
        
    except Exception as e:
        print(f"GET 처리 중 오류: {e}")
        return render_template(
            'compare_form.html',
            breadcrumb=breadcrumb,
            product_map={},
            bank_list=[],
            bank_tier_map={},
            result1=None,
            result2=None,
            gap=None,
            better=None
        )

@app.template_filter('format_currency')
def format_currency(value, symbol='₩'):
    try:
        return f"{symbol}{int(value):,}"
    except:
        return value


# 상품을 모아 페이지
@app.route('/plus/roadmap')
def roadmap():
    breadcrumb = [
        {'name': '홈', 'url': '/'},
        {'name': 'MOA PLUS', 'url': '/plus'},
        {'name': '당신의 미래를 모으는 시간', 'current': True}
    ]
    return render_template('plus_roadmap.html', breadcrumb=breadcrumb)

# 가이드 라우트 삭제 - 리다이렉트로 대체
@app.route('/guide')
def guide_moa():
    return redirect('/plus/calculator')

if __name__ == '__main__':
    app.run(debug=True)
