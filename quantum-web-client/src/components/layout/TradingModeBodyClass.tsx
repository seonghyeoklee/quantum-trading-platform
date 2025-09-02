'use client';

import { useTradingMode } from '@/contexts/TradingModeContext';
import { useEffect, useState } from 'react';

export default function TradingModeBodyClass() {
  const { isProduction, loading } = useTradingMode();
  const [isTransitioning, setIsTransitioning] = useState(false);

  useEffect(() => {
    if (!loading) {
      // Add transition effect
      setIsTransitioning(true);
      document.body.style.transition = 'all 0.5s ease-in-out';
      
      // Add a slight delay to show transition effect
      setTimeout(() => {
        // Remove any existing trading mode classes
        document.body.classList.remove('trading-mode-production', 'trading-mode-sandbox');
        
        // Add current trading mode class
        if (isProduction) {
          document.body.classList.add('trading-mode-production');
        } else {
          document.body.classList.add('trading-mode-sandbox');
        }
        
        // Reset transition after animation completes
        setTimeout(() => {
          setIsTransitioning(false);
          document.body.style.transition = '';
        }, 500);
      }, 50);
    }
  }, [isProduction, loading]);

  // Show visual feedback during mode transition
  return isTransitioning ? (
    <div className="fixed top-0 left-0 right-0 z-[9999] h-1 overflow-hidden">
      <div className="h-full bg-gradient-to-r from-transparent via-primary to-transparent animate-pulse"></div>
    </div>
  ) : null;
}