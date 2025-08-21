'use client';

import React, { useState } from 'react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AdminLayout } from '@/components/layout/AdminLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Settings,
  Server,
  Database,
  Shield,
  Bell,
  Globe,
  Save,
  RefreshCw,
  Download,
  Upload,
  AlertTriangle,
  CheckCircle,
  Activity,
  Cpu,
  HardDrive,
  Network,
  Clock
} from 'lucide-react';

interface SystemStatus {
  component: string;
  status: 'healthy' | 'warning' | 'error';
  value: string;
  description: string;
  lastChecked: string;
}

const mockSystemStatus: SystemStatus[] = [
  {
    component: 'API 서버',
    status: 'healthy',
    value: '99.9%',
    description: '정상 운영 중',
    lastChecked: '2024-01-15T11:30:00Z'
  },
  {
    component: 'PostgreSQL',
    status: 'healthy',
    value: '< 50ms',
    description: '응답 시간 정상',
    lastChecked: '2024-01-15T11:30:00Z'
  },
  {
    component: 'Redis 캐시',
    status: 'healthy',
    value: '98.5%',
    description: '캐시 히트율',
    lastChecked: '2024-01-15T11:30:00Z'
  },
  {
    component: 'WebSocket 서버',
    status: 'healthy',
    value: '실행 중',
    description: '실시간 연결 활성',
    lastChecked: '2024-01-15T11:30:00Z'
  },
  {
    component: '브로커 API',
    status: 'warning',
    value: '지연',
    description: '일부 지연 발생',
    lastChecked: '2024-01-15T11:29:00Z'
  }
];

