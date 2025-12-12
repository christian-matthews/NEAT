import React, { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Dashboard from './pages/Dashboard';
import CandidateDetail from './pages/CandidateDetail';
import Settings from './pages/Settings';
import { LayoutGrid, Settings2, Code2, Users } from 'lucide-react';

const queryClient = new QueryClient();

function App() {
  const [view, setView] = useState<'dashboard' | 'detail' | 'settings'>('dashboard');
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(null);

  const navigateToDetail = (id: string) => {
    setSelectedCandidateId(id);
    setView('detail');
  };

  const navigateToDashboard = () => {
    setView('dashboard');
    setSelectedCandidateId(null);
  };

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-background text-foreground font-sans selection:bg-purple-500/30 flex overflow-hidden relative">

        {/* Global Noise Overlay */}
        <div className="absolute inset-0 bg-noise pointer-events-none z-50 opacity-40 mix-blend-overlay" />

        {/* Navigation Rail - Ultra Minimal */}
        <aside className="w-14 border-r border-white/5 bg-black/20 flex flex-col items-center py-6 z-40">
          <div className="mb-8">
            <div className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center border border-white/10">
              <div className="w-3 h-3 bg-white rounded-full" />
            </div>
          </div>

          <nav className="flex-1 flex flex-col gap-4 w-full items-center">
            <NavButton active={view === 'dashboard'} onClick={navigateToDashboard} icon={<LayoutGrid className="w-4 h-4" />} />
            <NavButton active={view === 'settings'} onClick={() => setView('settings')} icon={<Settings2 className="w-4 h-4" />} />
          </nav>
        </aside>

        {/* Main Workspace */}
        <main className="flex-1 relative overflow-auto bg-black/20">
          <div className="max-w-[1600px] mx-auto p-6 min-h-screen">
            {view === 'dashboard' && <Dashboard onSelectCandidate={navigateToDetail} />}
            {view === 'detail' && selectedCandidateId && (
              <CandidateDetail
                candidateId={selectedCandidateId}
                onBack={navigateToDashboard}
              />
            )}
            {view === 'settings' && <Settings />}
          </div>
        </main>
      </div>
    </QueryClientProvider>
  );
}

function NavButton({ active, onClick, icon }: { active: boolean, onClick: () => void, icon: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      className={`
           w-8 h-8 rounded-md flex items-center justify-center transition-all duration-200
           ${active ? 'bg-white/10 text-white' : 'text-zinc-500 hover:text-zinc-300'}
        `}
    >
      {icon}
    </button>
  )
}

export default App;
