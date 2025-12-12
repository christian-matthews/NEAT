import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ChevronLeft, Sparkles, MessageSquare } from 'lucide-react';
import { useState } from 'react';

const API_URL = "http://localhost:8000/api";

export default function CandidateDetail({ candidateId, onBack }: { candidateId: string, onBack: () => void }) {
    const queryClient = useQueryClient();
    const [commentText, setCommentText] = useState("");
    const [interviewerName, setInterviewerName] = useState("");
    const [interviewNotes, setInterviewNotes] = useState("");

    const { data, isLoading, isError, error } = useQuery({
        queryKey: ['candidate', candidateId],
        queryFn: async () => {
            const res = await fetch(`${API_URL}/candidates/${candidateId}`);
            if (!res.ok) throw new Error("Failed to fetch candidate");
            return res.json();
        }
    });

    const addComment = useMutation({
        mutationFn: async (text: string) => {
            await fetch(`${API_URL}/candidates/${candidateId}/comment`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ author: 'User', text, timestamp: new Date().toISOString() })
            });
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['candidate', candidateId] });
            setCommentText("");
        }
    });

    const updateInterview = useMutation({
        mutationFn: async ({ notes, interviewer }: { notes: string, interviewer: string }) => {
            await fetch(`${API_URL}/candidates/${candidateId}/interview`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ score: 0, notes: `${interviewer}: ${notes}` })
            });
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['candidate', candidateId] });
            setInterviewerName("");
            setInterviewNotes("");
        }
    });

    if (isLoading) return <div className="flex items-center justify-center p-20 text-xs text-zinc-600 font-mono">LOADING_ASSETS...</div>;

    if (isError) return (
        <div className="flex flex-col items-center justify-center p-20 gap-4">
            <div className="text-xs text-red-400 font-mono">ERROR: {error?.message || 'Failed to load candidate'}</div>
            <button onClick={onBack} className="text-xs text-zinc-500 hover:text-white">← Back to List</button>
        </div>
    );

    if (!data || !data.metadata || !data.analysis) return (
        <div className="flex flex-col items-center justify-center p-20 gap-4">
            <div className="text-xs text-zinc-600 font-mono">NO_DATA_AVAILABLE</div>
            <button onClick={onBack} className="text-xs text-zinc-500 hover:text-white">← Back to List</button>
        </div>
    );

    const { metadata, analysis, comments = [], pdf_url } = data;
    // Add parameters to hide PDF sidebar thumbnails and optimize viewing
    const pdfUrlFull = `http://localhost:8000${pdf_url}#view=FitH&toolbar=0`;

    // Calculate score safely
    const scores = Object.values(analysis.fits || {}).map((f: any) => f.score || 0);
    const avgScore = scores.length > 0 ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : 0;

    return (
        <div className="h-[calc(100vh-6rem)] flex flex-col gap-4 animate-in fade-in duration-300">

            {/* TOP BAR: Compact Header */}
            <div className="flex items-center justify-between gap-4 glass-panel p-4 rounded-lg border border-white/5">
                <button onClick={onBack} className="text-zinc-500 hover:text-white flex items-center gap-2 text-sm font-medium transition-colors">
                    <ChevronLeft className="w-4 h-4" /> Back
                </button>

                <div className="flex items-center gap-4 flex-1">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-sm font-bold text-white shadow-lg shadow-indigo-500/20">
                        {metadata.name.charAt(0)}
                    </div>
                    <div className="flex-1">
                        <h2 className="text-base font-semibold text-white">{metadata.name}</h2>
                        <p className="text-xs text-zinc-500">{metadata.email}</p>
                    </div>
                    <div className="flex items-center gap-6">
                        <div className="text-right">
                            <div className="text-xs text-zinc-500">Profile Type</div>
                            <div className="text-sm font-medium text-zinc-200">{analysis.inference.profile_type}</div>
                        </div>
                        <div className="text-right">
                            <div className="text-xs text-zinc-500">Global Score</div>
                            <div className={`text-lg font-bold font-mono ${avgScore >= 80 ? 'text-green-400' : 'text-zinc-200'}`}>
                                {avgScore}/100
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* MAIN CONTENT: 2-Column Layout */}
            <div className="flex-1 flex gap-4 overflow-hidden">

                {/* LEFT: PDF Viewer (65% width) */}
                <div className="flex-[65] glass-panel rounded-lg border border-white/5 overflow-hidden flex flex-col relative group">
                    <div className="p-3 border-b border-white/5 flex items-center justify-between bg-zinc-900/50">
                        <span className="text-xs font-medium text-zinc-400">Curriculum Vitae</span>
                        <a
                            href={pdfUrlFull}
                            target="_blank"
                            rel="noreferrer"
                            className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium rounded transition-colors"
                        >
                            Open in New Tab
                        </a>
                    </div>
                    <iframe src={pdfUrlFull} className="flex-1 w-full h-full bg-zinc-100" title="CV" />
                </div>

                {/* RIGHT: Sidebar (35% width) */}
                <div className="flex-[35] flex flex-col gap-4 overflow-y-auto pr-1">

                    {/* Analysis Scores */}
                    <div className="space-y-3">
                        <h3 className="text-xs font-medium text-zinc-500 uppercase tracking-widest px-1">Analysis Report</h3>
                        <ScoreCard title="Admin & Finance" data={analysis.fits.admin} />
                        <ScoreCard title="Ops & Treasury" data={analysis.fits.ops} />
                        <ScoreCard title="Growth & Biz" data={analysis.fits.biz} />
                    </div>

                    {/* AI Reasoning */}
                    <div className="glass-panel p-4 rounded-lg border border-white/5">
                        <div className="flex items-center gap-2 mb-3 text-indigo-400">
                            <Sparkles className="w-3.5 h-3.5" />
                            <span className="text-xs font-bold uppercase">AI Reasoning</span>
                        </div>
                        <p className="text-xs text-zinc-400 leading-relaxed">
                            {analysis.inference.risk_warning}
                        </p>
                    </div>

                    {/* Interview Section */}
                    <div className="glass-panel rounded-lg border border-white/5 overflow-hidden">
                        <div className="p-3 border-b border-white/5 flex items-center gap-2">
                            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                            <span className="text-sm font-semibold text-zinc-300">Interview</span>
                        </div>
                        <div className="p-4 space-y-3">
                            {data.interview ? (
                                <div className="space-y-3">
                                    <div className="bg-zinc-900/30 rounded-lg p-3 border border-white/5">
                                        <div className="text-sm text-zinc-300 leading-relaxed whitespace-pre-wrap">
                                            {data.interview.notes}
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <div className="space-y-3">
                                    <div>
                                        <label className="text-xs text-zinc-500 mb-1.5 block">Interviewer Name</label>
                                        <input
                                            type="text"
                                            placeholder="Who conducted the interview?"
                                            value={interviewerName}
                                            onChange={(e) => setInterviewerName(e.target.value)}
                                            className="w-full bg-zinc-900/50 border border-white/5 rounded px-3 py-2.5 text-sm text-zinc-200 focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/20 transition-all placeholder:text-zinc-700"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-xs text-zinc-500 mb-1.5 block">Interview Notes</label>
                                        <textarea
                                            placeholder="Write your interview observations here..."
                                            value={interviewNotes}
                                            onChange={(e) => setInterviewNotes(e.target.value)}
                                            className="w-full bg-zinc-900/50 border border-white/5 rounded px-3 py-2.5 text-sm text-zinc-200 focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/20 transition-all placeholder:text-zinc-700 resize-none"
                                            rows={6}
                                        />
                                    </div>
                                    <button
                                        onClick={() => {
                                            if (interviewerName.trim() && interviewNotes.trim()) {
                                                updateInterview.mutate({ notes: interviewNotes, interviewer: interviewerName });
                                            }
                                        }}
                                        disabled={!interviewerName.trim() || !interviewNotes.trim()}
                                        className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:bg-zinc-800 disabled:text-zinc-600 disabled:cursor-not-allowed text-white text-sm font-semibold py-2.5 rounded transition-all"
                                    >
                                        Send Interview Notes
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Comments/Discussion */}
                    <div className="glass-panel rounded-lg border border-white/5 flex flex-col overflow-hidden min-h-[400px]">
                        <div className="p-3 border-b border-white/5 flex items-center gap-2">
                            <MessageSquare className="w-3.5 h-3.5 text-zinc-500" />
                            <span className="text-sm font-semibold text-zinc-300">Notes & Comments</span>
                        </div>
                        <div className="flex-1 overflow-y-auto p-4 space-y-4">
                            {comments.length === 0 ? (
                                <p className="text-xs text-zinc-600 italic">No comments yet. Add your first note below.</p>
                            ) : (
                                comments.map((c: any, i: number) => (
                                    <div key={i} className="text-sm">
                                        <div className="flex items-center gap-2 mb-1.5">
                                            <span className="font-semibold text-zinc-300">User</span>
                                            <span className="text-xs text-zinc-600">{new Date(c.timestamp).toLocaleString()}</span>
                                        </div>
                                        <p className="text-zinc-400 leading-relaxed">{c.text}</p>
                                    </div>
                                ))
                            )}
                        </div>
                        <div className="p-3 border-t border-white/5 bg-zinc-950/50 sticky bottom-0">
                            <textarea
                                className="w-full bg-zinc-900/50 border border-white/5 rounded px-3 py-2.5 text-sm text-zinc-200 focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/20 transition-all placeholder:text-zinc-700 resize-none"
                                placeholder="Add a note or comment..."
                                value={commentText}
                                onChange={(e) => setCommentText(e.target.value)}
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter' && !e.shiftKey && commentText.trim()) {
                                        e.preventDefault();
                                        addComment.mutate(commentText);
                                    }
                                }}
                                rows={4}
                            />
                            <button
                                onClick={() => commentText.trim() && addComment.mutate(commentText)}
                                disabled={!commentText.trim()}
                                className="mt-2 w-full bg-zinc-800 hover:bg-zinc-700 disabled:bg-zinc-900 disabled:text-zinc-700 disabled:cursor-not-allowed text-zinc-200 text-sm font-medium py-2 rounded transition-all"
                            >
                                Add Comment
                            </button>
                        </div>
                    </div>

                </div>
            </div>
        </div>
    );
}

