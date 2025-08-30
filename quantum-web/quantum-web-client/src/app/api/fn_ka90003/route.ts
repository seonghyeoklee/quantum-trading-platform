import { NextRequest, NextResponse } from 'next/server';

const KIWOOM_ADAPTER_URL = process.env.KIWOOM_ADAPTER_URL || 'http://localhost:10201';

export async function POST(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const cont_yn = searchParams.get('cont_yn') || 'N';
    
    const body = await request.json();
    
    const response = await fetch(`${KIWOOM_ADAPTER_URL}/api/fn_ka90003?cont_yn=${cont_yn}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      return NextResponse.json(
        { error: `키움 API 호출 실패: ${response.status}` },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);

  } catch (error) {
    console.error('fn_ka90003 API 오류:', error);
    return NextResponse.json(
      { error: '기관/외국인 순매수 정보 조회 중 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}