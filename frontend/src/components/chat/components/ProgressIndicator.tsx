import { useEffect, useState } from 'react';
import { cn } from '@/lib/utils';

interface ProgressStep {
  type: string;
  content: string;
  status?: 'start' | 'update' | 'end';
  file?: string;
  timestamp: string;
}

interface ProgressIndicatorProps {
  steps: ProgressStep[];
}

export function ProgressIndicator({ steps }: ProgressIndicatorProps) {
  const [imageData, setImageData] = useState<string | null>(null);

  useEffect(() => {
    // Find the latest image data from tool_progress_genome updates
    const latestImage = steps
      .filter(step => step.type === 'tool_progress_genome' && step.status === 'update' && step.file === 'image')
      .pop();

    if (latestImage?.content) {
      setImageData(latestImage.content);
    }
  }, [steps]);

  return (
    <div className="progress-indicator w-full px-6 py-3">
      <div className="flex flex-col gap-2">
        {steps.map((step, index) => {
          const isExecutePlan = step.type === 'execute_plan';
          const isToolProgress = step.type.startsWith('tool_progress_');
          const toolName = isToolProgress ? step.type.replace('tool_progress_', '') : '';
          
          if (!isExecutePlan && !isToolProgress) return null;

          return (
            <div 
              key={`${step.type}-${index}`}
              className={cn(
                "flex items-start gap-2 text-sm",
                isExecutePlan ? "text-[var(--text-secondary)]" : "text-[var(--text-primary)]"
              )}
            >
              {/* Step indicator */}
              <div className="mt-1.5">
                <div className={cn(
                  "w-2 h-2 rounded-full",
                  isExecutePlan ? "bg-[var(--text-secondary)]" : "bg-[var(--accent-color)]"
                )} />
              </div>

              {/* Step content */}
              <div className="flex-1">
                {isToolProgress && (
                  <div className="text-xs text-[var(--text-tertiary)] uppercase tracking-wide mb-1">
                    {toolName}
                  </div>
                )}
                <div className="font-['Times New Roman'] text-[16px] leading-[1.4]">
                  {step.content}
                </div>

                {/* Display image if present */}
                {step.type === 'tool_progress_genome' && 
                 step.status === 'update' && 
                 step.file === 'image' && 
                 imageData && (
                  <div className="mt-2 rounded-lg overflow-hidden border border-[var(--border-color)]">
                    <img 
                      src={`data:image/png;base64,${imageData}`}
                      alt="Genome visualization"
                      className="max-w-full h-auto"
                    />
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}