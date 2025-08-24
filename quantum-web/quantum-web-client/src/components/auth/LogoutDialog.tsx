'use client';

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { LogOut } from "lucide-react";

interface LogoutDialogProps {
  onLogout: () => Promise<void>;
  children?: React.ReactNode;
}

export default function LogoutDialog({ onLogout, children }: LogoutDialogProps) {
  const handleLogout = async () => {
    try {
      await onLogout();
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  return (
    <AlertDialog>
      <AlertDialogTrigger asChild>
        {children || (
          <Button
            variant="ghost"
            size="sm"
            className="text-muted-foreground hover:text-destructive"
          >
            <LogOut className="w-4 h-4" />
          </Button>
        )}
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>로그아웃 확인</AlertDialogTitle>
          <AlertDialogDescription>
            정말 로그아웃하시겠습니까? 현재 세션이 종료되고 로그인 페이지로 이동합니다.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>취소</AlertDialogCancel>
          <AlertDialogAction
            onClick={handleLogout}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            <LogOut className="w-4 h-4 mr-2" />
            로그아웃
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}