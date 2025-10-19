"""
로깅 유틸리티

시스템 전반의 로깅을 관리합니다.
"""

import os
import sys
import json
from datetime import datetime
from typing import Any, Dict, Optional
from loguru import logger
from pathlib import Path

from ..config import settings

class TradingLogger:
    """자동매매 시스템 전용 로거"""
    
    def __init__(self):
        self.setup_logger()
        
    def setup_logger(self):
        """로거 설정"""
        
        # 기본 로거 제거
        logger.remove()
        
        # 로그 디렉토리 생성
        log_dir = Path(settings.log_file_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 콘솔 출력 설정
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=settings.log_level,
            colorize=True
        )
        
        # 파일 출력 설정 (일반 로그)
        logger.add(
            settings.log_file_path,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=settings.log_level,
            rotation="1 day",
            retention="30 days",
            compression="zip"
        )
        
        # 거래 전용 로그 파일
        trading_log_path = log_dir / "trading.log"
        logger.add(
            trading_log_path,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
            level="INFO",
            rotation="1 day",
            retention="90 days",
            compression="zip",
            filter=lambda record: "TRADING" in record["extra"]
        )
        
        # 에러 전용 로그 파일
        error_log_path = log_dir / "error.log"
        logger.add(
            error_log_path,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}\n{exception}",
            level="ERROR",
            rotation="1 week",
            retention="12 weeks",
            compression="zip"
        )
        
        # JSON 형태 로그 (분석용)
        json_log_path = log_dir / "trading.json"
        logger.add(
            json_log_path,
            format="{message}",
            level="INFO",
            rotation="1 day",
            retention="30 days",
            compression="zip",
            serialize=True,
            filter=lambda record: "JSON" in record["extra"]
        )
        
        logger.info("🚀 로깅 시스템 초기화 완료")
    
    def log_signal(self, symbol: str, signal_type: str, strength: float, 
                   confidence: float, reasoning: str, metadata: Optional[Dict] = None):
        """매매 신호 로그"""
        
        log_data = {
            "type": "SIGNAL",
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "signal_type": signal_type,
            "strength": strength,
            "confidence": confidence,
            "reasoning": reasoning,
            "metadata": metadata or {}
        }
        
        # 일반 로그
        logger.bind(TRADING=True).info(
            f"📊 매매신호 | {symbol} | {signal_type.upper()} | 강도:{strength:.2f} | 신뢰도:{confidence:.2f} | {reasoning}"
        )
        
        # JSON 로그
        logger.bind(JSON=True).info(json.dumps(log_data, ensure_ascii=False))
    
    def log_order(self, order_id: str, symbol: str, side: str, quantity: int, 
                  price: Optional[float] = None, status: str = "PENDING"):
        """주문 로그"""
        
        log_data = {
            "type": "ORDER",
            "timestamp": datetime.now().isoformat(),
            "order_id": order_id,
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": price,
            "status": status
        }
        
        price_str = f"@{price:,.0f}원" if price else "@시장가"
        
        # 일반 로그
        logger.bind(TRADING=True).info(
            f"📋 주문 | {order_id} | {symbol} | {side.upper()} | {quantity}주 | {price_str} | {status}"
        )
        
        # JSON 로그
        logger.bind(JSON=True).info(json.dumps(log_data, ensure_ascii=False))
    
    def log_execution(self, order_id: str, symbol: str, side: str, quantity: int, 
                     price: float, pnl: Optional[float] = None):
        """체결 로그"""
        
        log_data = {
            "type": "EXECUTION",
            "timestamp": datetime.now().isoformat(),
            "order_id": order_id,
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": price,
            "pnl": pnl
        }
        
        pnl_str = f"| 손익:{pnl:+,.0f}원" if pnl is not None else ""
        
        # 일반 로그
        logger.bind(TRADING=True).info(
            f"✅ 체결 | {order_id} | {symbol} | {side.upper()} | {quantity}주 | @{price:,.0f}원 {pnl_str}"
        )
        
        # JSON 로그
        logger.bind(JSON=True).info(json.dumps(log_data, ensure_ascii=False))
    
    def log_position(self, symbol: str, action: str, quantity: int, avg_price: float, 
                    current_price: float, pnl: float, pnl_percent: float):
        """포지션 로그"""
        
        log_data = {
            "type": "POSITION",
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "action": action,  # OPEN, UPDATE, CLOSE
            "quantity": quantity,
            "avg_price": avg_price,
            "current_price": current_price,
            "pnl": pnl,
            "pnl_percent": pnl_percent
        }
        
        action_emoji = {"OPEN": "📈", "UPDATE": "🔄", "CLOSE": "📉"}.get(action, "📊")
        
        # 일반 로그
        logger.bind(TRADING=True).info(
            f"{action_emoji} 포지션 | {symbol} | {action} | {quantity}주 | 평단:{avg_price:,.0f}원 | 현재:{current_price:,.0f}원 | 손익:{pnl:+,.0f}원({pnl_percent:+.2f}%)"
        )
        
        # JSON 로그
        logger.bind(JSON=True).info(json.dumps(log_data, ensure_ascii=False))
    
    def log_risk_event(self, event_type: str, symbol: str, message: str, 
                      severity: str = "WARNING", metadata: Optional[Dict] = None):
        """리스크 이벤트 로그"""
        
        log_data = {
            "type": "RISK_EVENT",
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "symbol": symbol,
            "message": message,
            "severity": severity,
            "metadata": metadata or {}
        }
        
        severity_emoji = {
            "INFO": "ℹ️",
            "WARNING": "⚠️", 
            "ERROR": "❌",
            "CRITICAL": "🚨"
        }.get(severity, "⚠️")
        
        # 일반 로그
        log_level = severity.lower() if severity.lower() in ["info", "warning", "error"] else "warning"
        getattr(logger.bind(TRADING=True), log_level)(
            f"{severity_emoji} 리스크 | {event_type} | {symbol} | {message}"
        )
        
        # JSON 로그
        logger.bind(JSON=True).info(json.dumps(log_data, ensure_ascii=False))
    
    def log_performance(self, period: str, metrics: Dict[str, Any]):
        """성과 지표 로그"""
        
        log_data = {
            "type": "PERFORMANCE",
            "timestamp": datetime.now().isoformat(),
            "period": period,
            "metrics": metrics
        }
        
        # 주요 지표 추출
        total_pnl = metrics.get("total_pnl", 0)
        win_rate = metrics.get("win_rate", 0)
        total_trades = metrics.get("total_trades", 0)
        
        # 일반 로그
        logger.bind(TRADING=True).info(
            f"📊 성과 | {period} | 총손익:{total_pnl:+,.0f}원 | 승률:{win_rate:.1%} | 거래:{total_trades}회"
        )
        
        # JSON 로그
        logger.bind(JSON=True).info(json.dumps(log_data, ensure_ascii=False))
    
    def log_system_event(self, event_type: str, message: str, 
                        level: str = "INFO", metadata: Optional[Dict] = None):
        """시스템 이벤트 로그"""
        
        log_data = {
            "type": "SYSTEM_EVENT",
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "message": message,
            "level": level,
            "metadata": metadata or {}
        }
        
        event_emoji = {
            "START": "🚀",
            "STOP": "🛑", 
            "ERROR": "❌",
            "WARNING": "⚠️",
            "INFO": "ℹ️",
            "SUCCESS": "✅"
        }.get(event_type, "📋")
        
        # 일반 로그
        log_level = level.lower() if level.lower() in ["info", "warning", "error"] else "info"
        getattr(logger, log_level)(f"{event_emoji} 시스템 | {event_type} | {message}")
        
        # JSON 로그
        logger.bind(JSON=True).info(json.dumps(log_data, ensure_ascii=False))
    
    def log_market_data(self, symbol: str, data_type: str, data: Dict[str, Any]):
        """시장 데이터 로그 (디버깅용)"""
        
        if settings.log_level == "DEBUG":
            log_data = {
                "type": "MARKET_DATA",
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "data_type": data_type,
                "data": data
            }
            
            logger.debug(f"📡 시장데이터 | {symbol} | {data_type} | {data}")
            logger.bind(JSON=True).debug(json.dumps(log_data, ensure_ascii=False))
    
    def log_backtest_result(self, strategy: str, period: str, results: Dict[str, Any]):
        """백테스트 결과 로그"""
        
        log_data = {
            "type": "BACKTEST",
            "timestamp": datetime.now().isoformat(),
            "strategy": strategy,
            "period": period,
            "results": results
        }
        
        total_return = results.get("total_return", 0)
        sharpe_ratio = results.get("sharpe_ratio", 0)
        max_drawdown = results.get("max_drawdown", 0)
        
        # 일반 로그
        logger.info(
            f"🧪 백테스트 | {strategy} | {period} | 수익률:{total_return:.2f}% | 샤프:{sharpe_ratio:.2f} | MDD:{max_drawdown:.2f}%"
        )
        
        # JSON 로그
        logger.bind(JSON=True).info(json.dumps(log_data, ensure_ascii=False))

