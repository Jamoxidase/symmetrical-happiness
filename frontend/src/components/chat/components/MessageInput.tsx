import { Send } from 'lucide-react';

interface MessageInputProps {
  input: string;
  setInput: (value: string) => void;
  onSubmit: (message: string) => Promise<void>;
  isLoading: boolean;
  isAuthenticated: boolean;
  showArtifacts: boolean;
}

export function MessageInput({ 
  input, 
  setInput, 
  onSubmit, 
  isLoading, 
  isAuthenticated,
  showArtifacts 
}: MessageInputProps) {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
      onSubmit(input);
      setInput('');
    }
  };

  return (
    <div className="sticky bottom-0 z-50 border-t border-gray-700 bg-gray-800/95 
                  backdrop-blur supports-[backdrop-filter]:bg-gray-800/80">
      <form onSubmit={handleSubmit} className={`${!showArtifacts ? 'max-w-3xl mx-auto' : ''} 
                                               flex gap-3 p-4`}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="flex-1 bg-gray-900 border border-gray-600 px-4 py-2.5 rounded-md 
                   text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 
                   focus:ring-blue-500/50 focus:border-blue-500 transition-all duration-200"
          placeholder={!isAuthenticated ? "Please authenticate first..." : 
                     isLoading ? "Processing..." : "Type your message..."}
          disabled={isLoading || !isAuthenticated}
        />
        <button
          type="submit"
          disabled={!input.trim() || isLoading || !isAuthenticated}
          className="px-4 py-2.5 bg-blue-600 text-gray-100 rounded-md hover:bg-blue-500 
                   disabled:bg-gray-700 disabled:text-gray-500 disabled:cursor-not-allowed 
                   transition-all duration-200 flex items-center justify-center"
        >
          <Send className="h-5 w-5" />
        </button>
      </form>
    </div>
  );
}