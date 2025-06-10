import pandas as pd

#  원본 API 파일 로드
df_saving = pd.read_csv("적금_상품정보_API.csv")
df_deposit = pd.read_csv("정기예금_상품정보_API.csv")

#  적금용 컬럼 매핑
saving_column_mapping = {
    "kor_co_nm": "금융회사명",
    "fin_prdt_nm": "상품명",
    "join_way": "가입방법",
    "mtrt_int": "만기이자",
    "spcl_cnd": "우대조건",
    "join_member": "가입대상",
    "intr_rate_type_nm": "금리유형",
    "rsrv_type_nm": "적립유형",
    "save_trm": "저축기간(개월)",
    "intr_rate": "기본금리(%)",
    "intr_rate2": "최고우대금리(%)"
}

#  예금용 컬럼 매핑 (적립유형 제외)
deposit_column_mapping = {
    "kor_co_nm": "금융회사명",
    "fin_prdt_nm": "상품명",
    "join_way": "가입방법",
    "mtrt_int": "만기이자",
    "spcl_cnd": "우대조건",
    "join_member": "가입대상",
    "intr_rate_type_nm": "금리유형",
    "save_trm": "저축기간(개월)",
    "intr_rate": "기본금리(%)",
    "intr_rate2": "최고우대금리(%)"
}

#  공통 정리 함수
def clean_and_format(df, mapping):
    cols = [col for col in mapping.keys() if col in df.columns]
    df_clean = df[cols].rename(columns={k: v for k, v in mapping.items() if k in df.columns})
    df_clean = df_clean.drop_duplicates(subset=[
        "금융회사명", "상품명", "저축기간(개월)", "기본금리(%)", "최고우대금리(%)"
    ])
    df_clean = df_clean.sort_values(["금융회사명", "상품명", "저축기간(개월)"])
    return df_clean

#  각각 정리
clean_saving = clean_and_format(df_saving, saving_column_mapping)
clean_deposit = clean_and_format(df_deposit, deposit_column_mapping)

#  저장
clean_saving.to_csv("정리된_적금_API_버전.csv", index=False, encoding='utf-8-sig')
clean_deposit.to_csv("정리된_정기예금_API_버전.csv", index=False, encoding='utf-8-sig')

import ace_tools as tools; tools.display_dataframe_to_user(name="정리된 정기예금 API 데이터", dataframe=clean_deposit)
