/**
 * Storage Fallback Warning Banner.
 *
 * Appears when browser blocks localStorage (strict incognito, iframe sandbox, or security restrictions).
 */

import React, { useState } from 'react';
import { safeStorage } from '../../lib/storage';
import { VI } from '../../lib/i18n/vi';
import { Button } from '../ui/Button';

export const StorageWarningBanner: React.FC = () => {
  const [dismissed, setDismissed] = useState(false);
  const isFallback = safeStorage.isMemoryFallback();

  if (!isFallback || dismissed) {
    return null;
  }

  return (
    <aside
      role="alert"
      className="bg-amber-950/40 border-b border-amber-500/30 p-2.5 text-xs text-amber-200"
    >
      <div className="max-w-5xl mx-auto flex items-center justify-between gap-3">
        <div className="flex items-center space-x-2">
          <span className="font-semibold text-amber-400">Lưu ý:</span>
          <span>{VI.auth.storageWarning}</span>
        </div>
        <Button
          size="sm"
          variant="ghost"
          onClick={() => setDismissed(true)}
          className="text-xs h-6 px-2 text-amber-300 hover:text-white"
        >
          {VI.common.close}
        </Button>
      </div>
    </aside>
  );
};
