'use client';

import { useEffect, useState } from 'react';
import { getEnvironmentInfo } from '@/lib/api-config';

// 이 페이지를 동적으로 렌더링하도록 강제
export const dynamic = 'force-dynamic';

interface EnvironmentData {
  clientSide: any;
  serverSide: any;
}

export default function EnvironmentDebugPage() {
  const [environmentData, setEnvironmentData] = useState<EnvironmentData | null>(null);
  const [loading, setLoading] = useState(true);
  const [userAgent, setUserAgent] = useState<string>('');
  const [consoleLogs, setConsoleLogs] = useState<Array<{type: string, message: string, timestamp: string}>>([]);

  // 콘솔 로그 캡처
  useEffect(() => {
    const addLog = (type: string, message: string) => {
      setConsoleLogs(prev => [...prev.slice(-49), {
        type,
        message,
        timestamp: new Date().toLocaleTimeString()
      }]);
    };

    // 원본 console 메서드 저장
    const originalLog = console.log;
    const originalError = console.error;
    const originalWarn = console.warn;

    // console 메서드 오버라이드
    console.log = (...args) => {
      originalLog(...args);
      addLog('log', args.map(arg => typeof arg === 'object' ? JSON.stringify(arg) : String(arg)).join(' '));
    };

    console.error = (...args) => {
      originalError(...args);
      addLog('error', args.map(arg => typeof arg === 'object' ? JSON.stringify(arg) : String(arg)).join(' '));
    };

    console.warn = (...args) => {
      originalWarn(...args);
      addLog('warn', args.map(arg => typeof arg === 'object' ? JSON.stringify(arg) : String(arg)).join(' '));
    };

    return () => {
      // 컴포넌트 언마운트 시 원본 메서드 복원
      console.log = originalLog;
      console.error = originalError;
      console.warn = originalWarn;
    };
  }, []);

  useEffect(() => {
    const loadEnvironmentData = async () => {
      try {
        // 클라이언트 사이드 환경 정보
        const clientSideInfo = getEnvironmentInfo();
        
        // 추가 브라우저 정보
        const browserInfo = {
          userAgent: navigator.userAgent,
          platform: navigator.platform,
          cookieEnabled: navigator.cookieEnabled,
          onLine: navigator.onLine,
          screen: {
            width: window.screen.width,
            height: window.screen.height,
            availWidth: window.screen.availWidth,
            availHeight: window.screen.availHeight,
          },
          viewport: {
            width: window.innerWidth,
            height: window.innerHeight,
          },
          isMobile: /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent),
          isIOS: /iPad|iPhone|iPod/.test(navigator.userAgent),
          isAndroid: /Android/.test(navigator.userAgent),
        };

        setUserAgent(navigator.userAgent);
        
        // 서버 사이드 환경 정보 (API 호출)
        const response = await fetch('/api/debug/environment');
        const serverSideResult = await response.json();
        
        setEnvironmentData({
          clientSide: {
            ...clientSideInfo,
            ...browserInfo,
            currentURL: window.location.href,
            timestamp: new Date().toISOString(),
          },
          serverSide: serverSideResult.data,
        });
      } catch (error) {
        console.error('Failed to load environment data:', error);
        setEnvironmentData({
          clientSide: {
            ...getEnvironmentInfo(),
            error: 'Failed to load environment data',
            errorDetails: error instanceof Error ? error.message : String(error),
            currentURL: window.location.href,
            userAgent: navigator.userAgent,
            isMobile: /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent),
          },
          serverSide: { error: 'Failed to fetch server-side data' },
        });
      } finally {
        setLoading(false);
      }
    };

    loadEnvironmentData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 py-8">
        <div className="max-w-4xl mx-auto px-4">
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="animate-pulse">Loading environment data...</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 py-4 px-2 md:py-8 md:px-4">
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900">Environment Debug Info</h1>
          <p className="text-gray-600 mt-2 text-sm md:text-base">
            API configuration and host detection debugging information
          </p>
          <p className="text-xs text-gray-500 mt-1">
            빌드 버전: v2.1 - 향상된 디버깅 메시지 (2024-08-30)
          </p>
          {userAgent && (
            <div className="mt-2 p-2 bg-blue-100 rounded-lg">
              <p className="text-xs md:text-sm text-blue-800">
                <strong>Device:</strong> {environmentData?.clientSide?.isMobile ? '📱 Mobile' : '💻 Desktop'}
                {environmentData?.clientSide?.isIOS && ' (iOS)'}
                {environmentData?.clientSide?.isAndroid && ' (Android)'}
              </p>
              {environmentData?.clientSide?.isMobile && (
                <div className="mt-2 text-xs">
                  <div className="text-green-700">
                    ✅ 현재 API URL: <code>{environmentData?.clientSide?.apiBaseUrl}</code>
                  </div>
                  <div className="text-green-700">
                    ✅ 현재 Kiwoom URL: <code>{environmentData?.clientSide?.kiwoomAdapterUrl}</code>
                  </div>
                  {environmentData?.clientSide?.host === '100.68.90.21' ? (
                    <div className="text-green-700 font-semibold">🎯 올바른 Tailscale IP 접근!</div>
                  ) : (
                    <div className="text-orange-700 font-semibold">⚠️ localhost 접근 - 모바일에서는 API 호출 실패 가능</div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        <div className="space-y-6">
          {/* Client Side Info */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
              <span className="w-3 h-3 bg-blue-500 rounded-full mr-2"></span>
              Client Side Environment
            </h2>
            <pre className="bg-gray-100 p-4 rounded-lg overflow-x-auto text-sm">
              {JSON.stringify(environmentData?.clientSide, null, 2)}
            </pre>
          </div>

          {/* Server Side Info */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
              <span className="w-3 h-3 bg-green-500 rounded-full mr-2"></span>
              Server Side Environment
            </h2>
            <pre className="bg-gray-100 p-4 rounded-lg overflow-x-auto text-sm">
              {JSON.stringify(environmentData?.serverSide, null, 2)}
            </pre>
          </div>

          {/* API Test Buttons */}
          <div className="bg-white rounded-lg shadow-lg p-4 md:p-6">
            <h2 className="text-lg md:text-xl font-semibold text-gray-900 mb-4 flex items-center">
              <span className="w-3 h-3 bg-yellow-500 rounded-full mr-2"></span>
              API Connection Tests
            </h2>
            <div className="space-y-4">
              <APITestButton
                name="Web API Health Check"
                url={`${environmentData?.clientSide?.apiBaseUrl}/actuator/health`}
              />
              <APITestButton
                name="Kiwoom Adapter Health Check"
                url={`${environmentData?.clientSide?.kiwoomAdapterUrl}/health`}
              />
              {/* 모바일 전용 네트워크 진단 */}
              {environmentData?.clientSide?.isMobile && (
                <div className="bg-blue-50 p-3 rounded-lg border border-blue-200">
                  <h4 className="text-sm font-semibold text-blue-800 mb-2">📱 모바일 네트워크 진단</h4>
                  <p className="text-xs text-blue-700 mb-2">
                    모바일에서는 localhost 접근이 불가능합니다. 
                    Tailscale VPN을 통해 외부 IP로만 접근할 수 있습니다.
                  </p>
                  <div className="text-xs text-blue-600">
                    <div>✅ 정상: <code>http://100.68.90.21:XXXX</code></div>
                    <div>❌ 불가능: <code>http://localhost:XXXX</code></div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* 실시간 콘솔 로그 */}
          <div className="bg-white rounded-lg shadow-lg p-4 md:p-6">
            <h2 className="text-lg md:text-xl font-semibold text-gray-900 mb-4 flex items-center">
              <span className="w-3 h-3 bg-red-500 rounded-full mr-2"></span>
              실시간 콘솔 로그 (모바일 디버깅용)
              <button 
                onClick={() => setConsoleLogs([])}
                className="ml-auto text-xs bg-gray-200 px-2 py-1 rounded hover:bg-gray-300"
              >
                지우기
              </button>
            </h2>
            <div className="bg-black text-green-400 p-3 rounded-lg h-64 overflow-y-auto font-mono text-xs">
              {consoleLogs.length === 0 ? (
                <div className="text-gray-500">
                  콘솔 로그가 여기에 표시됩니다... API 테스트 버튼을 눌러보세요!
                </div>
              ) : (
                consoleLogs.map((log, index) => (
                  <div key={index} className={`mb-1 ${
                    log.type === 'error' ? 'text-red-400' : 
                    log.type === 'warn' ? 'text-yellow-400' : 
                    'text-green-400'
                  }`}>
                    <span className="text-gray-400">[{log.timestamp}]</span> {log.message}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function APITestButton({ name, url }: { name: string; url: string }) {
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [result, setResult] = useState<any>(null);

  const testAPI = async () => {
    setStatus('loading');
    console.log(`🔍 API 테스트 시작: ${url}`);
    
    try {
      const startTime = Date.now();
      const response = await fetch(url);
      const endTime = Date.now();
      
      console.log(`📊 응답 시간: ${endTime - startTime}ms, 상태: ${response.status}`);
      
      const data = await response.json();
      setResult({ 
        status: response.status, 
        responseTime: `${endTime - startTime}ms`,
        headers: Object.fromEntries(response.headers.entries()),
        data 
      });
      setStatus('success');
      
      console.log(`✅ API 성공: ${url}`);
    } catch (error) {
      const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
      const hostname = window.location.hostname;
      
      // 모바일 디버깅 상세 정보
      let debugInfo = '';
      if (isMobile) {
        debugInfo = `📱 모바일 디버깅 정보:
- 현재 접근 URL: ${window.location.href}
- API 호출 URL: ${url}
- 현재 호스트: ${hostname}
- 프로토콜: ${window.location.protocol}
- 네트워크 상태: ${navigator.onLine ? '온라인' : '오프라인'}
- Tailscale IP 접근: ${hostname === '100.68.90.21' ? '✅ 정상' : '❌ localhost 접근'}

💡 모바일 해결책:
${hostname === 'localhost' || hostname === '127.0.0.1' ? 
  '- Tailscale VPN으로 http://100.68.90.21:10301 접속하세요\n- localhost는 모바일에서 접근 불가능합니다' :
  '- Mixed Content Policy 확인 필요\n- HTTPS를 사용하거나 브라우저 설정을 변경하세요'
}`;
      }
      
      const errorDetails = {
        error: error instanceof Error ? error.message : String(error),
        type: error instanceof Error ? error.constructor.name : 'Unknown',
        stack: error instanceof Error ? error.stack : undefined,
        url: url,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        isMobile,
        hostname,
        protocol: window.location.protocol,
        isOnline: navigator.onLine,
        debugInfo: isMobile ? debugInfo : '데스크톱 환경에서는 일반적으로 localhost 접근이 가능합니다.',
      };
      
      setResult(errorDetails);
      setStatus('error');
      
      console.error(`❌ API 실패: ${url}`, errorDetails);
      
      // Mixed Content 정책 위반 체크
      if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
        console.warn('🚨 Mixed Content Policy 위반 가능성');
        console.warn('💡 해결책: HTTPS 사용하거나 브라우저 설정 변경');
        if (isMobile) {
          console.warn(debugInfo);
        }
      }
    }
  };

  const statusColors = {
    idle: 'bg-gray-500',
    loading: 'bg-yellow-500',
    success: 'bg-green-500',
    error: 'bg-red-500',
  };

  return (
    <div className="border rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-medium">{name}</h3>
        <button
          onClick={testAPI}
          disabled={status === 'loading'}
          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
        >
          {status === 'loading' ? 'Testing...' : 'Test'}
        </button>
      </div>
      <p className="text-sm text-gray-600 mb-2">{url}</p>
      {result && (
        <div className="bg-gray-100 p-2 rounded text-xs">
          <div className="flex items-center mb-1">
            <span className={`w-2 h-2 rounded-full ${statusColors[status]} mr-2`}></span>
            <span className="font-medium">{status.toUpperCase()}</span>
          </div>
          
          {status === 'error' && (
            <div className="mb-3 p-3 bg-red-100 border-2 border-red-300 rounded-lg text-red-900">
              <div className="font-bold text-red-900 mb-2 text-sm">🚨 API 로드 실패!</div>
              {result.debugInfo ? (
                <pre className="whitespace-pre-wrap text-xs bg-red-50 p-2 rounded border">{result.debugInfo}</pre>
              ) : (
                <div className="text-xs">
                  <div>에러: {result.error}</div>
                  <div>URL: {result.url}</div>
                  <div>시간: {result.timestamp}</div>
                </div>
              )}
            </div>
          )}
          
          <details className="cursor-pointer">
            <summary className="font-medium mb-2">기술적 세부 정보 보기</summary>
            <pre>{JSON.stringify(result, null, 2)}</pre>
          </details>
        </div>
      )}
    </div>
  );
}