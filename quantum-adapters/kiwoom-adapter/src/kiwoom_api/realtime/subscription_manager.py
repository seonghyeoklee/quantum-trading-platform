"""
실시간 시세 구독 관리자
종목별, 타입별 구독 상태를 관리하고 REG/REMOVE 요청을 최적화
"""

from typing import Dict, Set, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SubscriptionInfo:
    """구독 정보"""
    symbols: Set[str] = field(default_factory=set)
    types: Set[str] = field(default_factory=set)
    registered_at: datetime = field(default_factory=datetime.now)
    group_no: str = "1"
    
    def add_subscription(self, symbols: List[str], types: List[str]) -> None:
        """구독 추가"""
        self.symbols.update(symbols)
        self.types.update(types)
        self.registered_at = datetime.now()
        
    def remove_subscription(self, symbols: List[str], types: List[str]) -> None:
        """구독 제거"""
        for symbol in symbols:
            self.symbols.discard(symbol)
        for type_code in types:
            self.types.discard(type_code)
            
    def has_subscription(self, symbol: str, type_code: str) -> bool:
        """특정 구독 존재 여부 확인"""
        return symbol in self.symbols and type_code in self.types
        
    def is_empty(self) -> bool:
        """구독이 비어있는지 확인"""
        return len(self.symbols) == 0 or len(self.types) == 0


class SubscriptionManager:
    """실시간 시세 구독 관리자"""
    
    def __init__(self):
        self.subscriptions: Dict[str, SubscriptionInfo] = {}  # group_no별 구독 정보
        self.symbol_type_map: Dict[Tuple[str, str], str] = {}  # (symbol, type) -> group_no 매핑
        self._next_group_no = 1
        
    def _get_next_group_no(self) -> str:
        """다음 그룹 번호 생성"""
        group_no = str(self._next_group_no)
        self._next_group_no += 1
        return group_no
        
    def add_subscription(self, symbols: List[str], types: List[str], 
                        group_no: Optional[str] = None) -> str:
        """구독 추가"""
        if not symbols or not types:
            raise ValueError("symbols와 types는 비어있을 수 없습니다")
            
        # 그룹 번호 결정
        if group_no is None:
            group_no = "1"  # 기본 그룹
            
        # 그룹이 없으면 생성
        if group_no not in self.subscriptions:
            self.subscriptions[group_no] = SubscriptionInfo(group_no=group_no)
            
        # 구독 추가
        subscription = self.subscriptions[group_no]
        subscription.add_subscription(symbols, types)
        
        # 매핑 테이블 업데이트
        for symbol in symbols:
            for type_code in types:
                self.symbol_type_map[(symbol, type_code)] = group_no
                
        return group_no
        
    def remove_subscription(self, symbols: List[str], types: List[str],
                           group_no: Optional[str] = None) -> bool:
        """구독 제거"""
        if group_no is None:
            group_no = "1"
            
        if group_no not in self.subscriptions:
            return False
            
        # 구독 제거
        subscription = self.subscriptions[group_no]
        subscription.remove_subscription(symbols, types)
        
        # 매핑 테이블 업데이트
        for symbol in symbols:
            for type_code in types:
                self.symbol_type_map.pop((symbol, type_code), None)
                
        # 빈 구독 그룹 제거
        if subscription.is_empty():
            del self.subscriptions[group_no]
            
        return True
        
    def get_subscription_request(self, symbols: List[str], types: List[str],
                                group_no: Optional[str] = None, 
                                refresh: str = "1") -> Dict:
        """REG 요청 메시지 생성"""
        if group_no is None:
            group_no = "1"
            
        return {
            'trnm': 'REG',
            'grp_no': group_no,
            'refresh': refresh,
            'data': [{
                'item': symbols,
                'type': types,
            }]
        }
        
    def get_removal_request(self, symbols: List[str], types: List[str],
                           group_no: Optional[str] = None) -> Dict:
        """REMOVE 요청 메시지 생성"""
        if group_no is None:
            group_no = "1"
            
        return {
            'trnm': 'REMOVE',
            'grp_no': group_no,
            'data': [{
                'item': symbols,
                'type': types,
            }]
        }
        
    def is_subscribed(self, symbol: str, type_code: str) -> bool:
        """특정 종목/타입 구독 여부 확인"""
        return (symbol, type_code) in self.symbol_type_map
        
    def get_group_no(self, symbol: str, type_code: str) -> Optional[str]:
        """특정 종목/타입의 그룹 번호 반환"""
        return self.symbol_type_map.get((symbol, type_code))
        
    def get_subscribed_symbols(self, group_no: Optional[str] = None) -> Set[str]:
        """구독 중인 종목 목록"""
        if group_no:
            subscription = self.subscriptions.get(group_no)
            return subscription.symbols if subscription else set()
        else:
            # 모든 그룹의 종목 합집합
            all_symbols = set()
            for subscription in self.subscriptions.values():
                all_symbols.update(subscription.symbols)
            return all_symbols
            
    def get_subscribed_types(self, group_no: Optional[str] = None) -> Set[str]:
        """구독 중인 타입 목록"""
        if group_no:
            subscription = self.subscriptions.get(group_no)
            return subscription.types if subscription else set()
        else:
            # 모든 그룹의 타입 합집합
            all_types = set()
            for subscription in self.subscriptions.values():
                all_types.update(subscription.types)
            return all_types
            
    def get_all_subscriptions(self) -> Dict[str, SubscriptionInfo]:
        """모든 구독 정보 반환"""
        return self.subscriptions.copy()
        
    def clear_all_subscriptions(self) -> None:
        """모든 구독 정보 삭제"""
        self.subscriptions.clear()
        self.symbol_type_map.clear()
        self._next_group_no = 1
        
    def get_statistics(self) -> Dict[str, any]:
        """구독 통계 정보 반환"""
        total_symbols = len(self.get_subscribed_symbols())
        total_types = len(self.get_subscribed_types())
        total_groups = len(self.subscriptions)
        total_mappings = len(self.symbol_type_map)
        
        return {
            "total_symbols": total_symbols,
            "total_types": total_types,
            "total_groups": total_groups,
            "total_mappings": total_mappings,
            "groups": {gno: {
                "symbols": len(sub.symbols),
                "types": len(sub.types),
                "registered_at": sub.registered_at.isoformat()
            } for gno, sub in self.subscriptions.items()}
        }