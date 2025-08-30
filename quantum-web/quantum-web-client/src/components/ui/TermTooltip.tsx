'use client';

import { useState, useRef, useEffect, ReactNode } from 'react';
import { findTermById, FinancialTerm } from '@/lib/data/financial-terms';
import { Info, ExternalLink } from 'lucide-react';

interface TermTooltipProps {
  termId: string;           // 용어 ID
  children?: ReactNode;     // 툴팁을 적용할 요소 (없으면 기본 아이콘 표시)
  className?: string;
  showIcon?: boolean;       // 아이콘 표시 여부 (기본값: true)
  position?: 'top' | 'bottom' | 'left' | 'right'; // 툴팁 위치
  maxWidth?: number;        // 최대 너비 (px)
  delay?: number;          // 표시 지연시간 (ms)
}

export default function TermTooltip({
  termId,
  children,
  className = '',
  showIcon = true,
  position = 'right',  // 기본값을 right로 변경
  maxWidth = 280,
  delay = 150  // 300ms -> 150ms로 줄여서 더 반응성 좋게
}: TermTooltipProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [actualPosition, setActualPosition] = useState(position);
  const [isPinned, setIsPinned] = useState(false);  // 클릭으로 고정된 상태
  const tooltipRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLDivElement>(null);
  const timeoutRef = useRef<NodeJS.Timeout | undefined>(undefined);

  // 용어 정보 가져오기
  const term = findTermById(termId);

  // 툴팁 표시/숨김 처리
  const showTooltip = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    timeoutRef.current = setTimeout(() => {
      setIsVisible(true);
    }, delay);
  };

  const hideTooltip = () => {
    if (isPinned) return; // 고정된 상태면 숨기지 않음
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    // 툴팁을 즉시 숨기지 않고 약간의 지연을 둠
    timeoutRef.current = setTimeout(() => {
      setIsVisible(false);
    }, 100);
  };

  // 툴팁 내부에서 마우스 이벤트 처리
  const handleTooltipMouseEnter = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
  };

  const handleTooltipMouseLeave = () => {
    if (isPinned) return; // 고정된 상태면 숨기지 않음
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setIsVisible(false);
  };

  // 클릭으로 툴팁 토글 (고정/해제)
  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsPinned(!isPinned);
    setIsVisible(!isVisible || isPinned);
  };

  // 외부 클릭 시 고정 해제
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        isPinned &&
        tooltipRef.current &&
        triggerRef.current &&
        !tooltipRef.current.contains(event.target as Node) &&
        !triggerRef.current.contains(event.target as Node)
      ) {
        setIsPinned(false);
        setIsVisible(false);
      }
    };

    if (isPinned) {
      document.addEventListener('click', handleClickOutside);
    }

    return () => {
      document.removeEventListener('click', handleClickOutside);
    };
  }, [isPinned]);

  // 툴팁 위치 자동 조정 - 오른쪽을 우선적으로 선호
  useEffect(() => {
    if (isVisible && tooltipRef.current && triggerRef.current) {
      const tooltip = tooltipRef.current;
      const trigger = triggerRef.current;
      const rect = trigger.getBoundingClientRect();
      const tooltipRect = tooltip.getBoundingClientRect();
      const viewport = {
        width: window.innerWidth,
        height: window.innerHeight
      };

      let newPosition = 'right'; // 기본적으로 오른쪽 선호

      // 오른쪽에 공간이 충분하지 않으면 다른 위치로 조정
      if (rect.right + tooltipRect.width + 20 > viewport.width) {
        // 왼쪽 공간 확인
        if (rect.left - tooltipRect.width - 20 >= 0) {
          newPosition = 'left';
        }
        // 상단 공간 확인
        else if (rect.top - tooltipRect.height - 20 >= 0) {
          newPosition = 'top';
        }
        // 하단 공간 확인
        else if (rect.bottom + tooltipRect.height + 20 <= viewport.height) {
          newPosition = 'bottom';
        }
        // 모든 공간이 부족하면 오른쪽 유지 (일부 잘릴 수 있음)
      }

      setActualPosition(newPosition as 'top' | 'bottom' | 'left' | 'right');
    }
  }, [isVisible, position]);

  // 컴포넌트 언마운트 시 정리
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  // 용어를 찾을 수 없는 경우
  if (!term) {
    console.warn(`TermTooltip: 용어를 찾을 수 없습니다. termId: ${termId}`);
    // 용어를 찾을 수 없어도 children은 표시하되, 아이콘만 회색으로 표시
    return (
      <span className={`inline-flex items-center ${className}`}>
        {children}
        {showIcon && (
          <Info className="w-3 h-3 ml-1 text-gray-300 cursor-default" />
        )}
      </span>
    );
  }

  // 난이도에 따른 색상
  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner': return 'text-green-600 bg-green-50';
      case 'intermediate': return 'text-orange-600 bg-orange-50';
      case 'advanced': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  // 난이도 표시 텍스트
  const getDifficultyText = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner': return '초급';
      case 'intermediate': return '중급';
      case 'advanced': return '고급';
      default: return '기본';
    }
  };

  // 툴팁 위치 스타일 - 여유있는 간격으로 조정
  const getTooltipPositionStyle = () => {
    switch (actualPosition) {
      case 'top':
        return {
          bottom: '100%',
          left: '50%',
          transform: 'translateX(-50%)',
          marginBottom: '8px'
        };
      case 'bottom':
        return {
          top: '100%',
          left: '50%',
          transform: 'translateX(-50%)',
          marginTop: '8px'
        };
      case 'left':
        return {
          right: '100%',
          top: '50%',
          transform: 'translateY(-50%)',
          marginRight: '8px'
        };
      case 'right':
        return {
          left: '100%',
          top: '50%',
          transform: 'translateY(-50%)',
          marginLeft: '8px'
        };
      default:
        return {};
    }
  };

  // 화살표 위치 스타일
  const getArrowStyle = () => {
    const base = 'absolute w-2 h-2 bg-white dark:bg-gray-800 border transform rotate-45';
    switch (actualPosition) {
      case 'top':
        return `${base} -bottom-1 left-1/2 -translate-x-1/2 border-r border-b border-border`;
      case 'bottom':
        return `${base} -top-1 left-1/2 -translate-x-1/2 border-l border-t border-border`;
      case 'left':
        return `${base} -right-1 top-1/2 -translate-y-1/2 border-t border-r border-border`;
      case 'right':
        return `${base} -left-1 top-1/2 -translate-y-1/2 border-b border-l border-border`;
      default:
        return base;
    }
  };

  return (
    <div 
      ref={triggerRef}
      className={`relative inline-flex items-center ${className}`}
      onMouseEnter={showTooltip}
      onMouseLeave={hideTooltip}
      onFocus={showTooltip}
      onBlur={hideTooltip}
      onClick={handleClick}
    >
      {/* 트리거 요소 */}
      {children ? (
        <span className="cursor-help inline-flex items-center">
          {children}
          {showIcon && (
            <Info className={`w-3 h-3 ml-1 transition-colors flex-shrink-0 ${
              isPinned 
                ? 'text-primary' 
                : 'text-gray-500 hover:text-primary'
            }`} />
          )}
        </span>
      ) : (
        <Info className={`w-3 h-3 cursor-help transition-colors ${
          isPinned 
            ? 'text-primary' 
            : 'text-gray-500 hover:text-primary'
        }`} />
      )}

      {/* 툴팁 */}
      {isVisible && (
        <div
          ref={tooltipRef}
          className="absolute z-50 animate-in fade-in-0 zoom-in-95 duration-200"
          style={{
            ...getTooltipPositionStyle(),
            width: `${maxWidth}px`,
            minHeight: '160px'
          }}
          onMouseEnter={handleTooltipMouseEnter}
          onMouseLeave={handleTooltipMouseLeave}
        >
          {/* 화살표 */}
          <div className={getArrowStyle()}></div>
          
          {/* 툴팁 내용 */}
          <div className="bg-white dark:bg-gray-800 border border-border rounded-lg shadow-xl p-3">
            {/* 헤더 */}
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1 min-w-0">
                <h4 className="font-semibold text-sm text-gray-900 dark:text-gray-100 truncate">{term.term}</h4>
                <div className="flex items-center space-x-2 mt-1">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${getDifficultyColor(term.difficulty)}`}>
                    {getDifficultyText(term.difficulty)}
                  </span>
                  <span className="text-xs text-gray-600 dark:text-gray-300">{term.category}</span>
                </div>
              </div>
            </div>

            {/* 정의 */}
            <div className="mb-2">
              <p className="text-sm font-medium text-primary leading-tight">{term.definition}</p>
            </div>

            {/* 상세 설명 */}
            <div className="mb-3">
              <p 
                className="text-xs text-gray-700 dark:text-gray-300 leading-relaxed"
                style={{
                  display: '-webkit-box',
                  WebkitLineClamp: 3,
                  WebkitBoxOrient: 'vertical',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis'
                }}
              >
                {term.description}
              </p>
            </div>

            {/* 공식 (있는 경우) - 컴팩트하게 */}
            {term.formula && (
              <div className="mb-2">
                <div className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">공식</div>
                <div className="text-xs font-mono bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200 p-2 rounded border text-center">
                  {term.formula}
                </div>
              </div>
            )}

            {/* 예시 (있는 경우) - 축약 */}
            {term.example && (
              <div className="mb-2">
                <div className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">예시</div>
                <div 
                  className="text-xs bg-blue-50 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200 p-2 rounded border border-blue-200 dark:border-blue-700"
                  style={{
                    display: '-webkit-box',
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: 'vertical',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis'
                  }}
                >
                  {term.example}
                </div>
              </div>
            )}

            {/* 태그 - 최대 3개만 표시 */}
            {term.tags.length > 0 && (
              <div className="mb-3">
                <div className="flex flex-wrap gap-1">
                  {term.tags.slice(0, 3).map(tag => (
                    <span 
                      key={tag}
                      className="text-xs bg-secondary text-secondary-foreground px-1.5 py-0.5 rounded"
                    >
                      #{tag}
                    </span>
                  ))}
                  {term.tags.length > 3 && (
                    <span className="text-xs text-muted-foreground px-1">
                      +{term.tags.length - 3}
                    </span>
                  )}
                </div>
              </div>
            )}

            {/* 하단 링크 */}
            <div className="pt-2 border-t border-border">
              <button 
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  window.open(`/glossary?term=${termId}`, '_blank', 'noopener,noreferrer');
                }}
                className="text-xs text-primary hover:underline flex items-center justify-center w-full p-2 rounded hover:bg-muted/50 transition-colors"
              >
                <span>자세히 보기</span>
                <ExternalLink className="w-3 h-3 ml-1" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// 간편 사용을 위한 래퍼 컴포넌트들
export function PERTooltip({ children, ...props }: Omit<TermTooltipProps, 'termId'>) {
  return <TermTooltip termId="per" {...props}>{children}</TermTooltip>;
}

export function PBRTooltip({ children, ...props }: Omit<TermTooltipProps, 'termId'>) {
  return <TermTooltip termId="pbr" {...props}>{children}</TermTooltip>;
}

export function ROETooltip({ children, ...props }: Omit<TermTooltipProps, 'termId'>) {
  return <TermTooltip termId="roe" {...props}>{children}</TermTooltip>;
}

export function EPSTooltip({ children, ...props }: Omit<TermTooltipProps, 'termId'>) {
  return <TermTooltip termId="eps" {...props}>{children}</TermTooltip>;
}

export function BPSTooltip({ children, ...props }: Omit<TermTooltipProps, 'termId'>) {
  return <TermTooltip termId="bps" {...props}>{children}</TermTooltip>;
}

export function MarketCapTooltip({ children, ...props }: Omit<TermTooltipProps, 'termId'>) {
  return <TermTooltip termId="market_cap" {...props}>{children}</TermTooltip>;
}

export function ForeignOwnershipTooltip({ children, ...props }: Omit<TermTooltipProps, 'termId'>) {
  return <TermTooltip termId="foreign_ownership" {...props}>{children}</TermTooltip>;
}

export function UpperLimitTooltip({ children, ...props }: Omit<TermTooltipProps, 'termId'>) {
  return <TermTooltip termId="upper_limit" {...props}>{children}</TermTooltip>;
}

export function LowerLimitTooltip({ children, ...props }: Omit<TermTooltipProps, 'termId'>) {
  return <TermTooltip termId="lower_limit" {...props}>{children}</TermTooltip>;
}

export function Week52HighTooltip({ children, ...props }: Omit<TermTooltipProps, 'termId'>) {
  return <TermTooltip termId="week52_high" {...props}>{children}</TermTooltip>;
}

export function Week52LowTooltip({ children, ...props }: Omit<TermTooltipProps, 'termId'>) {
  return <TermTooltip termId="week52_low" {...props}>{children}</TermTooltip>;
}

export function EVEBITDATooltip({ children, ...props }: Omit<TermTooltipProps, 'termId'>) {
  return <TermTooltip termId="ev_ebitda" {...props}>{children}</TermTooltip>;
}

export function EnterpriseValueTooltip({ children, ...props }: Omit<TermTooltipProps, 'termId'>) {
  return <TermTooltip termId="enterprise_value" {...props}>{children}</TermTooltip>;
}

export function EBITDATooltip({ children, ...props }: Omit<TermTooltipProps, 'termId'>) {
  return <TermTooltip termId="ebitda" {...props}>{children}</TermTooltip>;
}