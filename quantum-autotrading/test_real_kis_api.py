"""
실제 KIS API 연동 테스트

quantum-autotrading의 KIS 클라이언트를 실제 API와 연동하여 테스트합니다.
"""

import asyncio
import json
import yaml
import requests
from datetime import datetime
from pathlib import Path

# 기존 KIS 설정 로드
def load_kis_config():
    """KIS 설정 파일 로드"""
    try:
        config_path = "/Users/admin/study/quantum-trading-platform/quantum-adapter-kis/kis_devlp.yaml"
        with open(config_path, encoding="UTF-8") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        return config
    except Exception as e:
        print(f"❌ KIS 설정 파일 로드 실패: {e}")
        return None

class RealKISClient:
    """실제 KIS API 클라이언트"""
    
    def __init__(self):
        self.config = load_kis_config()
        if not self.config:
            raise Exception("KIS 설정을 로드할 수 없습니다.")
        
        # 모의투자 설정 사용
        self.app_key = self.config['paper_app']
        self.app_secret = self.config['paper_sec']
        self.base_url = self.config['vps']  # 모의투자 URL
        self.account_no = self.config['my_paper_stock']
        self.product_code = self.config['my_prod']
        
        self.access_token = None
        
    def get_access_token(self):
        """KIS API 접근 토큰 발급"""
        
        print("🔐 KIS API 토큰 발급 중...")
        
        url = f"{self.base_url}/oauth2/tokenP"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        data = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                self.access_token = result.get("access_token")
                
                if self.access_token:
                    print(f"✅ 토큰 발급 성공: {self.access_token[:20]}...")
                    return True
                else:
                    print("❌ 토큰이 응답에 없습니다.")
                    print(f"응답: {result}")
                    return False
            else:
                print(f"❌ 토큰 발급 실패: {response.status_code}")
                print(f"응답: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 토큰 발급 오류: {e}")
            return False
    
    def get_current_price(self, symbol: str):
        """주식 현재가 조회"""
        
        if not self.access_token:
            print("❌ 토큰이 없습니다. 먼저 인증을 수행하세요.")
            return None
        
        print(f"📊 {symbol} 현재가 조회 중...")
        
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
        
        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": "FHKST01010100"
        }
        
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": symbol
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("rt_cd") == "0":
                    output = result.get("output", {})
                    current_price = output.get("stck_prpr", "N/A")
                    change_rate = output.get("prdy_ctrt", "N/A")
                    
                    print(f"✅ 현재가 조회 성공")
                    print(f"   💹 현재가: {current_price}원")
                    print(f"   📈 등락률: {change_rate}%")
                    
                    return {
                        "current_price": current_price,
                        "change_rate": change_rate,
                        "raw_data": output
                    }
                else:
                    print(f"❌ API 오류: {result.get('msg1', 'Unknown error')}")
                    return None
            else:
                print(f"❌ 현재가 조회 실패: {response.status_code}")
                print(f"응답: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ 현재가 조회 오류: {e}")
            return None
    
    def get_account_balance(self):
        """계좌 잔고 조회"""
        
        if not self.access_token:
            print("❌ 토큰이 없습니다. 먼저 인증을 수행하세요.")
            return None
        
        print("💰 계좌 잔고 조회 중...")
        
        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-balance"
        
        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": "VTTC8434R"  # 모의투자용 TR_ID
        }
        
        params = {
            "CANO": self.account_no,
            "ACNT_PRDT_CD": self.product_code,
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",
            "INQR_DVSN": "02",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "01",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": ""
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("rt_cd") == "0":
                    output2 = result.get("output2", [{}])[0] if result.get("output2") else {}
                    
                    total_balance = output2.get("tot_evlu_amt", "N/A")
                    cash_balance = output2.get("dnca_tot_amt", "N/A")
                    stock_balance = output2.get("scts_evlu_amt", "N/A")
                    
                    print(f"✅ 잔고 조회 성공")
                    print(f"   💵 총 평가금액: {total_balance}원")
                    print(f"   💰 예수금: {cash_balance}원")
                    print(f"   📈 주식 평가금액: {stock_balance}원")
                    
                    return {
                        "total_balance": total_balance,
                        "cash_balance": cash_balance,
                        "stock_balance": stock_balance,
                        "raw_data": output2
                    }
                else:
                    print(f"❌ API 오류: {result.get('msg1', 'Unknown error')}")
                    return None
            else:
                print(f"❌ 잔고 조회 실패: {response.status_code}")
                print(f"응답: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ 잔고 조회 오류: {e}")
            return None

def test_real_kis_api():
    """실제 KIS API 테스트"""
    
    print("🚀 === 실제 KIS API 연동 테스트 ===")
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # KIS 클라이언트 생성
        client = RealKISClient()
        
        print(f"📋 설정 정보:")
        print(f"   App Key: {client.app_key[:10]}...")
        print(f"   Base URL: {client.base_url}")
        print(f"   계좌번호: {client.account_no}")
        print()
        
        # 1. 토큰 발급 테스트
        print("1️⃣ === 토큰 발급 테스트 ===")
        auth_success = client.get_access_token()
        
        if not auth_success:
            print("❌ 토큰 발급 실패로 테스트를 중단합니다.")
            return
        
        print()
        
        # 2. 계좌 잔고 조회 테스트
        print("2️⃣ === 계좌 잔고 조회 테스트 ===")
        balance_data = client.get_account_balance()
        print()
        
        # 3. 주식 현재가 조회 테스트
        print("3️⃣ === 주식 현재가 조회 테스트 ===")
        
        # 삼성전자 현재가 조회
        samsung_data = client.get_current_price("005930")
        print()
        
        # SK하이닉스 현재가 조회
        sk_data = client.get_current_price("000660")
        print()
        
        # 4. 결과 요약
        print("🎯 === 테스트 결과 요약 ===")
        
        results = [
            ("토큰 발급", auth_success),
            ("잔고 조회", balance_data is not None),
            ("삼성전자 현재가", samsung_data is not None),
            ("SK하이닉스 현재가", sk_data is not None)
        ]
        
        total_tests = len(results)
        passed_tests = sum(1 for _, result in results if result)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {test_name}: {status}")
        
        print(f"\n📊 총 테스트: {total_tests}")
        print(f"📊 성공: {passed_tests}")
        print(f"📊 실패: {total_tests - passed_tests}")
        print(f"📊 성공률: {(passed_tests/total_tests*100):.1f}%")
        
        if passed_tests == total_tests:
            print("\n🎉 모든 테스트가 성공했습니다!")
            print("   quantum-autotrading 시스템에서 실제 KIS API를 사용할 준비가 되었습니다!")
        else:
            print(f"\n⚠️ {total_tests - passed_tests}개의 테스트가 실패했습니다.")
        
        print(f"\n완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"❌ 테스트 실행 오류: {e}")

if __name__ == "__main__":
    test_real_kis_api()
