import { useContext } from 'react';
import { ToastContext, ToastContextValue } from './ToastContext';

export const useToast = (): ToastContextValue => {
  const context = useContext(ToastContext);
  if (!context) {
    return {
      showToast: () => '',
      removeToast: () => {},
      toast: {
        success: () => '',
        error: () => '',
        warning: () => '',
        info: () => '',
      },
    };
  }
  return context;
};

