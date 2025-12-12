import { useQuery } from '@tanstack/react-query';
import { Search, Plus, Filter, AlertCircle, ArrowRight } from 'lucide-react';
import { useState } from 'react';
import { motion } from 'framer-motion';

const API_URL = "http://localhost:8000/api";

interface Candidate {
    id: string;
    name: string;
    email: string;
    score_avg: number;
    risk: string;
    hands_on: number;
    interview_status: string;
}

export default function Dashboard({ onSelectCandidate }: { onSelectCandidate: (id: string) => void }) {
    const [search, setSearch] = useState("");

    const { data: candidates, isLoading } = useQuery<Candidate[]>({
        queryKey: ['candidates'],
        queryFn: async () => {
            const res = await fetch(`${API_URL}/candidates`);
            if (!res.ok) throw new Error("Failed");
            return res.json();
        }
    });

    const filtered = candidates?.filter(c => c.name.toLowerCase().includes(search.toLowerCase())) || [];

    // KPIs
    const avgScore = filtered.length > 0 ? (filtered.reduce((acc, c) => acc + c.score_avg, 0) / filtered.length).toFixed(0) : 0;

    return (
        <div className="space-y-8 animate-in fade-in duration-500">

            {/* Header */}
            <div className="flex items-center justify-between border-b border-white/5 pb-6">
                <div>
                    <h1 className="text-xl font-medium text-white mb-1">Overview</h1>
                    <p className="text-sm text-zinc-500">Global view of active candidates</p>
                </div>
                <div className="flex items-center gap-3">
                    <button className="h-8 px-3 rounded-md bg-white/5 border border-white/5 text-xs font-medium text-zinc-400 hover:text-white hover:bg-white/10 transition-colors flex items-center gap-2">
                        <Filter className="w-3.5 h-3.5" /> Filter
                    </button>
                    <button className="h-8 px-3 rounded-md bg-white text-black text-xs font-medium hover:opacity-90 transition-opacity flex items-center gap-2">
                        <Plus className="w-3.5 h-3.5" /> Upload CV
                    </button>
                </div>
            </div>

            {/* Bento Grid Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="glass-panel p-5 rounded-xl">
                    <div className="text-zinc-500 text-xs font-medium uppercase tracking-wider mb-2">Total Candidates</div>
                    <div className="text-2xl font-mono text-white">{filtered.length}</div>
                    <div className="mt-2 h-1 w-full bg-zinc-800 rounded-full overflow-hidden">
                        <div className="h-full bg-zinc-500 w-full" />
                    </div>
                </div>
                <div className="glass-panel p-5 rounded-xl">
                    <div className="text-zinc-500 text-xs font-medium uppercase tracking-wider mb-2">Avg. Score</div>
                    <div className="text-2xl font-mono text-white flex items-center gap-2">
                        {avgScore}%
                        <span className="text-xs text-zinc-600 font-sans px-1.5 py-0.5 bg-zinc-900 rounded border border-zinc-800">Target 70%</span>
                    </div>
                    <div className="mt-2 h-1 w-full bg-zinc-800 rounded-full overflow-hidden">
                        <div className="h-full bg-white w-[60%]" />
                    </div>
                </div>
                <div className="glass-panel p-5 rounded-xl">
                    <div className="text-zinc-500 text-xs font-medium uppercase tracking-wider mb-2">Attention Needed</div>
                    <div className="text-2xl font-mono text-white flex items-center gap-2">
                        {filtered.filter(c => c.risk === 'Alto').length}
                        <AlertCircle className="w-4 h-4 text-orange-500/80" />
                    </div>
                    <div className="mt-2 text-xs text-orange-400/80">High retention risk detected</div>
                </div>
            </div>

            {/* High Density Table */}
            <div className="space-y-3">
                <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-zinc-500" />
                    <input
                        type="text"
                        placeholder="Search candidates..."
                        className="w-full bg-transparent border-b border-white/10 py-2 pl-9 pr-4 text-sm focus:outline-none focus:border-white/20 transition-colors text-white placeholder:text-zinc-700"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                    />
                </div>

                <div className="w-full">
                    {/* Table Header */}
                    <div className="grid grid-cols-12 gap-4 px-4 py-2 text-xs font-medium text-zinc-600 uppercase tracking-wider">
                        <div className="col-span-4">Candidate</div>
                        <div className="col-span-2">Score</div>
                        <div className="col-span-2">Hands On</div>
                        <div className="col-span-2">Risk</div>
                        <div className="col-span-2 text-right">Action</div>
                    </div>

                    {/* Table Rows */}
                    <div className="space-y-1">
                        {isLoading ? (
                            <div className="text-center py-10 text-zinc-600 text-sm">Loading data...</div>
                        ) : (
                            filtered.map((c, i) => (
                                <CandidateRow key={c.id} candidate={c} onClick={() => onSelectCandidate(c.id)} index={i} />
                            ))
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

function CandidateRow({ candidate, onClick, index }: { candidate: Candidate, onClick: () => void, index: number }) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.02 }}
            onClick={onClick}
            className="grid grid-cols-12 gap-4 px-4 py-3 items-center rounded-lg interactive-item cursor-pointer group"
        >
            <div className="col-span-4 flex items-center gap-3">
                <div className="w-6 h-6 rounded-full bg-gradient-to-tr from-zinc-700 to-zinc-800 flex items-center justify-center text-[10px] text-zinc-300 font-bold border border-white/5">
                    {candidate.name.charAt(0)}
                </div>
                <div>
                    <div className="text-sm text-zinc-200 group-hover:text-white transition-colors">{candidate.name}</div>
                    <div className="text-[10px] text-zinc-600 truncate max-w-[150px]">{candidate.email}</div>
                </div>
            </div>

            <div className="col-span-2">
                <div className={`
               inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium border
               ${candidate.score_avg >= 80 ? 'bg-green-500/10 text-green-400 border-green-500/20' :
                        candidate.score_avg >= 60 ? 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20' :
                            'bg-red-500/10 text-red-400 border-red-500/20'}
            `}>
                    {candidate.score_avg} match
                </div>
            </div>

            <div className="col-span-2">
                <div className="flex items-center gap-1.5">
                    <div className="h-1 w-12 bg-zinc-800 rounded-full overflow-hidden">
                        <div className="h-full bg-zinc-400" style={{ width: `${candidate.hands_on}%` }} />
                    </div>
                    <span className="text-[10px] text-zinc-500 font-mono">{candidate.hands_on}%</span>
                </div>
            </div>

            <div className="col-span-2">
                <span className={`text-[10px] px-1.5 py-0.5 rounded ${candidate.risk === 'Alto' ? 'text-red-400' : 'text-zinc-500'}`}>
                    {candidate.risk === 'Alto' ? 'High Risk' : 'Low'}
                </span>
            </div>

            <div className="col-span-2 text-right opacity-0 group-hover:opacity-100 transition-opacity">
                <ArrowRight className="w-3.5 h-3.5 text-zinc-500 ml-auto" />
            </div>
        </motion.div>
    )
}