function ScoreCard({ title, data }: { title: string, data: any }) {
    return (
        <div className="glass-panel p-4 rounded-lg border border-white/5 interactive-item">
            <div className="flex justify-between items-end mb-2">
                <span className="text-xs font-medium text-zinc-300">{title}</span>
                <span className="text-[10px] font-mono text-zinc-500">{data.score}%</span>
            </div>
            <div className="h-0.5 w-full bg-zinc-800 rounded-full overflow-hidden mb-3">
                <div
                    className={`h-full rounded-full ${data.score > 80 ? 'bg-indigo-500' : 'bg-zinc-500'}`}
                    style={{ width: `${data.score}%` }}
                />
            </div>

            <div className="space-y-1">
                {data.found.slice(0, 3).map((kw: string) => (
                    <div key={kw} className="flex items-center gap-1.5 text-[10px] text-zinc-500">
                        <div className="w-1 h-1 rounded-full bg-indigo-500/50" />
                        {kw}
                    </div>
                ))}
                {data.missing.length > 0 && (
                    <div className="flex items-center gap-1.5 text-[10px] text-zinc-600 italic mt-2">
                        <div className="w-1 h-1 rounded-full bg-red-500/20" />
                        Missing: {data.missing[0]}
                    </div>
                )}
            </div>
        </div>
    )
}
