import { NextResponse } from 'next/server';
import { getEnvironmentInfo } from '@/lib/api-config';

export async function GET() {
  try {
    const environmentInfo = getEnvironmentInfo();
    
    return NextResponse.json({
      success: true,
      data: {
        ...environmentInfo,
        headers: {
          // Add server-side header information if needed
          userAgent: process.env.HTTP_USER_AGENT || 'server-side',
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