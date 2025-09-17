# -*- coding: utf-8 -*-
"""
순수 파일 기반 KIS 인증 시스템 (DB 의존성 완전 제거)
KIS Open API 표준 방식 그대로 사용
"""

import json
import logging
import os
import time
from base64 import b64decode
from collections import namedtuple
from datetime import datetime
from io import StringIO

import pandas as pd
import requests
import websockets
import yaml
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

clearConsole = lambda: os.system("cls" if os.name in ("nt", "dos") else "clear")

key_bytes = 32
config_root = os.path.join(os.path.expanduser("~"), "KIS", "config")

# 토큰 파일 경로
token_tmp = os.path.join(
    config_root, f"KIS{datetime.today().strftime("%Y%m%d")}"
)

# 접근토큰 관리하는 파일 존재여부 체크, 없으면 생성
if os.path.exists(token_tmp) == False:
    f = open(token_tmp, "w+")

# 설정 파일 로드
with open(os.path.join(config_root, "kis_devlp.yaml"), encoding="UTF-8") as f:
    _cfg = yaml.load(f, Loader=yaml.FullLoader)

_base_headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "charset": "UTF-8",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

_last_auth_time = None
_DEBUG = True

def read_token():
    """파일에서 토큰 읽기"""
    try:
        with open(token_tmp, "r") as f:
            data = f.read()
            if data:
                # 토큰 파일에서 순수한 토큰만 추출
                lines = data.strip().split('\n')
                for line in lines:
                    if line.startswith('token:'):
                        token = line.split('token:', 1)[1].strip()
                        print("✅ 파일에서 유효한 토큰 조회 성공")
                        return token
                    elif line.startswith('eyJ'):  # JWT 토큰 시작
                        print("✅ 파일에서 유효한 토큰 조회 성공")
                        return line.strip()

                # 전체 데이터가 토큰인 경우
                if data.startswith('eyJ'):
                    print("✅ 파일에서 유효한 토큰 조회 성공")
                    return data.strip()
    except FileNotFoundError:
        pass
    return None

def save_token(token):
    """파일에 토큰 저장"""
    try:
        with open(token_tmp, "w") as f:
            f.write(token)
        if _DEBUG:
            print(f"💾 토큰 파일 저장 완료: {token_tmp}")
        return True
    except Exception as e:
        print(f"❌ 토큰 저장 실패: {e}")
        return False

def changeTREnv(token, svr, product):
    """거래 환경 설정"""
    global _cfg
    _cfg["my_token"] = token
    _cfg["my_svr"] = svr
    _cfg["my_prod"] = product

def auth(svr="prod", product=None, url=None, user_id=1):
    """KIS API 인증 (순수 파일 기반)"""
    global _last_auth_time

    if product is None:
        product = _cfg["my_prod"]

    print("📁 순수 파일 기반 토큰 관리 모드")

    # 1단계: 파일에서 토큰 확인
    saved_token = read_token()

    # 2단계: 토큰이 없으면 KIS API에서 새로 발급
    if saved_token is None:
        print("🔑 새 토큰 발급 요청...")

        p = {
            "grant_type": "client_credentials",
        }

        if svr == "prod":  # 실전투자
            ak1 = "my_app"
            ak2 = "my_sec"
        elif svr == "vps":  # 모의투자
            ak1 = "paper_app"
            ak2 = "paper_sec"

        p["appkey"] = _cfg[ak1]
        p["appsecret"] = _cfg[ak2]

        url = f"{_cfg[svr]}/oauth2/tokenP"

        try:
            res = requests.post(url, headers=_base_headers, data=json.dumps(p))

            if res.status_code == 200:
                token_data = res.json()
                my_token = token_data["access_token"]

                # 파일에 저장
                if save_token(my_token):
                    print(f"✅ KIS API에서 새 토큰 발급 완료")
                else:
                    print(f"⚠️ 토큰 발급 성공했지만 저장 실패")

            else:
                print(f"❌ 토큰 발급 실패: {res.status_code}")
                print(f"응답: {res.text}")
                return None

        except Exception as e:
            print(f"❌ 토큰 발급 중 오류: {e}")
            return None
    else:
        my_token = saved_token
        print("📄 기존 파일 토큰 사용")

    # 3단계: 헤더 설정
    changeTREnv(my_token, svr, product)
    _base_headers["authorization"] = f"Bearer {my_token}"
    _base_headers["appkey"] = _cfg["my_app" if svr == "prod" else "paper_app"]
    _base_headers["appsecret"] = _cfg["my_sec" if svr == "prod" else "paper_sec"]

    _last_auth_time = datetime.now()

    if _DEBUG:
        print(f"[{_last_auth_time}] => 인증 완료!")

    return my_token

# 기타 필요한 함수들 (기존 kis_auth.py에서 복사)
def is_market_open():
    """장 운영시간 확인"""
    now = datetime.now()
    hour = now.hour
    minute = now.minute

    # 평일 9:00-15:30
    if now.weekday() < 5:  # 월-금
        if (hour == 9 and minute >= 0) or (9 < hour < 15) or (hour == 15 and minute <= 30):
            return True

    return False

def get_current_price(stock_code, svr="vps"):
    """현재가 조회"""
    if not _cfg.get("my_token"):
        print("❌ 인증이 필요합니다")
        return None

    url = f"{_cfg[svr]}/uapi/domestic-stock/v1/quotations/inquire-price"

    headers = _base_headers.copy()
    headers["tr_id"] = "FHKST01010100"

    params = {
        "fid_cond_mrkt_div_code": "J",
        "fid_input_iscd": stock_code
    }

    try:
        res = requests.get(url, headers=headers, params=params)
        if res.status_code == 200:
            data = res.json()
            if data.get("rt_cd") == "0":
                output = data.get("output", {})
                return {
                    "stock_code": stock_code,
                    "current_price": int(output.get("stck_prpr", 0)),
                    "change": int(output.get("prdy_vrss", 0)),
                    "change_rate": float(output.get("prdy_ctrt", 0)),
                    "volume": int(output.get("acml_vol", 0))
                }

        print(f"❌ 현재가 조회 실패: {res.status_code}")
        return None

    except Exception as e:
        print(f"❌ 현재가 조회 오류: {e}")
        return None

if __name__ == "__main__":
    # 테스트
    print("🧪 순수 파일 기반 KIS 인증 테스트")

    # 모의투자 인증
    result = auth(svr="vps", product="01")
    if result:
        print("✅ 모의투자 인증 성공")

        # 현재가 조회 테스트
        price_data = get_current_price("005930")
        if price_data:
            print(f"📊 삼성전자 현재가: {price_data['current_price']:,}원")

    else:
        print("❌ 모의투자 인증 실패")