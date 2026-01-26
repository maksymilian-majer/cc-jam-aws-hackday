import { Calendar, Zap } from 'lucide-react';
import { useTheme } from './context/ThemeContext';
import Chat from './components/Chat';
import PluginPanel from './components/PluginPanel';
import ThemeToggle from './components/ThemeToggle';

function App() {
  const { theme } = useTheme();

  return (
    <div className="min-h-screen relative">
      {/* Theme background */}
      <div className="theme-bg" />

      {/* Grain texture overlay */}
      <div className="grain-overlay" />

      {/* Main content */}
      <div className="relative z-10 min-h-screen p-4 sm:p-6 lg:p-8">
        {/* Header */}
        <header className="max-w-7xl mx-auto mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`w-12 h-12 flex items-center justify-center ${
                theme === 'brutalist'
                  ? 'bg-black border-4 border-black'
                  : 'rounded-2xl bg-white/10 backdrop-blur-sm border border-white/20'
              }`}>
                {theme === 'brutalist' ? (
                  <Zap className="w-6 h-6 text-yellow-400" />
                ) : (
                  <Calendar className="w-6 h-6 text-violet-400" />
                )}
              </div>
              <div>
                <h1 className={`text-2xl tracking-tight flex items-center gap-2 ${
                  theme === 'brutalist'
                    ? 'font-display text-4xl text-black uppercase tracking-wider'
                    : 'font-bold text-white'
                }`}>
                  Schedule Hacker
                </h1>
                <p className={`text-sm ${
                  theme === 'brutalist'
                    ? 'text-black/70 uppercase tracking-wide font-mono'
                    : 'text-white/50'
                }`}>
                  {theme === 'brutalist' ? 'FIND EVENTS. GET BUSY.' : 'AI-powered event discovery'}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <ThemeToggle />
              {/* Mobile plugin toggle */}
              <button className={`lg:hidden px-4 py-2 text-sm ${
                theme === 'brutalist'
                  ? 'theme-button-secondary'
                  : 'theme-button-secondary rounded-xl'
              }`}>
                Plugins
              </button>
            </div>
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
