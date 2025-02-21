import { 
  PanelLeft, 
  PanelRight, 
  Wifi, 
  WifiOff, 
  AlertTriangle,
  Loader2,
  Database
} from 'lucide-react';
import { AuthComponent } from '../AuthComponent';
import { AuthTabs } from '../AuthTabs';
import { Chat, ConnectionState } from '../types';
import { cn } from '@/lib/utils';
import { 
  Tooltip, 
  TooltipTrigger, 
  TooltipContent, 
  TooltipProvider 
} from '@/components/ui/tooltip';

interface ChatHeaderProps {
  isAuthenticated: boolean;
  showSidebar: boolean;
  setShowSidebar: (value: boolean) => void;
  activeChat: Chat | null;
  showArtifacts: boolean;
  setShowArtifacts: (value: boolean) => void;
  connectionState: ConnectionState;
  isLoading: boolean;
}

export function ChatHeader({
  isAuthenticated,
  showSidebar,
  setShowSidebar,
  activeChat,
  showArtifacts,
  setShowArtifacts,
  connectionState,
  isLoading
}: ChatHeaderProps) {
  const getConnectionInfo = () => {
    if (!isAuthenticated) return null;

    switch (connectionState) {
      case 'connecting':
        return {
          icon: <Loader2 className="h-4 w-4 animate-spin text-gold" />,
          text: 'Connecting...',
          bgColor: 'bg-gold/10',
          textColor: 'text-gold',
          tooltip: 'Establishing connection to server'
        };
      case 'connected':
        return {
          icon: <Wifi className="h-4 w-4 text-coral" />,
          text: isLoading ? 'Receiving response...' : 'Connected',
          bgColor: 'bg-coral/10',
          textColor: 'text-coral',
          tooltip: 'Connected to server'
        };
      case 'disconnected':
        return {
          icon: <WifiOff className="h-4 w-4 text-gray-light" />,
          text: 'Disconnected',
          bgColor: 'bg-white/5',
          textColor: 'text-gray-light',
          tooltip: 'Connection lost. Trying to reconnect...'
        };
      case 'error':
        return {
          icon: <AlertTriangle className="h-4 w-4 text-coral" />,
          text: 'Connection Error',
          bgColor: 'bg-coral/10',
          textColor: 'text-coral',
          tooltip: 'Failed to connect. Please check your connection.'
        };
      default:
        return null;
    }
  };

  const renderConnectionStatus = () => {
    const info = getConnectionInfo();
    if (!info) return null;

    return (
      <Tooltip content={info.tooltip}>
        <div 
          className={cn(
            "flex items-center gap-2 px-3 py-1.5 rounded-lg border",
            "transition-all duration-200",
            info.bgColor,
            info.textColor,
            info.textColor === 'text-coral' ? 'border-coral/20' : 
            info.textColor === 'text-gold' ? 'border-gold/20' : 
            'border-white/10'
          )}
          role="status"
          aria-live="polite"
        >
          {info.icon}
          <span className="text-sm font-medium">
            {info.text}
          </span>
          {isLoading && (
            <div className="w-1.5 h-1.5 rounded-full animate-pulse bg-current" />
          )}
        </div>
      </Tooltip>
    );
  };

  return (
    <TooltipProvider>
      <header 
        className="sticky top-0 z-40 border-b border-white/10 bg-navy/95 backdrop-blur supports-[backdrop-filter]:bg-navy/80"
        role="banner"
      >
      <div className={cn(
        "flex justify-between items-center px-4 py-3",
        !showArtifacts && "max-w-5xl mx-auto"
      )}>
        <div className="flex items-center gap-4">
          {isAuthenticated && (
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                onClick={() => setShowSidebar(!showSidebar)}
                className={cn(
                  "p-2 rounded-lg transition-all duration-200",
                  "hover:bg-white/5 focus:outline-none focus:ring-2 focus:ring-coral/50",
                  "lg:hidden"
                )}
                aria-label={showSidebar ? "Hide chat menu" : "Show chat menu"}
                aria-expanded={showSidebar}
              >
                <PanelLeft size={20} className="text-coral" />
              </button>
              </TooltipTrigger>
              <TooltipContent>
                {showSidebar ? "Hide chat menu" : "Show chat menu"}
              </TooltipContent>
            </Tooltip>
          )}
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold text-soft-white">
              {activeChat?.title || 'tRNA Analysis Chat'}
            </h1>
            {activeChat?.id && (
              <Tooltip content="Active chat ID">
                <span className="px-2 py-0.5 text-xs font-mono bg-white/5 text-gray-light rounded-lg border border-white/10">
                  {activeChat.id.slice(0, 8)}
                </span>
              </Tooltip>
            )}
          </div>
        </div>

        <div className="flex items-center gap-4">
          {renderConnectionStatus()}
          <AuthComponent />
          
          {isAuthenticated && (
            <div className="flex items-center gap-2">
              <Tooltip content={showArtifacts ? "Hide data explorer" : "Show data explorer"}>
                <button
                  onClick={() => setShowArtifacts(!showArtifacts)}
                  className={cn(
                    "flex items-center gap-2 px-4 py-2 text-base font-medium rounded-xl",
                    "transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-coral/50",
                    showArtifacts
                      ? "bg-coral/20 text-coral hover:bg-coral/30 border border-coral/20"
                      : "bg-white/5 text-soft-white border border-white/10 hover:bg-white/10"
                  )}
                  aria-label={showArtifacts ? "Hide data explorer" : "Show data explorer"}
                  aria-expanded={showArtifacts}
                >
                  <Database size={18} className={cn(
                    "transition-colors",
                    showArtifacts ? "text-coral" : "text-gray-light group-hover:text-soft-white"
                  )} />
                  <span>{showArtifacts ? "Hide Explorer" : "Show Explorer"}</span>
                </button>
              </Tooltip>
            </div>
          )}
        </div>
      </div>
    </header>
    </TooltipProvider>
  );
}