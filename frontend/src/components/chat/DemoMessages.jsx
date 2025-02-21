import React from 'react';

const DEMO_MESSAGES = [
  {
    label: "Show tRNA Sequences",
    message: "Show me some high-scoring tRNA with known modifications in humans."
  },
  {
    label: "Compare Structures",
    message: "Can you compare the secondary structures of tRNA-SeC-TCA-1-1 and tRNA-SeC-TCA-2-1?"
  },
  {
    label: "Analyze Features",
    message: "What are the unique structural features of human iMet tRNAs?"
  },
  {
    label: "Find External Resources",
    message: "Lets take a look at patterns in the genomic context of isoleucine tRNAs in humans."
  }
];

export function DemoMessages({ onSelectDemo, disabled }) {
  return (
    <div className="grid grid-cols-2 gap-4">
      {DEMO_MESSAGES.map((demo, index) => (
        <button
          key={index}
          onClick={() => onSelectDemo(demo.message)}
          className="text-left bg-[#1E1E1E]/80 backdrop-blur-sm border border-[#333333]/80 
                    rounded-xl hover:bg-[#252525]/80 transition-all duration-200 
                    group overflow-hidden p-6"
          disabled={disabled}
        >
          <div className="space-y-3">
            <span className="block text-[#FF6F61] text-lg font-['Times New Roman'] group-hover:text-[#FF8F81]">
              {demo.label}
            </span>
            <p className="text-[#999999] text-base font-['Times New Roman'] leading-relaxed 
                       group-hover:text-white transition-colors">
              {demo.message}
            </p>
          </div>
        </button>
      ))}
    </div>
  );
}