import { useState, useMemo } from 'react';
import { ChevronDown, ChevronRight, Copy, X, ExternalLink, Box, Search } from 'lucide-react';
import JmolViewer from '../JmolViewer';

const BASE_URL = 'https://gtrnadb.ucsc.edu/genomes/eukaryota/Hsapi19/dummyDir/';

const TableRow = ({ label, value }) => (
  <div className="grid grid-cols-[200px,1fr] border-b border-[var(--border-color)] last:border-b-0">
    <div className="text-sm font-medium text-[var(--text-primary)] p-3 border-r border-[var(--border-color)]">
      {label}
    </div>
    <div className="text-sm text-[var(--text-secondary)] p-3">
      {value}
    </div>
  </div>
);

const ArtifactsPanel = ({ tableData = {}, isOpen, onClose }) => {
  const [expandedItems, setExpandedItems] = useState({});
  const [expandedSubfields, setExpandedSubfields] = useState({});
  const [copyStatus, setCopyStatus] = useState({});
  const [jmolData, setJmolData] = useState(null);
  const [showJmolViewer, setShowJmolViewer] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Process sequence data for display
  const processedData = useMemo(() => {
    if (!tableData?.sequences) return {};
    const sequences = { ...tableData.sequences };
    return {
      sequences: Object.fromEntries(
        Object.entries(sequences).sort(([a], [b]) => a.localeCompare(b))
      )
    };
  }, [tableData.sequences]);

  // Filter data based on search query
  const filteredData = useMemo(() => {
    if (!searchQuery.trim()) return processedData;

    const query = searchQuery.toLowerCase();
    const filtered = {};

    Object.entries(processedData).forEach(([tableName, entries]) => {
      const filteredEntries = {};
      
      Object.entries(entries).forEach(([key, entry]) => {
        if (
          entry.gene_symbol?.toLowerCase().includes(query) ||
          entry.overview?.Organism?.toLowerCase().includes(query)
        ) {
          filteredEntries[key] = entry;
        }
      });

      if (Object.keys(filteredEntries).length > 0) {
        filtered[tableName] = filteredEntries;
      }
    });

    return filtered;
  }, [processedData, searchQuery]);

  const toggleItem = (id) => {
    setExpandedItems(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  const toggleSubfield = (itemId, subfieldKey) => {
    const key = `${itemId}-${subfieldKey}`;
    setExpandedSubfields(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const handleOpenJmol = (blocksData) => {
    setJmolData(blocksData);
    setShowJmolViewer(true);
  };

  const copyToClipboard = async (text, id, section) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopyStatus({ id, section });
      setTimeout(() => setCopyStatus({}), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const getImageUrl = (imagePath, overview) => {
    if (overview?.Organism === 'Homo sapiens') {
      return `${BASE_URL}${imagePath}`;
    }
    return imagePath;
  };

  const renderDataField = (itemId, key, value, overview = null) => {
    if (key === 'gene_symbol') return null;
    
    const subfieldKey = `${itemId}-${key}`;
    
    if (typeof value === 'object' && value !== null) {
      return (
        <div key={key} className="mb-2">
          <button
            onClick={() => toggleSubfield(itemId, key)}
            className="flex items-center gap-2 w-full text-left px-3 py-2 
                     hover:bg-[var(--bg-hover)] rounded-[var(--radius-sm)]
                     transition-colors duration-200"
          >
            {expandedSubfields[subfieldKey] ? 
              <ChevronDown size={14} className="text-[var(--text-secondary)]" /> : 
              <ChevronRight size={14} className="text-[var(--text-secondary)]" />
            }
            <span className="text-sm font-medium text-[var(--text-primary)]">{key}</span>
          </button>
          {expandedSubfields[subfieldKey] && (
            <div className="ml-6 mt-2 border border-[var(--border-color)] rounded-[var(--radius-md)] overflow-hidden">
              {Object.entries(value).map(([subKey, subValue]) => (
                <TableRow 
                  key={subKey}
                  label={subKey}
                  value={
                    key === 'Images' ? (
                      <img
                        src={getImageUrl(subValue, overview)}
                        alt={subKey}
                        className="rounded-[var(--radius-sm)] border border-[var(--border-color)]"
                        style={{ maxWidth: '100%' }}
                      />
                    ) : subValue
                  }
                />
              ))}
            </div>
          )}
        </div>
      );
    }
  
    return <TableRow key={key} label={key} value={value} />;
  };

  const DataSection = ({ title, data, id, section, overview = null }) => {
    if (!data) return null;
    const isCopied = copyStatus.id === id && copyStatus.section === section;

    const fields = Object.entries(data)
      .map(([key, value]) => renderDataField(id, key, value, overview))
      .filter(field => field !== null);

    if (fields.length === 0) return null;

    return (
      <div className="mb-4">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-[var(--text-primary)]">{title}</span>
          <button
            onClick={() => copyToClipboard(JSON.stringify(data, null, 2), id, section)}
            className="p-1.5 hover:bg-[var(--bg-hover)] rounded-[var(--radius-sm)] 
                     transition-colors flex items-center gap-1 text-xs text-[var(--text-secondary)]"
          >
            <Copy size={14} />
            {isCopied ? 'Copied!' : 'Copy'}
          </button>
        </div>
        
        <div className="bg-[var(--bg-input)] rounded-[var(--radius-md)] overflow-hidden 
                      border border-[var(--border-color)]">
          {fields}
        </div>
      </div>
    );
  };

  if (!isOpen) return null;

  return (
    <div className="h-full bg-[var(--bg-surface)] flex flex-col">
      {/* Header */}
      <div className="flex justify-between items-center px-4 py-3 border-b border-[var(--border-color)]">
        <h2 className="text-lg font-medium text-[var(--text-primary)]">Data Explorer</h2>
        <button
          onClick={onClose}
          className="p-1.5 hover:bg-[var(--bg-hover)] rounded-[var(--radius-sm)]
                   text-[var(--text-secondary)] hover:text-[var(--text-primary)]
                   transition-colors"
          aria-label="Close panel"
        >
          <ChevronRight size={20} />
        </button>
      </div>

      {/* Search */}
      <div className="px-4 py-3 border-b border-[var(--border-color)]">
        <div className="relative">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by gene symbol..."
            className="w-full pl-9 pr-4 py-2 bg-[var(--bg-input)] border border-[var(--border-color)] 
                     rounded-[var(--radius-md)] text-sm text-[var(--text-primary)] 
                     placeholder-[var(--text-tertiary)] focus:outline-none focus:ring-2 
                     focus:ring-[var(--accent-color)]/50 focus:border-transparent
                     transition-colors duration-200"
          />
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-[var(--text-tertiary)]" />
        </div>
      </div>

      {/* Content */}
      <div className="overflow-y-auto flex-1 px-4 py-3">
        {Object.entries(filteredData).map(([tableName, entries]) => (
          <div key={tableName} className="mb-6">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-md font-semibold text-[var(--text-primary)] capitalize">
                {tableName}
              </h3>
              <span className="text-sm text-[var(--text-secondary)]">
                {Object.keys(entries).length} entries
              </span>
            </div>

            {Object.entries(entries).map(([key, data]) => (
              <div key={key} className="mb-3 rounded-[var(--radius-md)] border border-[var(--border-color)] 
                                    bg-[var(--bg-input)] overflow-hidden">
                <div className="flex items-center justify-between p-3 hover:bg-[var(--bg-hover)] 
                              transition-colors duration-200">
                  <button
                    onClick={() => toggleItem(key)}
                    className="flex items-center gap-2 text-left flex-1"
                  >
                    {expandedItems[key] ? 
                      <ChevronDown size={18} className="text-[var(--text-secondary)]" /> : 
                      <ChevronRight size={18} className="text-[var(--text-secondary)]" />
                    }
                    <span className="font-medium text-[var(--text-primary)]">
                      {data.gene_symbol}
                    </span>
                    {data.overview?.Organism && (
                      <span className="text-sm text-[var(--text-secondary)]">
                        ({data.overview.Organism})
                      </span>
                    )}
                  </button>
                  {data.tool_data?.blocks_file && (
                    <button
                      onClick={() => handleOpenJmol(data.tool_data.blocks_file)}
                      className="p-1.5 hover:bg-[var(--bg-hover)] rounded-[var(--radius-sm)] 
                               transition-colors duration-200"
                      title="View 3D Structure"
                    >
                      <Box size={18} className="text-[var(--accent-color)]" />
                    </button>
                  )}
                </div>
                
                {expandedItems[key] && (
                  <div className="p-3 border-t border-[var(--border-color)]">
                    <DataSection 
                      title="Core Data" 
                      data={data}
                      id={key}
                      section="core"
                      overview={data.overview}
                    />
                    
                    {data.tool_data?.trnascan_se_ss && (
                      <DataSection 
                        title="tRNAscan-SE Structure" 
                        data={data.trnascan_se_ss} 
                        id={key}
                        section="trnascan"
                      />
                    )}
                    
                    {data.tool_data?.sprinzl_pos && (
                      <DataSection 
                        title="Sprinzl Positions" 
                        data={data.sprinzl_pos} 
                        id={key}
                        section="sprinzl"
                        overview={data.overview}
                      />
                    )}

                    {data.rnacentral_link && (
                      <div className="mt-4 pt-3 border-t border-[var(--border-color)]">
                        <a
                          href={data.rnacentral_link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1.5 text-sm text-[var(--accent-color)] 
                                   hover:text-[var(--accent-color)]/80 transition-colors duration-200"
                        >
                          <ExternalLink size={16} />
                          View on RNA Central
                        </a>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        ))}
      </div>

      {showJmolViewer && jmolData && (
        <JmolViewer data={jmolData} onClose={() => setShowJmolViewer(false)} />
      )}
    </div>
  );
};

export default ArtifactsPanel;