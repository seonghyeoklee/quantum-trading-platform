'use client';

import { useTheme } from 'next-themes';
import { useEffect, useState } from 'react';

export function ThemeDebug() {
  const { theme, resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return <div className="p-4 bg-muted rounded-lg">Loading theme debug...</div>;
  }

  return (
    <div className="fixed bottom-4 right-4 p-4 bg-background border border-border rounded-lg shadow-lg z-50 text-sm">
      <h3 className="font-semibold mb-2 text-foreground">Theme Debug</h3>
      <div className="space-y-1 text-xs">
        <div className="text-muted-foreground">Theme: <span className="text-foreground font-mono">{theme}</span></div>
        <div className="text-muted-foreground">Resolved: <span className="text-foreground font-mono">{resolvedTheme}</span></div>
        <div className="text-muted-foreground">HTML class: <span className="text-foreground font-mono">{typeof window !== 'undefined' ? document.documentElement.classList.toString() : 'N/A'}</span></div>
        <div className="text-muted-foreground">Background color: <span className="text-foreground font-mono">{typeof window !== 'undefined' ? getComputedStyle(document.documentElement).getPropertyValue('--background') : 'N/A'}</span></div>
      </div>
      <div className="flex gap-2 mt-3">
        <button 
          onClick={() => setTheme('light')} 
          className="px-2 py-1 text-xs bg-white text-black border rounded hover:bg-gray-100"
        >
          Light
        </button>
        <button 
          onClick={() => setTheme('dark')} 
          className="px-2 py-1 text-xs bg-black text-white border rounded hover:bg-gray-900"
        >
          Dark
        </button>
        <button 
          onClick={() => setTheme('system')} 
          className="px-2 py-1 text-xs bg-blue-500 text-white border rounded hover:bg-blue-600"
        >
          System
        </button>
      </div>
    </div>
  );
}