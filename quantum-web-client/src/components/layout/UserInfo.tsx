'use client';

import { useAuth } from '@/contexts/AuthContext';
import { Badge } from '@/components/ui/badge';
import { useEffect, useState } from 'react';

export default function UserInfo() {
  const { user, isLoading } = useAuth();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    console.log('UserInfo render:', { mounted, isLoading, hasUser: !!user, user });
  }, [mounted, isLoading, user]);

  // 클라이언트에서 마운트되기 전에는 로딩 표시
  if (!mounted) {
    return (
      <div className="text-right">
        <div className="w-16 h-4 bg-muted animate-pulse rounded mb-1"></div>
        <div className="w-12 h-3 bg-muted animate-pulse rounded"></div>
      </div>
    );
  }

  // 로딩 중이면 로딩 표시
  if (isLoading) {
    return (
      <div className="text-right">
        <div className="w-16 h-4 bg-muted animate-pulse rounded mb-1"></div>
        <div className="w-12 h-3 bg-muted animate-pulse rounded"></div>
      </div>
    );
  }

  // 사용자 정보가 없으면 아무것도 표시하지 않음
  if (!user) {
    return null;
  }

  // 사용자 정보 표시
  return (
    <div className="text-right">
      <p className="text-sm font-medium">{user.username}</p>
      <div className="flex items-center justify-end space-x-1">
        <Badge variant="secondary" className="text-xs">
          {user.roles?.[0] || 'USER'}
        </Badge>
      </div>
    </div>
  );
}