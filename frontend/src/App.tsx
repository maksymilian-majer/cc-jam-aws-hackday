import { Calendar, Sparkles } from 'lucide-react';
import Chat from './components/Chat';
import PluginPanel from './components/PluginPanel';

function App() {
  return (
    <div className="min-h-screen relative">
      {/* Animated aurora background */}
      <div className="aurora-bg" />

      {/* Grain texture overlay */}
      <div className="grain-overlay" />

      {/* Main content */}
      <div className="relative z-10 min-h-screen p-4 sm:p-6 lg:p-8">
        {/* Header */}
        <header className="max-w-7xl mx-auto mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-2xl glass-card flex items-center justify-center">
                <Calendar className="w-6 h-6 text-violet-400" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
                  Schedule Hacker
                  <Sparkles className="w-5 h-5 text-cyan-400" />
                </h1>
                <p className="text-sm text-white/50">
                  AI-powered event discovery
                </p>
              </div>
            </div>

            {/* Mobile plugin toggle - could add state management here */}
            <button className="lg:hidden glass-button-secondary px-4 py-2 rounded-xl text-sm">
              Plugins
            </button>
          </div>
        </header>

        {/* Main layout */}
        <div className="max-w-7xl mx-auto h-[calc(100vh-140px)] flex gap-6">
          {/* Main chat area */}
          <div className="flex-1 min-w-0">
            <Chat />
          </div>

          {/* Plugin sidebar - hidden on mobile */}
          <div className="hidden lg:block w-80 flex-shrink-0">
            <PluginPanel />
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
