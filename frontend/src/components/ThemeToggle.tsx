import { useTheme } from '../context/ThemeContext';
import { Sword, Sparkles } from 'lucide-react';

export default function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className="theme-button-secondary px-3 py-2 rounded-lg flex items-center gap-2 text-sm font-medium"
      title={`Switch to ${theme === 'brutalist' ? 'Glass' : 'Kill Bill'} theme`}
    >
      {theme === 'brutalist' ? (
        <>
          <Sparkles className="w-4 h-4" />
          <span className="hidden sm:inline">Glass</span>
        </>
      ) : (
        <>
          <Sword className="w-4 h-4" />
          <span className="hidden sm:inline">Kill Bill</span>
        </>
      )}
    </button>
  );
}
