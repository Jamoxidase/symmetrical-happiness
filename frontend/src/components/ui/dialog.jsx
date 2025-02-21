// src/components/ui/dialog.jsx

import React from 'react';
import * as DialogPrimitive from '@radix-ui/react-dialog';
import clsx from 'clsx';

// Dialog Root Component
export const Dialog = DialogPrimitive.Root;

// Dialog Trigger Component
export const DialogTrigger = DialogPrimitive.Trigger;

// Dialog Content Component
export const DialogContent = React.forwardRef(
  ({ className, children, ...props }, ref) => (
    <DialogPrimitive.Portal>
      <DialogPrimitive.Overlay className="fixed inset-0 bg-black bg-opacity-70 z-40" />
      <DialogPrimitive.Content
        ref={ref}
        className={clsx(
          'fixed z-50 w-full max-w-lg p-6 rounded-lg shadow-lg',
          'bg-gray-900 border border-gray-700 text-gray-100',
          'top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2',
          className
        )}
        {...props}
      >
        {children}
      </DialogPrimitive.Content>
    </DialogPrimitive.Portal>
  )
);
DialogContent.displayName = 'DialogContent';

// Dialog Header Component
export const DialogHeader = ({ className, ...props }) => (
  <div className={clsx('mb-4', className)} {...props} />
);
DialogHeader.displayName = 'DialogHeader';

// Dialog Title Component
export const DialogTitle = React.forwardRef(({ className, ...props }, ref) => (
  <DialogPrimitive.Title
    ref={ref}
    className={clsx('text-2xl font-semibold', className)}
    {...props}
  />
));
DialogTitle.displayName = 'DialogTitle';