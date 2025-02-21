// WelcomePopup.jsx

import React from 'react';
import { X } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

const WelcomePopup = ({ isOpen, onClose }) => {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader className="flex items-center justify-between">
          <DialogTitle>Welcome to tRNA Analysis Chat</DialogTitle>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-200 transition-colors"
          >
            <X size={24} />
          </button>
        </DialogHeader>

        <div className="space-y-4">
          <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-4">
            <span className="text-xs font-medium text-blue-400 bg-blue-500/20 px-2 py-1 rounded">
              BETA
            </span>
          </div>

          <p className="text-gray-300">
            Welcome to our interactive tRNA analysis assistant! This tool allows you to query and analyze data from the Genomic tRNA Database (GtRNAdb) through natural conversation.
          </p>

          <div className="space-y-2">
            <h3 className="font-medium text-gray-200">Current Features:</h3>
            <ul className="list-disc list-inside space-y-1 text-gray-300">
              <li>Natural language queries of GtRNAdb data</li>
              <li>Interactive data visualization</li>
              <li>Real-time analysis and insights</li>
            </ul>
          </div>

          <p className="text-sm text-gray-400">
            Additional analysis tools and features coming soon! Stay tuned for updates.
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default WelcomePopup;