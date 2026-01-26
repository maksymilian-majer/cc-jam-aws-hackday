import { useState, useEffect } from 'react';
import { Plug, Plus, RefreshCw, ExternalLink, X, Zap } from 'lucide-react';

interface Plugin {
  name: string;
  source_url: string;
  description: string;
}

export default function PluginPanel() {
  const [plugins, setPlugins] = useState<Plugin[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [pluginUrl, setPluginUrl] = useState('');
  const [generationError, setGenerationError] = useState<string | null>(null);
  const [generationSuccess, setGenerationSuccess] = useState<string | null>(null);

  const fetchPlugins = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/plugins');
      if (!response.ok) {
        throw new Error('Failed to fetch plugins');
      }
      const data = await response.json();
      setPlugins(data);
    } catch (error) {
      console.error('Error fetching plugins:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPlugins();
  }, []);

  const handleGeneratePlugin = async () => {
    const trimmedUrl = pluginUrl.trim();
    if (!trimmedUrl) return;

    setIsGenerating(true);
    setGenerationError(null);
    setGenerationSuccess(null);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: `Create a plugin for ${trimmedUrl}`,
          conversation_id: null,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate plugin');
      }

      const data = await response.json();

      if (data.response.toLowerCase().includes('error') ||
          data.response.toLowerCase().includes('failed')) {
        setGenerationError(data.response);
      } else {
        setGenerationSuccess(data.response);
        await fetchPlugins();
        setTimeout(() => {
          setShowModal(false);
          setPluginUrl('');
          setGenerationSuccess(null);
        }, 2000);
      }
    } catch (error) {
      setGenerationError('Failed to generate plugin. Please try again.');
    } finally {
      setIsGenerating(false);
    }
  };

  const closeModal = () => {
    if (!isGenerating) {
      setShowModal(false);
      setPluginUrl('');
      setGenerationError(null);
      setGenerationSuccess(null);
    }
  };

  return (
    <>
      <div className="flex flex-col h-full glass-card glass-card-glow rounded-3xl overflow-hidden">
        {/* Header */}
        <div className="px-5 py-4 border-b border-white/10 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center">
              <Plug className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-white">Plugins</h2>
              <p className="text-xs text-white/50">{plugins.length} active</p>
            </div>
          </div>
          <button
            onClick={fetchPlugins}
            disabled={isLoading}
            className="p-2 rounded-lg hover:bg-white/10 transition-colors disabled:opacity-50"
            title="Refresh plugins"
          >
            <RefreshCw className={`w-4 h-4 text-white/70 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {/* Plugin list */}
        <div className="flex-1 overflow-y-auto p-4">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <RefreshCw className="w-6 h-6 text-white/30 animate-spin" />
            </div>
          ) : plugins.length === 0 ? (
            <div className="text-center py-12">
              <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-white/5 flex items-center justify-center">
                <Plug className="w-8 h-8 text-white/30" />
              </div>
              <p className="text-sm text-white/50">No plugins loaded</p>
              <p className="text-xs text-white/30 mt-1">Generate one below</p>
            </div>
          ) : (
            <div className="space-y-3">
              {plugins.map((plugin) => (
                <div
                  key={plugin.name}
                  className="event-card-glass rounded-xl p-4 cursor-pointer"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500/20 to-cyan-500/20 flex items-center justify-center flex-shrink-0">
                        <Zap className="w-4 h-4 text-violet-400" />
                      </div>
                      <h3 className="font-medium text-white">{plugin.name}</h3>
                    </div>
                  </div>
                  <a
                    href={plugin.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1 mt-2 ml-10"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <ExternalLink className="w-3 h-3" />
                    <span className="truncate">{plugin.source_url}</span>
                  </a>
                  {plugin.description && (
                    <p className="text-sm text-white/50 mt-2 ml-10 line-clamp-2">
                      {plugin.description}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Generate Plugin button */}
        <div className="p-4 border-t border-white/10">
          <button
            onClick={() => setShowModal(true)}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl glass-button"
          >
            <Plus className="w-5 h-5" />
            Generate Plugin
          </button>
        </div>
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 modal-backdrop flex items-center justify-center z-50 p-4">
          <div className="glass-card rounded-2xl max-w-md w-full overflow-hidden">
            {/* Modal header */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-white/10">
              <h3 className="text-lg font-semibold text-white">Generate New Plugin</h3>
              <button
                onClick={closeModal}
                disabled={isGenerating}
                className="p-1.5 rounded-lg hover:bg-white/10 transition-colors disabled:opacity-50"
              >
                <X className="w-5 h-5 text-white/70" />
              </button>
            </div>

            {/* Modal content */}
            <div className="p-5">
              <label className="block text-sm font-medium text-white/70 mb-2">
                Website URL
              </label>
              <input
                type="url"
                value={pluginUrl}
                onChange={(e) => setPluginUrl(e.target.value)}
                placeholder="https://example.com/events"
                disabled={isGenerating}
                className="w-full px-4 py-3 rounded-xl glass-input disabled:opacity-50"
              />
              <p className="mt-3 text-xs text-white/40">
                Enter a URL with events. AI will analyze and generate a scraper.
              </p>

              {/* Loading state */}
              {isGenerating && (
                <div className="mt-4 flex items-center gap-3 text-cyan-400">
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span className="text-sm">Generating plugin...</span>
                </div>
              )}

              {/* Error message */}
              {generationError && (
                <div className="mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded-xl">
                  <p className="text-sm text-red-400">{generationError}</p>
                </div>
              )}

              {/* Success message */}
              {generationSuccess && (
                <div className="mt-4 p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl">
                  <p className="text-sm text-emerald-400">{generationSuccess}</p>
                </div>
              )}
            </div>

            {/* Modal footer */}
            <div className="flex justify-end gap-3 px-5 py-4 border-t border-white/10">
              <button
                onClick={closeModal}
                disabled={isGenerating}
                className="px-4 py-2 rounded-xl glass-button-secondary disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleGeneratePlugin}
                disabled={isGenerating || !pluginUrl.trim()}
                className="px-5 py-2 rounded-xl glass-button disabled:opacity-50 flex items-center gap-2"
              >
                {isGenerating ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Zap className="w-4 h-4" />
                    Generate
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
