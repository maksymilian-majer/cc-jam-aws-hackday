import Chat from './components/Chat';
import PluginPanel from './components/PluginPanel';

function App() {
  return (
    <div className="h-screen bg-gray-100 p-4 sm:p-6 lg:p-8">
      <div className="h-full max-w-6xl mx-auto flex gap-4">
        {/* Main chat area */}
        <div className="flex-1 min-w-0">
          <Chat />
        </div>
        {/* Plugin sidebar - hidden on mobile, shown on larger screens */}
        <div className="hidden lg:block w-80 flex-shrink-0">
          <PluginPanel />
        </div>
      </div>
    </div>
  );
}

export default App;