export default function SettingsPage() {
  const [isDirty, setIsDirty] = useState(false);
  const [saving, setSaving] = useState(false);

  const getStatusIcon = (status: SystemStatus['status']) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
      case 'error':
        return <AlertTriangle className="h-4 w-4 text-red-600" />;
      default:
        return <Activity className="h-4 w-4 text-gray-600" />;
    }
  };

  const getStatusColor = (status: SystemStatus['status']) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-100 text-green-800';
      case 'warning':
        return 'bg-yellow-100 text-yellow-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      // API 호출 시뮬레이션
      await new Promise(resolve => setTimeout(resolve, 1000));
      setIsDirty(false);
    } catch (error) {
      console.error('설정 저장 실패:', error);
    } finally {
      setSaving(false);
    }
  };

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('ko-KR');
  };

  return (
    <ProtectedRoute requiredRoles={['ADMIN']}>
      <AdminLayout>
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">시스템 설정</h1>
              <p className="text-muted-foreground">
                시스템 구성과 운영 파라미터를 관리하세요.
              </p>
            </div>
            <div className="flex gap-2 mt-4 sm:mt-0">
              <Button variant="outline">
                <Download className="h-4 w-4 mr-2" />
                설정 내보내기
              </Button>
              <Button variant="outline">
                <Upload className="h-4 w-4 mr-2" />
                설정 가져오기
              </Button>
              <Button onClick={handleSave} disabled={!isDirty || saving}>
                {saving ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    저장 중
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-2" />
                    설정 저장
                  </>
                )}
              </Button>
            </div>
          </div>

          {/* 저장되지 않은 변경사항 알림 */}
          {isDirty && (
            <Alert className="border-yellow-200 bg-yellow-50">
              <AlertTriangle className="h-4 w-4 text-yellow-600" />
              <AlertDescription>
                <div className="flex items-center justify-between">
                  <span>저장되지 않은 변경사항이 있습니다.</span>
                  <Button size="sm" onClick={handleSave}>
                    지금 저장
                  </Button>
                </div>
              </AlertDescription>
            </Alert>
          )}

          <Tabs defaultValue="system" className="space-y-6">
            <TabsList className="grid w-full grid-cols-5">
              <TabsTrigger value="system">시스템 상태</TabsTrigger>
              <TabsTrigger value="database">데이터베이스</TabsTrigger>
              <TabsTrigger value="security">보안</TabsTrigger>
              <TabsTrigger value="notifications">알림</TabsTrigger>
              <TabsTrigger value="api">API 설정</TabsTrigger>
            </TabsList>

            <TabsContent value="system" className="space-y-6">
              {/* 시스템 상태 */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Server className="h-5 w-5 mr-2" />
                    시스템 상태 모니터링
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {mockSystemStatus.map((status, index) => (
                      <div
                        key={index}
                        className="p-4 border rounded-lg space-y-2"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-medium">{status.component}</span>
                          {getStatusIcon(status.status)}
                        </div>
                        
                        <div className="space-y-1">
                          <div className="text-2xl font-bold">
                            {status.value}
                          </div>
                          <Badge className={getStatusColor(status.status)}>
                            {status.description}
                          </Badge>
                        </div>
                        
                        <div className="text-xs text-gray-500">
                          마지막 확인: {formatTime(status.lastChecked)}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* 시스템 리소스 */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Cpu className="h-5 w-5 mr-2" />
                    시스템 리소스
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">CPU 사용률</span>
                        <span className="text-sm text-gray-600">23%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div className="bg-blue-500 h-2 rounded-full" style={{ width: '23%' }} />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">메모리 사용률</span>
                        <span className="text-sm text-gray-600">67%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div className="bg-green-500 h-2 rounded-full" style={{ width: '67%' }} />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">디스크 사용률</span>
                        <span className="text-sm text-gray-600">45%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div className="bg-yellow-500 h-2 rounded-full" style={{ width: '45%' }} />
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* 성능 설정 */}
              <Card>
                <CardHeader>
                  <CardTitle>성능 최적화 설정</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-medium">캐시 자동 정리</div>
                        <div className="text-sm text-gray-600">매시간 미사용 캐시 데이터 삭제</div>
                      </div>
                      <input 
                        type="checkbox" 
                        className="rounded" 
                        defaultChecked
                        onChange={() => setIsDirty(true)}
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-medium">데이터베이스 연결 풀링</div>
                        <div className="text-sm text-gray-600">연결 풀 최적화로 성능 향상</div>
                      </div>
                      <input 
                        type="checkbox" 
                        className="rounded" 
                        defaultChecked
                        onChange={() => setIsDirty(true)}
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-medium">압축 전송</div>
                        <div className="text-sm text-gray-600">API 응답 데이터 압축</div>
                      </div>
                      <input 
                        type="checkbox" 
                        className="rounded" 
                        defaultChecked
                        onChange={() => setIsDirty(true)}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="database" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Database className="h-5 w-5 mr-2" />
                    데이터베이스 설정
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium mb-2">
                          최대 연결 수
                        </label>
                        <input
                          type="number"
                          className="w-full p-2 border border-gray-300 rounded-md"
                          defaultValue={100}
                          onChange={() => setIsDirty(true)}
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium mb-2">
                          연결 타임아웃 (초)
                        </label>
                        <input
                          type="number"
                          className="w-full p-2 border border-gray-300 rounded-md"
                          defaultValue={30}
                          onChange={() => setIsDirty(true)}
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium mb-2">
                          백업 주기
                        </label>
                        <select 
                          className="w-full p-2 border border-gray-300 rounded-md"
                          onChange={() => setIsDirty(true)}
                        >
                          <option value="daily">매일</option>
                          <option value="weekly">매주</option>
                          <option value="monthly">매월</option>
                        </select>
                      </div>
                    </div>

                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium mb-2">
                          백업 보관 기간 (일)
                        </label>
                        <input
                          type="number"
                          className="w-full p-2 border border-gray-300 rounded-md"
                          defaultValue={30}
                          onChange={() => setIsDirty(true)}
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium mb-2">
                          로그 보관 기간 (일)
                        </label>
                        <input
                          type="number"
                          className="w-full p-2 border border-gray-300 rounded-md"
                          defaultValue={90}
                          onChange={() => setIsDirty(true)}
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium mb-2">
                          인덱스 최적화 주기
                        </label>
                        <select 
                          className="w-full p-2 border border-gray-300 rounded-md"
                          onChange={() => setIsDirty(true)}
                        >
                          <option value="daily">매일</option>
                          <option value="weekly">매주</option>
                          <option value="monthly">매월</option>
                        </select>
                      </div>
                    </div>
                  </div>

                  <div className="mt-6 pt-6 border-t">
                    <div className="flex gap-2">
                      <Button variant="outline">
                        <Database className="h-4 w-4 mr-2" />
                        수동 백업
                      </Button>
                      <Button variant="outline">
                        <RefreshCw className="h-4 w-4 mr-2" />
                        인덱스 재구성
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="security" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Shield className="h-5 w-5 mr-2" />
                    보안 설정
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    <div className="space-y-4">
                      <h4 className="font-medium">인증 설정</h4>
                      
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-medium">JWT 토큰 만료 시간</div>
                          <div className="text-sm text-gray-600">액세스 토큰 유효 기간</div>
                        </div>
                        <div className="flex items-center gap-2">
                          <input
                            type="number"
                            className="w-16 p-1 text-sm border rounded text-right"
                            defaultValue={24}
                            onChange={() => setIsDirty(true)}
                          />
                          <span className="text-sm">시간</span>
                        </div>
                      </div>

                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-medium">리프레시 토큰 만료 시간</div>
                          <div className="text-sm text-gray-600">리프레시 토큰 유효 기간</div>
                        </div>
                        <div className="flex items-center gap-2">
                          <input
                            type="number"
                            className="w-16 p-1 text-sm border rounded text-right"
                            defaultValue={7}
                            onChange={() => setIsDirty(true)}
                          />
                          <span className="text-sm">일</span>
                        </div>
                      </div>

                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-medium">최대 로그인 실패 횟수</div>
                          <div className="text-sm text-gray-600">계정 잠금 전 최대 시도 횟수</div>
                        </div>
                        <div className="flex items-center gap-2">
                          <input
                            type="number"
                            className="w-16 p-1 text-sm border rounded text-right"
                            defaultValue={5}
                            onChange={() => setIsDirty(true)}
                          />
                          <span className="text-sm">회</span>
                        </div>
                      </div>
                    </div>

                    <div className="space-y-4 pt-6 border-t">
                      <h4 className="font-medium">보안 정책</h4>
                      
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-medium">2단계 인증 필수</div>
                          <div className="text-sm text-gray-600">모든 관리자 계정에 2FA 적용</div>
                        </div>
                        <input 
                          type="checkbox" 
                          className="rounded" 
                          defaultChecked
                          onChange={() => setIsDirty(true)}
                        />
                      </div>

                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-medium">세션 동시 제한</div>
                          <div className="text-sm text-gray-600">사용자별 동시 세션 수 제한</div>
                        </div>
                        <input 
                          type="checkbox" 
                          className="rounded" 
                          defaultChecked
                          onChange={() => setIsDirty(true)}
                        />
                      </div>

                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-medium">IP 화이트리스트</div>
                          <div className="text-sm text-gray-600">허용된 IP에서만 접근 가능</div>
                        </div>
                        <input 
                          type="checkbox" 
                          className="rounded"
                          onChange={() => setIsDirty(true)}
                        />
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="notifications" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Bell className="h-5 w-5 mr-2" />
                    알림 설정
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    <div className="space-y-4">
                      <h4 className="font-medium">시스템 알림</h4>
                      
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-medium">서버 다운 알림</div>
                          <div className="text-sm text-gray-600">시스템 장애 발생 시 즉시 알림</div>
                        </div>
                        <input 
                          type="checkbox" 
                          className="rounded" 
                          defaultChecked
                          onChange={() => setIsDirty(true)}
                        />
                      </div>

                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-medium">성능 임계치 알림</div>
                          <div className="text-sm text-gray-600">CPU, 메모리 사용률 임계치 초과 시</div>
                        </div>
                        <input 
                          type="checkbox" 
                          className="rounded" 
                          defaultChecked
                          onChange={() => setIsDirty(true)}
                        />
                      </div>

                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-medium">보안 이벤트 알림</div>
                          <div className="text-sm text-gray-600">비정상적인 로그인 시도 등</div>
                        </div>
                        <input 
                          type="checkbox" 
                          className="rounded" 
                          defaultChecked
                          onChange={() => setIsDirty(true)}
                        />
                      </div>
                    </div>

                    <div className="space-y-4 pt-6 border-t">
                      <h4 className="font-medium">거래 알림</h4>
                      
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-medium">대량 거래 알림</div>
                          <div className="text-sm text-gray-600">설정 금액 이상 거래 시 알림</div>
                        </div>
                        <input 
                          type="checkbox" 
                          className="rounded" 
                          defaultChecked
                          onChange={() => setIsDirty(true)}
                        />
                      </div>

                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-medium">위험 임계치 알림</div>
                          <div className="text-sm text-gray-600">포트폴리오 위험도 임계치 초과</div>
                        </div>
                        <input 
                          type="checkbox" 
                          className="rounded" 
                          defaultChecked
                          onChange={() => setIsDirty(true)}
                        />
                      </div>
                    </div>

                    <div className="space-y-4 pt-6 border-t">
                      <h4 className="font-medium">알림 채널</h4>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium mb-2">
                            이메일 주소
                          </label>
                          <input
                            type="email"
                            className="w-full p-2 border border-gray-300 rounded-md"
                            defaultValue="admin@quantum-trading.com"
                            onChange={() => setIsDirty(true)}
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium mb-2">
                            Slack 웹훅 URL
                          </label>
                          <input
                            type="url"
                            className="w-full p-2 border border-gray-300 rounded-md"
                            placeholder="https://hooks.slack.com/..."
                            onChange={() => setIsDirty(true)}
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="api" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Globe className="h-5 w-5 mr-2" />
                    API 설정
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    <div className="space-y-4">
                      <h4 className="font-medium">브로커 API 설정</h4>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium mb-2">
                            한국투자증권 API URL
                          </label>
                          <input
                            type="url"
                            className="w-full p-2 border border-gray-300 rounded-md"
                            defaultValue="https://openapi.koreainvestment.com"
                            onChange={() => setIsDirty(true)}
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium mb-2">
                            API 타임아웃 (초)
                          </label>
                          <input
                            type="number"
                            className="w-full p-2 border border-gray-300 rounded-md"
                            defaultValue={10}
                            onChange={() => setIsDirty(true)}
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium mb-2">
                            최대 재시도 횟수
                          </label>
                          <input
                            type="number"
                            className="w-full p-2 border border-gray-300 rounded-md"
                            defaultValue={3}
                            onChange={() => setIsDirty(true)}
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium mb-2">
                            Rate Limit (req/min)
                          </label>
                          <input
                            type="number"
                            className="w-full p-2 border border-gray-300 rounded-md"
                            defaultValue={100}
                            onChange={() => setIsDirty(true)}
                          />
                        </div>
                      </div>
                    </div>

                    <div className="space-y-4 pt-6 border-t">
                      <h4 className="font-medium">WebSocket 설정</h4>
                      
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-medium">자동 재연결</div>
                          <div className="text-sm text-gray-600">연결 끊김 시 자동으로 재연결</div>
                        </div>
                        <input 
                          type="checkbox" 
                          className="rounded" 
                          defaultChecked
                          onChange={() => setIsDirty(true)}
                        />
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium mb-2">
                            Heartbeat 간격 (초)
                          </label>
                          <input
                            type="number"
                            className="w-full p-2 border border-gray-300 rounded-md"
                            defaultValue={30}
                            onChange={() => setIsDirty(true)}
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium mb-2">
                            최대 동시 연결 수
                          </label>
                          <input
                            type="number"
                            className="w-full p-2 border border-gray-300 rounded-md"
                            defaultValue={1000}
                            onChange={() => setIsDirty(true)}
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </AdminLayout>
    </ProtectedRoute>
  );
}