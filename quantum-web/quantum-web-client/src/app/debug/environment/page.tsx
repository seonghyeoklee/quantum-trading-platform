'use client';

import { useEffect, useState } from 'react';
import { getEnvironmentInfo } from '@/lib/api-config';

interface EnvironmentData {
  clientSide: any;
  serverSide: any;
}

export default function EnvironmentDebugPage() {
  const [environmentData, setEnvironmentData] = useState<EnvironmentData | null>(null);
  const [loading, setLoading] = useState(true);
  const [userAgent, setUserAgent] = useState<string>('');

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
          {userAgent && (
            <div className="mt-2 p-2 bg-blue-100 rounded-lg">
              <p className="text-xs md:text-sm text-blue-800">
                <strong>Device:</strong> {environmentData?.clientSide?.isMobile ? '📱 Mobile' : '💻 Desktop'}
                {environmentData?.clientSide?.isIOS && ' (iOS)'}
                {environmentData?.clientSide?.isAndroid && ' (Android)'}
              </p>
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
              {/* 모바일 전용 추가 테스트 */}
              {environmentData?.clientSide?.isMobile && (
                <>
                  <APITestButton
                    name="Direct Localhost Test (Mobile)"
                    url="http://localhost:10101/actuator/health"
                  />
                  <APITestButton
                    name="Direct Tailscale Test (Mobile)"
                    url="http://100.68.90.21:10101/actuator/health"
                  />
                </>
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
    try {
      const response = await fetch(url);
      const data = await response.json();
      setResult({ status: response.status, data });
      setStatus('success');
    } catch (error) {
      setResult({ error: error instanceof Error ? error.message : String(error) });
      setStatus('error');
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
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}