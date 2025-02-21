import { useState, useRef, MouseEvent } from 'react';

interface UseArtifactsPanelReturn {
  showArtifacts: boolean;
  setShowArtifacts: (value: boolean) => void;
  artifactsPanelWidth: string;
  dragRef: React.RefObject<HTMLDivElement>;
  handleDragStart: (e: MouseEvent) => void;
}

export function useArtifactsPanel(): UseArtifactsPanelReturn {
  const [showArtifacts, setShowArtifacts] = useState(false);
  const [artifactsPanelWidth, setArtifactsPanelWidth] = useState('35%');
  const dragRef = useRef<HTMLDivElement>(null);

  const handleDragStart = (e: MouseEvent) => {
    const handleDrag = (e: globalThis.MouseEvent) => {
      const width = ((window.innerWidth - e.clientX) / window.innerWidth) * 100;
      if (width > 20 && width < 60) {
        setArtifactsPanelWidth(`${width}%`);
      }
    };

    const handleDragEnd = () => {
      document.removeEventListener('mousemove', handleDrag);
      document.removeEventListener('mouseup', handleDragEnd);
    };

    document.addEventListener('mousemove', handleDrag);
    document.addEventListener('mouseup', handleDragEnd);
  };

  return {
    showArtifacts,
    setShowArtifacts,
    artifactsPanelWidth,
    dragRef,
    handleDragStart
  };
}