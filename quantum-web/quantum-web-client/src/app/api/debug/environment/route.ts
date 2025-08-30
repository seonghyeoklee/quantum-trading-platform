import { NextRequest, NextResponse } from 'next/server';
import { getEnvironmentInfo } from '@/lib/api-config';

export async function GET(request: NextRequest) {
  try {
    const environmentInfo = getEnvironmentInfo(request);
    
    return NextResponse.json({
      success: true,
      data: {
        ...environmentInfo,
        headers: {
          host: request.headers.get('host'),
          userAgent: request.headers.get('user-agent') || 'server-side',
          xForwardedFor: request.headers.get('x-forwarded-for'),
        },
        serverSide: true,
        timestamp: new Date().toISOString(),
      }
    });
  } catch (error) {
    return NextResponse.json({
      success: false,
      error: 'Failed to get environment info',
      details: error instanceof Error ? error.message : String(error)
    }, { status: 500 });
  }
}