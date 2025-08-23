#!/usr/bin/env python3
"""
키움증권 조건검색 WebSocket TR 테스트 클라이언트

조건검색 TR 명령어 전용 테스트 스크립트:
- CNSRLST: 조건검색 목록조회
- CNSRREQ: 조건검색 실행 (일반/실시간)
- CNSRCLR: 조건검색 실시간 해제
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Dict, Any

# 프로젝트 루트를 PYTHONPATH에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

# .env 파일 로드를 위한 경로 설정
os.chdir(project_root)

from kiwoom_api.realtime.client import RealtimeClient

# 키움 공식 WebSocket 서버 URL
SOCKET_URL = 'wss://api.kiwoom.com:10000/api/dostk/websocket'


class ScreenerTester:
    """조건검색 TR 테스트 클래스"""
    
    def __init__(self):
        self.client = RealtimeClient(SOCKET_URL)
        self.conditions = []  # 조회된 조건식 목록
        self.active_conditions = []  # 실시간 활성화된 조건식들
        
        # TR 콜백 등록
        self.client.add_tr_callback(self._handle_tr_response)
    
    def _handle_tr_response(self, tr_name: str, result: Dict[str, Any]):
        """TR 응답 처리 콜백"""
        print(f"\n{'='*60}")
        
        if tr_name == "CNSRLST":
            print(f"📋 조건검색 목록조회 응답")
            if result['success']:
                self.conditions = result.get('conditions', [])
                print(f"✅ 성공: {result.get('total_count', 0)}개 조건식 발견")
                for i, condition in enumerate(self.conditions):
                    print(f"   {i+1}. {condition['seq']}: {condition['name']}")
                    print(f"      └ {condition.get('description', 'No description')}")
            else:
                print(f"❌ 실패: {result.get('error_message', 'Unknown error')}")
        
        elif tr_name == "CNSRREQ":
            print(f"🔍 조건검색 실행 응답")
            seq = result.get('seq')
            if result['success']:
                results_count = result.get('total_results', 0)
                search_type = result.get('search_type', '0')
                is_realtime = result.get('realtime_enabled', False)
                
                print(f"✅ 성공: 조건식 {seq}")
                print(f"   - 검색 모드: {'실시간 포함' if is_realtime else '일반 검색'}")
                print(f"   - 발견 종목: {results_count}개")
                
                # 검색 결과 표시
                search_results = result.get('search_results', [])
                for result_item in search_results[:5]:  # 최대 5개만 표시
                    print(f"   - {result_item.get('stock_code', 'N/A')} (발견시간: {result_item.get('detected_time', 'N/A')})")
                
                if len(search_results) > 5:
                    print(f"   - ... 외 {len(search_results) - 5}개 종목")
                
                # 실시간 모드면 활성 조건식에 추가
                if is_realtime:
                    if seq not in self.active_conditions:
                        self.active_conditions.append(seq)
                    print(f"   🚨 실시간 감시 시작됨")
            else:
                print(f"❌ 실패: 조건식 {seq}")
                print(f"   오류: {result.get('error_message', 'Unknown error')}")
        
        elif tr_name == "CNSRCLR":
            print(f"⏹️ 조건검색 실시간 해제 응답")
            seq = result.get('seq')
            if result['success']:
                print(f"✅ 성공: 조건식 {seq} 실시간 감시 중단됨")
                if seq in self.active_conditions:
                    self.active_conditions.remove(seq)
            else:
                print(f"❌ 실패: 조건식 {seq}")
                print(f"   오류: {result.get('error_message', 'Unknown error')}")
        
        elif tr_name == "SCREENER_REALTIME":
            print(f"🚨 조건검색 실시간 알림")
            condition_seq = result.get('condition_seq')
            stock_code = result.get('stock_code')
            action_desc = result.get('action_description')
            status = result.get('status')
            trade_time = result.get('trade_time')
            
            print(f"   조건식: {condition_seq}")
            print(f"   종목코드: {stock_code}")
            print(f"   상태: {action_desc} → {status}")
            if trade_time:
                print(f"   시간: {trade_time}")
        
        print(f"{'='*60}\n")
    
    async def run_interactive_test(self):
        """대화형 테스트 실행"""
        print("🚀 키움증권 조건검색 TR 테스트 시작")
        print("=" * 60)
        
        try:
            # 연결
            if not await self.client.connect():
                print("❌ WebSocket 연결 실패")
                return
            
            print("✅ WebSocket 연결 성공!")
            print("⏳ 로그인 완료 대기 중... (3초)")
            await asyncio.sleep(3)
            
            # 지원 기능 표시
            tr_stats = self.client.get_tr_statistics()
            print(f"\n📊 지원 TR 명령어: {len(tr_stats['supported_trs'])}개")
            for tr in tr_stats['supported_trs']:
                print(f"   - {tr}")
            
            print("\n" + "=" * 60)
            print("대화형 테스트 시작 (메시지 수신을 백그라운드에서 처리)")
            print("=" * 60)
            
            # 메시지 수신을 백그라운드 태스크로 실행
            receive_task = asyncio.create_task(self.client.receive_messages())
            
            # 대화형 테스트 시작
            await self._interactive_menu()
            
            # 태스크 정리
            receive_task.cancel()
            try:
                await receive_task
            except asyncio.CancelledError:
                pass
            
        except KeyboardInterrupt:
            print("\n🛑 사용자에 의해 중단됨")
        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
        finally:
            # 정리 작업
            await self._cleanup()
            await self.client.disconnect()
            print("🏁 테스트 종료")
    
    async def _interactive_menu(self):
        """대화형 메뉴"""
        while True:
            print("\n" + "-" * 40)
            print("📋 테스트 메뉴")
            print("-" * 40)
            print("1. 조건검색 목록조회 (CNSRLST)")
            print("2. 조건검색 실행 - 일반 (CNSRREQ)")
            print("3. 조건검색 실행 - 실시간 (CNSRREQ)")
            print("4. 실시간 감시 해제 (CNSRCLR)")
            print("5. 현재 상태 조회")
            print("0. 종료")
            print("-" * 40)
            
            try:
                choice = input("선택 (0-5): ").strip()
                
                if choice == "0":
                    break
                elif choice == "1":
                    await self._test_get_conditions()
                elif choice == "2":
                    await self._test_search_normal()
                elif choice == "3":
                    await self._test_search_realtime()
                elif choice == "4":
                    await self._test_clear_realtime()
                elif choice == "5":
                    self._show_status()
                else:
                    print("❌ 잘못된 선택입니다.")
                
                # 응답 대기
                if choice in ["1", "2", "3", "4"]:
                    print("\n⏳ 응답 대기 중...")
                    await asyncio.sleep(2)
                
            except (EOFError, KeyboardInterrupt):
                break
    
    async def _test_get_conditions(self):
        """조건검색 목록조회 테스트"""
        print("\n📋 조건검색 목록조회 요청...")
        await self.client.get_screener_list()
    
    async def _test_search_normal(self):
        """일반 조건검색 테스트"""
        if not self.conditions:
            print("❌ 조건검색 목록을 먼저 조회해주세요.")
            return
        
        print("\n사용 가능한 조건식:")
        for i, condition in enumerate(self.conditions):
            print(f"   {i}: {condition['seq']} - {condition['name']}")
        
        try:
            idx = int(input("조건식 번호 선택: "))
            if 0 <= idx < len(self.conditions):
                seq = self.conditions[idx]['seq']
                print(f"\n🔍 일반 조건검색 실행: {seq}")
                await self.client.execute_screener_search(seq, "0")
            else:
                print("❌ 잘못된 번호입니다.")
        except (ValueError, IndexError):
            print("❌ 잘못된 입력입니다.")
    
    async def _test_search_realtime(self):
        """실시간 조건검색 테스트"""
        if not self.conditions:
            print("❌ 조건검색 목록을 먼저 조회해주세요.")
            return
        
        print("\n사용 가능한 조건식:")
        for i, condition in enumerate(self.conditions):
            status = "🔴 활성" if condition['seq'] in self.active_conditions else "⚪ 비활성"
            print(f"   {i}: {condition['seq']} - {condition['name']} ({status})")
        
        try:
            idx = int(input("조건식 번호 선택: "))
            if 0 <= idx < len(self.conditions):
                seq = self.conditions[idx]['seq']
                if seq in self.active_conditions:
                    print("⚠️ 이미 실시간 감시 중인 조건식입니다.")
                else:
                    print(f"\n🚨 실시간 조건검색 실행: {seq}")
                    await self.client.execute_screener_search(seq, "1")
            else:
                print("❌ 잘못된 번호입니다.")
        except (ValueError, IndexError):
            print("❌ 잘못된 입력입니다.")
    
    async def _test_clear_realtime(self):
        """실시간 감시 해제 테스트"""
        if not self.active_conditions:
            print("❌ 실시간 감시 중인 조건식이 없습니다.")
            return
        
        print("\n실시간 감시 중인 조건식:")
        for i, seq in enumerate(self.active_conditions):
            condition_name = next((c['name'] for c in self.conditions if c['seq'] == seq), "Unknown")
            print(f"   {i}: {seq} - {condition_name}")
        
        try:
            idx = int(input("해제할 조건식 번호 선택: "))
            if 0 <= idx < len(self.active_conditions):
                seq = self.active_conditions[idx]
                print(f"\n⏹️ 실시간 감시 해제: {seq}")
                await self.client.clear_screener_realtime(seq)
            else:
                print("❌ 잘못된 번호입니다.")
        except (ValueError, IndexError):
            print("❌ 잘못된 입력입니다.")
    
    def _show_status(self):
        """현재 상태 표시"""
        print("\n" + "=" * 40)
        print("📊 현재 상태")
        print("=" * 40)
        
        stats = self.client.get_subscription_statistics()
        print(f"연결 상태: {'✅ 연결됨' if stats['connected'] else '❌ 연결 끊김'}")
        print(f"실시간 구독 종목: {stats['total_symbols']}개")
        print(f"실시간 구독 타입: {stats['total_types']}개")
        
        print(f"\n조건검색 현황:")
        print(f"전체 조건식: {len(self.conditions)}개")
        print(f"실시간 감시 중: {len(self.active_conditions)}개")
        
        if self.conditions:
            print(f"\n📋 전체 조건식 목록:")
            for condition in self.conditions:
                status = "🔴" if condition['seq'] in self.active_conditions else "⚪"
                print(f"   {status} {condition['seq']}: {condition['name']}")
        
        print("=" * 40)
    
    async def _cleanup(self):
        """정리 작업"""
        if self.active_conditions:
            print("\n🧹 실시간 감시 조건식 정리 중...")
            for seq in self.active_conditions.copy():
                try:
                    await self.client.clear_screener_realtime(seq)
                    await asyncio.sleep(0.2)
                except Exception as e:
                    print(f"⚠️ 조건식 {seq} 정리 실패: {e}")


async def main():
    """메인 함수"""
    tester = ScreenerTester()
    await tester.run_interactive_test()


if __name__ == "__main__":
    asyncio.run(main())