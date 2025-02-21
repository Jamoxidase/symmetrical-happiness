import React, { useEffect, useRef, useState } from 'react';
import { X } from 'lucide-react';

const JmolViewer = ({ data, isOpen, onClose }) => {
  const viewerRef = useRef(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!isOpen || !data) return;
    
    const loadJSmol = async () => {
      try {
        setIsLoading(true);

        // Load jQuery first
        if (!window.jQuery) {
          const jquery = document.createElement('script');
          jquery.src = "https://cdnjs.cloudflare.com/ajax/libs/jquery/3.7.1/jquery.min.js";
          await new Promise((resolve, reject) => {
            jquery.onload = resolve;
            jquery.onerror = reject;
            document.head.appendChild(jquery);
          });
        }

        // Then load JSmol
        if (!window.Jmol) {
          const jsmol = document.createElement('script');
          jsmol.src = "https://chemapps.stolaf.edu/jmol/jsmol/JSmol.min.js";
          await new Promise((resolve, reject) => {
            jsmol.onload = resolve;
            jsmol.onerror = reject;
            document.head.appendChild(jsmol);
          });
        }

        // Wait a bit for JSmol to initialize
        await new Promise(resolve => setTimeout(resolve, 100));

        if (!window.Jmol?.getApplet) {
          throw new Error('JSmol not properly initialized');
        }

        const Info = {
          width: "100%",
          height: "100%",
          use: "HTML5",
          j2sPath: "https://chemapps.stolaf.edu/jmol/jsmol/j2s",
          serverURL: "https://chemapps.stolaf.edu/jmol/jsmol/php/jsmol.php",
          disableJ2SLoadMonitor: true,
          disableInitialConsole: true,
          debug: false,
          readyFunction: () => setIsLoading(false)
        };

        if (viewerRef.current) {
          viewerRef.current.innerHTML = '';
          const applet = window.Jmol.getApplet("jsmolApplet", Info);
          viewerRef.current.innerHTML = window.Jmol.getAppletHtml(applet);

          // Load structure after a short delay
          setTimeout(() => {
            window.Jmol.script(applet, `
              set pdbAddHydrogens FALSE;
              load data "pdb"\n${data}\nend "pdb";
              set cartoonRockets OFF;
              set cartoonLadders OFF;
              set cartoonRibose ON;
              set nucleicStrand 1;
              cartoons only;
              color cartoons [x007020];
              center all;
              rotate best;
              zoom 70;
            `);
          }, 500);
        }
      } catch (err) {
        console.error('JSmol initialization error:', err);
        setError('Failed to initialize viewer');
        setIsLoading(false);
      }
    };

    loadJSmol();

    return () => {
      if (viewerRef.current) {
        viewerRef.current.innerHTML = '';
      }
    };
  }, [isOpen, data]);

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 z-50"
      style={{ backgroundColor: 'rgba(0, 0, 0, 0.5)' }}
    >
      <div className="fixed inset-0 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-xl w-[800px] h-[600px] flex flex-col">
          <div className="flex justify-between items-center px-4 py-2 border-b">
            <h3 className="font-semibold">RNA Structure Viewer</h3>
            <button 
              onClick={onClose} 
              className="p-1.5 hover:bg-gray-100 rounded-md"
            >
              <X size={18} />
            </button>
          </div>
          
          <div className="flex-1 relative bg-gray-50 p-4">
            {isLoading && (
              <div className="absolute inset-0 flex items-center justify-center bg-white">
                <div className="text-sm text-gray-500">Loading viewer...</div>
              </div>
            )}
            {error && (
              <div className="absolute inset-0 flex items-center justify-center bg-white">
                <div className="text-sm text-red-500">{error}</div>
              </div>
            )}
            <div
              ref={viewerRef}
              className="w-full h-full border rounded-lg bg-white"
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default JmolViewer;