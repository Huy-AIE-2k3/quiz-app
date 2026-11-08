/**
 * Server Wake-Up & Connectivity Banner.
 *
 * Displays friendly progress notice when free-tier cloud server is spinning up from cold sleep (>3s delay),
 * polls /healthz automatically, and displays retry button if unreachable after 90s.
 */

import React, { useEffect, useState } from 'react';
import { serverStateManager, ServerConnectionStatus, pollServerHealth } from '../../lib/api';
import { VI } from '../../lib/i18n/vi';
import { Button } from '../ui/Button';

export const ServerWakeBanner: React.FC = () => {
  const [status, setStatus] = useState<ServerConnectionStatus>('idle');
  const [isRetrying, setIsRetrying] = useState(false);

  useEffect(() => {
    return serverStateManager.subscribe((newStatus) => {
      setStatus(newStatus);
    });
  }, []);

  if (status === 'idle' || status === 'online') {
    return null;
  }

  const handleManualRetry = async () => {
    setIsRetrying(true);
    await pollServerHealth(15_000, 2_000);
    setIsRetrying(false);
  };

  return (
    <aside
      role="status"
      aria-live="polite"
      className="fixed top-0 left-0 right-0 z-50 p-3 bg-amber-500/10 border-b border-amber-500/20 backdrop-blur-md text-amber-300"
    >
      <div className="max-w-5xl mx-auto flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center space-x-2">
          {status === 'waking' && (
            <span className="w-2.5 h-2.5 rounded-full bg-amber-400 animate-ping inline-block" />
          )}
          {status === 'unreachable' && (
            <span className="w-2.5 h-2.5 rounded-full bg-red-400 inline-block" />
          )}
          <div>
            <span className="font-semibold mr-1.5">
              {status === 'waking' ? VI.server.wakingTitle : VI.server.unreachableTitle}
            </span>
            <span className="text-text-secondary">
              {status === 'waking' ? VI.server.wakingMessage : VI.server.unreachableMessage}
            </span>
          </div>
        </div>

        {status === 'unreachable' && (
          <Button
            size="sm"
            variant="outline"
            onClick={handleManualRetry}
            disabled={isRetrying}
            className="text-xs"
          >
            {isRetrying ? VI.common.loading : VI.common.retry}
          </Button>
        )}
      </div>
    </aside>
  );
};

