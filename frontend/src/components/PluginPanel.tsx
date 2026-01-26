import { useState, useEffect } from 'react';
import { Plug, Plus, RefreshCw, ExternalLink, X } from 'lucide-react';

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

      // Check if the response indicates success
      if (data.response.toLowerCase().includes('error') ||
          data.response.toLowerCase().includes('failed')) {
        setGenerationError(data.response);
      } else {
        setGenerationSuccess(data.response);
        // Refresh plugin list after successful generation
        await fetchPlugins();
        // Close modal after a delay to show success message
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
    <div className="flex flex-col h-full bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 bg-emerald-600 text-white flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Plug className="w-5 h-5" />
          <h2 className="text-lg font-semibold">Plugins</h2>
        </div>
        <button
          onClick={fetchPlugins}
          disabled={isLoading}
          className="p-1.5 hover:bg-emerald-700 rounded transition-colors disabled:opacity-50"
          title="Refresh plugins"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Plugin list */}
      <div className="flex-1 overflow-y-auto p-4">
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="w-6 h-6 text-gray-400 animate-spin" />
          </div>
        ) : plugins.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <Plug className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No plugins loaded</p>
          </div>
        ) : (
          <div className="space-y-3">
            {plugins.map((plugin) => (
              <div
                key={plugin.name}
                className="border border-gray-200 rounded-lg p-3 hover:border-emerald-300 transition-colors"
              >
                <div className="flex items-start justify-between gap-2">
                  <h3 className="font-medium text-gray-900">{plugin.name}</h3>
                </div>
                <a
                  href={plugin.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-emerald-600 hover:text-emerald-800 flex items-center gap-1 mt-1"
                >
                  <ExternalLink className="w-3 h-3" />
                  {plugin.source_url}
                </a>
                {plugin.description && (
                  <p className="text-sm text-gray-500 mt-2 line-clamp-2">
                    {plugin.description}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Generate Plugin button */}
      <div className="p-4 border-t border-gray-200">
        <button
          onClick={() => setShowModal(true)}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 transition-colors"
        >
          <Plus className="w-5 h-5" />
          Generate Plugin
        </button>
      </div>

      {/* Modal for plugin URL input */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
            {/* Modal header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Generate New Plugin</h3>
              <button
                onClick={closeModal}
                disabled={isGenerating}
                className="p-1 hover:bg-gray-100 rounded transition-colors disabled:opacity-50"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            {/* Modal content */}
            <div className="p-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Website URL
              </label>
              <input
                type="url"
                value={pluginUrl}
                onChange={(e) => setPluginUrl(e.target.value)}
                placeholder="https://example.com/events"
                disabled={isGenerating}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
              />
              <p className="mt-2 text-xs text-gray-500">
                Enter the URL of a website with events. The AI will analyze the page and generate a scraper plugin.
              </p>

              {/* Loading state */}
              {isGenerating && (
                <div className="mt-4 flex items-center gap-2 text-emerald-600">
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span className="text-sm">Generating plugin... This may take a moment.</span>
                </div>
              )}

              {/* Error message */}
              {generationError && (
                <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-sm text-red-700">{generationError}</p>
                </div>
              )}

              {/* Success message */}
              {generationSuccess && (
                <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
                  <p className="text-sm text-green-700">{generationSuccess}</p>
                </div>
              )}
            </div>

            {/* Modal footer */}
            <div className="flex justify-end gap-2 px-4 py-3 border-t border-gray-200 bg-gray-50">
              <button
                onClick={closeModal}
                disabled={isGenerating}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleGeneratePlugin}
                disabled={isGenerating || !pluginUrl.trim()}
                className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
              >
                {isGenerating ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Plus className="w-4 h-4" />
                    Generate
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
