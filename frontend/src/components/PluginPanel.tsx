import { useState, useEffect } from 'react';
import { Plug, Plus, RefreshCw, ExternalLink, X, Zap } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

interface Plugin {
  name: string;
  source_url: string;
  description: string;
}

export default function PluginPanel() {
  const { theme } = useTheme();
  const [plugins, setPlugins] = useState<Plugin[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [pluginUrl, setPluginUrl] = useState('');
  const [generationError, setGenerationError] = useState<string | null>(null);
  const [generationSuccess, setGenerationSuccess] = useState<string | null>(null);

  const isBrutalist = theme === 'brutalist';

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
      <div className={`flex flex-col h-full overflow-hidden ${
        isBrutalist
          ? 'theme-card'
          : 'theme-card theme-card-glow rounded-3xl'
      }`}>
        {/* Header */}
        <div className={`px-5 py-4 flex items-center justify-between ${
          isBrutalist
            ? 'border-b-4 border-black bg-black'
            : 'border-b border-white/10'
        }`}>
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 flex items-center justify-center ${
              isBrutalist
                ? 'bg-yellow-400'
                : 'rounded-xl bg-gradient-to-br from-emerald-500 to-cyan-500'
            }`}>
              <Plug className={`w-5 h-5 ${isBrutalist ? 'text-black' : 'text-white'}`} />
            </div>
            <div>
              <h2 className={`text-lg font-semibold ${
                isBrutalist
                  ? 'text-yellow-400 uppercase tracking-wider font-display text-xl'
                  : 'text-white'
              }`}>Plugins</h2>
              <p className={`text-xs ${
                isBrutalist
                  ? 'text-yellow-400/70 uppercase tracking-wide'
                  : 'text-white/50'
              }`}>{plugins.length} active</p>
            </div>
          </div>
          <button
            onClick={fetchPlugins}
            disabled={isLoading}
            className={`p-2 transition-colors disabled:opacity-50 ${
              isBrutalist
                ? 'hover:bg-yellow-400 text-yellow-400 hover:text-black'
                : 'rounded-lg hover:bg-white/10'
            }`}
            title="Refresh plugins"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''} ${
              isBrutalist ? '' : 'text-white/70'
            }`} />
          </button>
        </div>

        {/* Plugin list */}
        <div className={`flex-1 overflow-y-auto p-4 ${
          isBrutalist ? 'bg-white' : ''
        }`}>
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <RefreshCw className={`w-6 h-6 animate-spin ${
                isBrutalist ? 'text-black/30' : 'text-white/30'
              }`} />
            </div>
          ) : plugins.length === 0 ? (
            <div className="text-center py-12">
              <div className={`w-16 h-16 mx-auto mb-4 flex items-center justify-center ${
                isBrutalist
                  ? 'bg-black border-4 border-black'
                  : 'rounded-2xl bg-white/5'
              }`}>
                <Plug className={`w-8 h-8 ${
                  isBrutalist ? 'text-yellow-400' : 'text-white/30'
                }`} />
              </div>
              <p className={`text-sm ${
                isBrutalist
                  ? 'text-black uppercase tracking-wide font-bold'
                  : 'text-white/50'
              }`}>
                {isBrutalist ? 'NO PLUGINS LOADED' : 'No plugins loaded'}
              </p>
              <p className={`text-xs mt-1 ${
                isBrutalist
                  ? 'text-black/60 uppercase tracking-wide'
                  : 'text-white/30'
              }`}>
                {isBrutalist ? 'GENERATE ONE BELOW' : 'Generate one below'}
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {plugins.map((plugin) => (
                <div
                  key={plugin.name}
                  className={`p-4 cursor-pointer ${
                    isBrutalist
                      ? 'theme-event-card'
                      : 'theme-event-card rounded-xl'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <div className={`w-8 h-8 flex items-center justify-center flex-shrink-0 ${
                        isBrutalist
                          ? 'bg-black'
                          : 'rounded-lg bg-gradient-to-br from-violet-500/20 to-cyan-500/20'
                      }`}>
                        <Zap className={`w-4 h-4 ${
                          isBrutalist ? 'text-yellow-400' : 'text-violet-400'
                        }`} />
                      </div>
                      <h3 className={`font-medium ${
                        isBrutalist
                          ? 'text-black uppercase tracking-wide'
                          : 'text-white'
                      }`}>{plugin.name}</h3>
                    </div>
                  </div>
                  <a
                    href={plugin.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={`text-xs flex items-center gap-1 mt-2 ml-10 ${
                      isBrutalist
                        ? 'text-red-600 hover:text-red-700 underline'
                        : 'text-cyan-400 hover:text-cyan-300'
                    }`}
                    onClick={(e) => e.stopPropagation()}
                  >
                    <ExternalLink className="w-3 h-3" />
                    <span className="truncate">{plugin.source_url}</span>
                  </a>
                  {plugin.description && (
                    <p className={`text-sm mt-2 ml-10 line-clamp-2 ${
                      isBrutalist ? 'text-black/60' : 'text-white/50'
                    }`}>
                      {plugin.description}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Generate Plugin button */}
        <div className={`p-4 ${
          isBrutalist
            ? 'border-t-4 border-black bg-yellow-400'
            : 'border-t border-white/10'
        }`}>
          <button
            onClick={() => setShowModal(true)}
            className={`w-full flex items-center justify-center gap-2 px-4 py-3 theme-button ${
              isBrutalist ? '' : 'rounded-xl'
            }`}
          >
            <Plus className="w-5 h-5" />
            {isBrutalist ? 'GENERATE PLUGIN' : 'Generate Plugin'}
          </button>
        </div>
      </div>

      {/* Modal */}
      {showModal && (
        <div className={`fixed inset-0 flex items-center justify-center z-50 p-4 ${
          isBrutalist
            ? 'theme-modal-backdrop'
            : 'theme-modal-backdrop'
        }`}>
          <div className={`max-w-md w-full overflow-hidden ${
            isBrutalist
              ? 'theme-modal'
              : 'theme-modal rounded-2xl'
          }`}>
            {/* Modal header */}
            <div className={`flex items-center justify-between px-5 py-4 ${
              isBrutalist
                ? 'border-b-4 border-black bg-black'
                : 'border-b border-white/10'
            }`}>
              <h3 className={`text-lg font-semibold ${
                isBrutalist
                  ? 'text-yellow-400 uppercase tracking-wider font-display'
                  : 'text-white'
              }`}>
                {isBrutalist ? 'GENERATE NEW PLUGIN' : 'Generate New Plugin'}
              </h3>
              <button
                onClick={closeModal}
                disabled={isGenerating}
                className={`p-1.5 transition-colors disabled:opacity-50 ${
                  isBrutalist
                    ? 'hover:bg-yellow-400 text-yellow-400 hover:text-black'
                    : 'rounded-lg hover:bg-white/10'
                }`}
              >
                <X className={`w-5 h-5 ${isBrutalist ? '' : 'text-white/70'}`} />
              </button>
            </div>

            {/* Modal content */}
            <div className={`p-5 ${isBrutalist ? 'bg-yellow-400' : ''}`}>
              <label className={`block text-sm font-medium mb-2 ${
                isBrutalist
                  ? 'text-black uppercase tracking-wide'
                  : 'text-white/70'
              }`}>
                {isBrutalist ? 'WEBSITE URL' : 'Website URL'}
              </label>
              <input
                type="url"
                value={pluginUrl}
                onChange={(e) => setPluginUrl(e.target.value)}
                placeholder={isBrutalist ? 'HTTPS://EXAMPLE.COM/EVENTS' : 'https://example.com/events'}
                disabled={isGenerating}
                className={`w-full px-4 py-3 theme-input disabled:opacity-50 ${
                  isBrutalist ? '' : 'rounded-xl'
                }`}
              />
              <p className={`mt-3 text-xs ${
                isBrutalist
                  ? 'text-black/60 uppercase tracking-wide'
                  : 'text-white/40'
              }`}>
                {isBrutalist
                  ? 'ENTER A URL WITH EVENTS. AI WILL ANALYZE AND GENERATE A SCRAPER.'
                  : 'Enter a URL with events. AI will analyze and generate a scraper.'}
              </p>

              {/* Loading state */}
              {isGenerating && (
                <div className={`mt-4 flex items-center gap-3 ${
                  isBrutalist ? 'text-black' : 'text-cyan-400'
                }`}>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span className={`text-sm ${isBrutalist ? 'uppercase tracking-wide' : ''}`}>
                    {isBrutalist ? 'GENERATING PLUGIN...' : 'Generating plugin...'}
                  </span>
                </div>
              )}

              {/* Error message */}
              {generationError && (
                <div className={`mt-4 p-3 ${
                  isBrutalist
                    ? 'bg-white border-3 border-black'
                    : 'bg-red-500/10 border border-red-500/20 rounded-xl'
                }`} style={isBrutalist ? { borderWidth: '3px' } : {}}>
                  <p className={`text-sm ${
                    isBrutalist ? 'text-red-600 uppercase' : 'text-red-400'
                  }`}>{generationError}</p>
                </div>
              )}

              {/* Success message */}
              {generationSuccess && (
                <div className={`mt-4 p-3 ${
                  isBrutalist
                    ? 'bg-white border-3 border-black'
                    : 'bg-emerald-500/10 border border-emerald-500/20 rounded-xl'
                }`} style={isBrutalist ? { borderWidth: '3px' } : {}}>
                  <p className={`text-sm ${
                    isBrutalist ? 'text-black uppercase' : 'text-emerald-400'
                  }`}>{generationSuccess}</p>
                </div>
              )}
            </div>

            {/* Modal footer */}
            <div className={`flex justify-end gap-3 px-5 py-4 ${
              isBrutalist
                ? 'border-t-4 border-black bg-yellow-400'
                : 'border-t border-white/10'
            }`}>
              <button
                onClick={closeModal}
                disabled={isGenerating}
                className={`px-4 py-2 theme-button-secondary disabled:opacity-50 ${
                  isBrutalist ? '' : 'rounded-xl'
                }`}
              >
                {isBrutalist ? 'CANCEL' : 'Cancel'}
              </button>
              <button
                onClick={handleGeneratePlugin}
                disabled={isGenerating || !pluginUrl.trim()}
                className={`px-5 py-2 theme-button disabled:opacity-50 flex items-center gap-2 ${
                  isBrutalist ? '' : 'rounded-xl'
                }`}
              >
                {isGenerating ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    {isBrutalist ? 'GENERATING...' : 'Generating...'}
                  </>
                ) : (
                  <>
                    <Zap className="w-4 h-4" />
                    {isBrutalist ? 'GENERATE' : 'Generate'}
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