# 전역 로거 인스턴스
trading_logger = TradingLogger()

# 편의 함수들
def log_signal(symbol: str, signal_type: str, strength: float, confidence: float, 
               reasoning: str, metadata: Optional[Dict] = None):
    """매매 신호 로그 (편의 함수)"""
    trading_logger.log_signal(symbol, signal_type, strength, confidence, reasoning, metadata)

def log_order(order_id: str, symbol: str, side: str, quantity: int, 
              price: Optional[float] = None, status: str = "PENDING"):
    """주문 로그 (편의 함수)"""
    trading_logger.log_order(order_id, symbol, side, quantity, price, status)

def log_execution(order_id: str, symbol: str, side: str, quantity: int, 
                 price: float, pnl: Optional[float] = None):
    """체결 로그 (편의 함수)"""
    trading_logger.log_execution(order_id, symbol, side, quantity, price, pnl)

def log_position(symbol: str, action: str, quantity: int, avg_price: float, 
                current_price: float, pnl: float, pnl_percent: float):
    """포지션 로그 (편의 함수)"""
    trading_logger.log_position(symbol, action, quantity, avg_price, current_price, pnl, pnl_percent)

def log_risk_event(event_type: str, symbol: str, message: str, 
                  severity: str = "WARNING", metadata: Optional[Dict] = None):
    """리스크 이벤트 로그 (편의 함수)"""
    trading_logger.log_risk_event(event_type, symbol, message, severity, metadata)

def log_performance(period: str, metrics: Dict[str, Any]):
    """성과 지표 로그 (편의 함수)"""
    trading_logger.log_performance(period, metrics)

def log_system_event(event_type: str, message: str, level: str = "INFO", 
                    metadata: Optional[Dict] = None):
    """시스템 이벤트 로그 (편의 함수)"""
    trading_logger.log_system_event(event_type, message, level, metadata)

# 기본 로거 접근
def get_logger():
    """기본 로거 반환"""
    return logger
