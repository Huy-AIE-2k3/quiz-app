import React, { createContext, useContext, useState, useId, useRef, KeyboardEvent } from 'react';

interface TabsContextValue {
  activeTab: string;
  setActiveTab: (val: string) => void;
  baseId: string;
}

const TabsContext = createContext<TabsContextValue | null>(null);

export interface TabsProps {
  readonly defaultValue: string;
  readonly value?: string;
  readonly onValueChange?: (val: string) => void;
  readonly className?: string;
  readonly children: React.ReactNode;
}

export const Tabs: React.FC<TabsProps> = ({
  defaultValue,
  value,
  onValueChange,
  className = '',
  children,
}) => {
  const [internalTab, setInternalTab] = useState(defaultValue);
  const baseId = useId();

  const activeTab = value !== undefined ? value : internalTab;

  const setActiveTab = (val: string) => {
    if (value === undefined) {
      setInternalTab(val);
    }
    onValueChange?.(val);
  };

  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab, baseId }}>
      <div className={`w-full flex flex-col gap-4 ${className}`}>{children}</div>
    </TabsContext.Provider>
  );
};

export interface TabListProps {
  readonly ariaLabel: string;
  readonly className?: string;
  readonly children: React.ReactNode;
}

export const TabList: React.FC<TabListProps> = ({ ariaLabel, className = '', children }) => {
  const listRef = useRef<HTMLDivElement>(null);

  const handleKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    if (!listRef.current) return;
    const triggers = Array.from(
      listRef.current.querySelectorAll<HTMLButtonElement>('[role="tab"]:not([disabled])')
    );
    const currentIndex = triggers.findIndex((el) => el === document.activeElement);

    if (currentIndex === -1) return;

    let targetIndex = currentIndex;
    if (e.key === 'ArrowRight') {
      targetIndex = (currentIndex + 1) % triggers.length;
    } else if (e.key === 'ArrowLeft') {
      targetIndex = (currentIndex - 1 + triggers.length) % triggers.length;
    } else if (e.key === 'Home') {
      targetIndex = 0;
    } else if (e.key === 'End') {
      targetIndex = triggers.length - 1;
    } else {
      return;
    }

    e.preventDefault();
    triggers[targetIndex].focus();
    triggers[targetIndex].click();
  };

  return (
    <div
      ref={listRef}
      role="tablist"
      aria-label={ariaLabel}
      onKeyDown={handleKeyDown}
      className={`inline-flex items-center gap-1 p-1 rounded-md bg-canvas border border-line-subtle text-text-muted ${className}`}
    >
      {children}
    </div>
  );
};

export interface TabTriggerProps {
  readonly value: string;
  readonly disabled?: boolean;
  readonly className?: string;
  readonly children: React.ReactNode;
}

export const TabTrigger: React.FC<TabTriggerProps> = ({
  value,
  disabled = false,
  className = '',
  children,
}) => {
  const ctx = useContext(TabsContext);
  if (!ctx) throw new Error('TabTrigger must be used inside Tabs');

  const { activeTab, setActiveTab, baseId } = ctx;
  const isSelected = activeTab === value;
  const tabId = `${baseId}-tab-${value}`;
  const panelId = `${baseId}-panel-${value}`;

  return (
    <button
      type="button"
      role="tab"
      id={tabId}
      aria-selected={isSelected}
      aria-controls={panelId}
      tabIndex={isSelected ? 0 : -1}
      disabled={disabled}
      onClick={() => setActiveTab(value)}
      className={`inline-flex items-center justify-center px-3.5 py-1.5 text-xs font-mono font-medium rounded transition-all select-none focus:outline-none focus:ring-1 focus:ring-brand ${
        isSelected
          ? 'bg-elevated text-brand font-semibold shadow-xs'
          : 'text-text-secondary hover:text-text-primary hover:bg-surface/50'
      } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'} ${className}`}
    >
      {children}
    </button>
  );
};

export interface TabContentProps {
  readonly value: string;
  readonly className?: string;
  readonly children: React.ReactNode;
}

export const TabContent: React.FC<TabContentProps> = ({ value, className = '', children }) => {
  const ctx = useContext(TabsContext);
  if (!ctx) throw new Error('TabContent must be used inside Tabs');

  const { activeTab, baseId } = ctx;
  if (activeTab !== value) return null;

  const tabId = `${baseId}-tab-${value}`;
  const panelId = `${baseId}-panel-${value}`;

  return (
    <div
      role="tabpanel"
      id={panelId}
      aria-labelledby={tabId}
      tabIndex={0}
      className={`focus:outline-none text-left ${className}`}
    >
      {children}
    </div>
  );
};

