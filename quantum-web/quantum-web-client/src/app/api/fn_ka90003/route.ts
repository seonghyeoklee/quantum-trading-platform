import { NextRequest, NextResponse } from 'next/server';

const KIWOOM_ADAPTER_BASE_URL = process.env.KIWOOM_ADAPTER_URL || 'http://localhost:8100';

export async function POST(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const contYn = searchParams.get('cont_yn') || 'N';
    
    const body = await request.json();
    
    // 연속조회를 위한 헤더 구성
    const headers: Record<string, string> = {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
    };
    
    // 클라이언트에서 전달한 연속조회 헤더 추가
    const apiId = request.headers.get('api-id');
    const clientContYn = request.headers.get('cont-yn');
    const nextKey = request.headers.get('next-key');
    
    if (apiId) headers['api-id'] = apiId;
    if (clientContYn === 'Y' && nextKey) {
      headers['cont-yn'] = 'Y';
      headers['next-key'] = nextKey;
    }
    
    const response = await fetch(`${KIWOOM_ADAPTER_BASE_URL}/api/fn_ka90003?cont_yn=${contYn}`, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      console.error('Kiwoom API Error:', response.status, response.statusText);
      return NextResponse.json(
        { error: `키움 API 호출 실패: ${response.status} ${response.statusText}` },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
    
  } catch (error) {
    console.error('API Proxy Error:', error);
    return NextResponse.json(
      { error: '프로그램 거래 데이터 조회 중 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}