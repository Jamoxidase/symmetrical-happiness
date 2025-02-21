import { useState } from 'react';
import { ChevronDown, ChevronRight, ExternalLink, Copy, Check, ImageIcon, FileText } from 'lucide-react';

const BASE_URL = 'https://gtrnadb.ucsc.edu/genomes/eukaryota/Hsapi19/dummyDir/';

const CopyButton = ({ text, className }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    if (!text) return;
    
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  return (
    <button
      onClick={handleCopy}
      className={`inline-flex items-center gap-1.5 px-2 py-1 text-gray-400 hover:text-gray-300 
                 hover:bg-gray-700 rounded-md transition-colors text-sm ${className}`}
      title="Copy to clipboard"
    >
      {copied ? (
        <>
          <Check size={14} />
          <span>Copied!</span>
        </>
      ) : (
        <>
          <Copy size={14} />
          <span>Copy</span>
        </>
      )}
    </button>
  );
};

const ImageLink = ({ path, entry }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  const getImageUrl = () => {
    if (!path) return '';
    if (entry?.overview?.Organism === 'Homo sapiens') {
      return `${BASE_URL}${path}`;
    }
    return path;
  };

  return (
    <span className="inline-block">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="inline-flex items-center gap-1.5 px-2 py-1 text-blue-400 hover:text-blue-300 
                   bg-gray-800 hover:bg-gray-700 rounded-md transition-colors text-sm"
      >
        <ImageIcon size={14} className="text-gray-400" />
        <span>View Image</span>
        {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
      </button>
      {isExpanded && path && (
        <div className="mt-2 rounded-lg overflow-hidden border border-gray-700 bg-white p-2">
          <img
            src={getImageUrl()}
            alt="tRNA structure"
            className="max-w-full rounded-md"
          />
        </div>
      )}
    </span>
  );
};

const DataLink = ({ tag, tableData }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  const matches = tag.match(/<([^>]+)>/);
  if (!matches) return tag;
  
  const parts = matches[1].split('/');
  const identifier = parts[0];
  const pathParts = parts.slice(1);

  if (!identifier || !tableData?.sequences) {
    return tag;
  }

  // Find the entry by matching the gene_symbol field (case-insensitive)
  const entry = Object.values(tableData.sequences || {}).find(
    seq => seq.gene_symbol.toLowerCase() === identifier.toLowerCase()
  );
  
  if (!entry) {
    return tag;
  }
  
  // Navigate through the path parts to get the value
  let value = entry;
  for (const part of pathParts) {
    value = value?.[part];
    if (value === undefined || value === null) {
      console.log('Failed to find field:', part, 'in:', entry);
      return tag;
    }
  }

  const isImage = pathParts.includes('images') ||
    (typeof value === 'string' && 
     (value.endsWith('.png') || value.endsWith('.jpg') || value.endsWith('.svg')));

  const isUrl = typeof value === 'string' && 
    (value.startsWith('http://') || value.startsWith('https://'));

  const isSprinzl = pathParts.includes('sprinzl_pos');
  // Consider it a simple field if it's a direct property (not nested)
  const isSimpleField = pathParts.length === 1;

  if (isImage) {
    return <ImageLink path={value} entry={entry} />;
  }

  if (isUrl) {
    return (
      <a
        href={value}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-1.5 px-2 py-1 text-blue-400 hover:text-blue-300 
                   bg-gray-800 hover:bg-gray-700 rounded-md transition-colors text-sm"
      >
        <ExternalLink size={14} />
        <span>{String(value || '')}</span>
      </a>
    );
  }

  const safeValue = value?.toString() || '';
  
  if (isSimpleField) {
    return (
      <span className="inline-flex items-center gap-1.5 px-2 py-1 text-blue-400 bg-gray-800/50 rounded-md transition-colors text-sm">
        <span>{safeValue}</span>
        <CopyButton text={safeValue} />
      </span>
    );
  }

  const buttonText = isSprinzl ? 'Sprinzl alignment' : (
    isSimpleField ? safeValue : 
    `${safeValue.slice(0, 20)}${safeValue.length > 20 ? '...' : ''}`
  );

  return (
    <span className="inline-block">
      <div className="flex items-center gap-2">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="inline-flex items-center gap-1.5 px-2 py-1 text-blue-400 hover:text-blue-300 
                     bg-gray-800 hover:bg-gray-700 rounded-md transition-colors text-sm"
        >
          {isSprinzl ? <FileText size={14} className="text-gray-400" /> : null}
          <span>{buttonText || 'Empty content'}</span>
          {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        </button>
        {!isImage && !isUrl && value && (
          <CopyButton text={safeValue} />
        )}
      </div>
      {isExpanded && (
        <div className="mt-2 rounded-lg border border-gray-700 bg-gray-800/50 p-3">
          <pre className="whitespace-pre font-mono text-sm text-gray-300 overflow-x-auto leading-tight">
            {typeof value === 'object' ? 
              JSON.stringify(value, null, 2) : 
              safeValue
            }
          </pre>
        </div>
      )}
    </span>
  );
};

function parseMessageContent(content, tableData, isStreaming = false) {
  if (!content) return null;
  
  try {
    // Split content into parts, preserving data tags
    const parts = content.split(/(<[^>]+>)/).filter(Boolean);
    
    // Split text parts into words while preserving data tags
    const wordParts = parts.map((part, index) => {
      if (part.startsWith('<') && part.endsWith('>')) {
        // Return data tags as single items
        return [<DataLink key={`${index}-0`} tag={part} tableData={tableData} />];
      } else {
        // Split text into lines first
        return part.split(/(\n)/).map((line, lineIndex) => {
          if (line === '\n') {
            return <br key={`${index}-line-${lineIndex}`} />;
          }
          // Then split each line into words and preserve other whitespace
          return line.split(/(\s+)/).filter(Boolean).map((word, wordIndex) => {
            const isWhitespace = /^\s+$/.test(word);
            if (isWhitespace) {
              return word;
            }
            return (
              <span
                key={`${index}-${lineIndex}-${wordIndex}`}
                className="inline-block"
              >
                {word}
              </span>
            );
          });
        });
      }
    });

    // Flatten the array of arrays
    return wordParts.flat();
  } catch (error) {
    console.error('Error parsing message content:', error);
    return content;
  }
};

export { DataLink as default, parseMessageContent };