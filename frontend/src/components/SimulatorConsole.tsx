import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Play, AlertOctagon, ShieldCheck, TrendingDown } from 'lucide-react';
import { analyticsAPI, competitorsAPI } from '@/lib/api';
import RiskHeatmap from './RiskHeatmap';

interface Competitor {
    id: number;
    name: string;
}

export default function SimulatorConsole() {
    const [scenario, setScenario] = useState('');
    const [competitor, setCompetitor] = useState('');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<any>(null);

    // Fetch real competitors from database
    const { data: competitors } = useQuery<Competitor[]>({
        queryKey: ['competitors-list'],
        queryFn: async () => {
            const response = await competitorsAPI.list();
            return response.data;
        },
    });

    const handleRunSimulation = async () => {
        if (!scenario || !competitor) return;

        setLoading(true);
        try {
            // Call real backend API
            const res = await analyticsAPI.runSimulation({
                competitor_name: competitor,
                scenario: scenario,
                context: ''
            });

            if (res.data?.prediction) {
                setResult(res.data.prediction);
            } else if (res.data?.error) {
                console.error('Simulation error:', res.data.error);
                setResult({
                    win_rate_prediction: "Unable to calculate",
                    market_reaction: "Simulation encountered an error. Please try again.",
                    new_objections: ["Error processing scenario"],
                    recommended_response: "Contact support if issue persists."
                });
            }
        } catch (e) {
            console.error(e);
            setResult({
                win_rate_prediction: "Error",
                market_reaction: "Could not connect to simulation engine.",
                new_objections: ["Network or server error"],
                recommended_response: "Check your connection and try again."
            });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-full">
            {/* Input Console */}
            <div className="card flex flex-col h-full bg-gray-900 border-gray-800 text-white">
                <div className="flex items-center gap-2 mb-6 border-b border-gray-700 pb-4">
                    <AlertOctagon className="text-red-500" />
                    <h2 className="text-xl font-bold font-mono">WAR ROOM // SIMULATOR</h2>
                </div>

                <div className="space-y-6 flex-1">
                    <div>
                        <label className="block text-xs font-mono text-gray-400 mb-2 uppercase">Target Competitor</label>
                        <select
                            className="w-full bg-gray-800 border border-gray-700 rounded p-3 text-white focus:ring-2 focus:ring-red-500 focus:outline-none"
                            value={competitor}
                            onChange={(e) => setCompetitor(e.target.value)}
                        >
                            <option value="">SELECT TARGET...</option>
                            {competitors?.map((c) => (
                                <option key={c.id} value={c.name}>{c.name}</option>
                            ))}
                        </select>
                    </div>

                    <div>
                        <label className="block text-xs font-mono text-gray-400 mb-2 uppercase">Scenario (What If?)</label>
                        <textarea
                            className="w-full bg-gray-800 border border-gray-700 rounded p-3 text-white h-32 focus:ring-2 focus:ring-red-500 focus:outline-none font-mono text-sm"
                            placeholder="E.g., Competitor drops pricing by 20% for Enterprise tier..."
                            value={scenario}
                            onChange={(e) => setScenario(e.target.value)}
                        />
                    </div>

                    <button
                        onClick={handleRunSimulation}
                        disabled={loading || !competitor || !scenario}
                        className={`w-full py-4 rounded font-bold font-mono uppercase tracking-widest flex items-center justify-center gap-2 transition-all
                    ${loading ? 'bg-gray-700 cursor-wait' : 'bg-red-600 hover:bg-red-700 shadow-lg shadow-red-900/50'}`}
                    >
                        {loading ? (
                            'Running Simulation...'
                        ) : (
                            <>
                                <Play size={18} /> Initiate Sequence
                            </>
                        )}
                    </button>
                </div>
            </div>

            {/* Output / Results */}
            <div className="card bg-white border-l-4 border-l-red-500 relative overflow-auto max-h-[80vh]">
                {!result ? (
                    <div className="h-full flex flex-col items-center justify-center text-gray-400 opacity-50">
                        <ShieldCheck size={64} className="mb-4" />
                        <p className="font-mono text-sm text-center">AWAITING SIMULATION DATA...</p>
                    </div>
                ) : (
                    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                        <div className="flex items-center justify-between mb-6">
                            <h3 className="text-lg font-bold text-gray-900 uppercase tracking-wide">Prediction Results</h3>
                            <span className="px-3 py-1 bg-red-100 text-red-800 text-xs font-bold rounded">AI POWERED</span>
                        </div>

                        <div className="grid grid-cols-2 gap-4 mb-6">
                            <div className="p-4 bg-gray-50 rounded-lg">
                                <label className="text-xs font-medium text-gray-500 uppercase">Win Rate Impact</label>
                                <div className="flex items-center gap-2 text-2xl font-bold text-red-600 mt-1">
                                    <TrendingDown /> {result.win_rate_prediction}
                                </div>
                            </div>
                            <div className="p-4 bg-gray-50 rounded-lg">
                                <label className="text-xs font-medium text-gray-500 uppercase">Risk Level</label>
                                <div className="text-2xl font-bold text-gray-900 mt-1">
                                    {result.win_rate_prediction?.includes('-') ? 'CRITICAL' : 'MODERATE'}
                                </div>
                            </div>
                        </div>

                        <div className="mb-6">
                            <label className="text-xs font-medium text-gray-500 uppercase block mb-2">Market Reaction & Objections</label>
                            <div className="p-4 bg-yellow-50 text-yellow-900 rounded-lg text-sm italic border border-yellow-200">
                                "{result.market_reaction}"
                            </div>
                            <ul className="mt-3 space-y-2">
                                {result.new_objections?.map((obj: string, i: number) => (
                                    <li key={i} className="flex items-center gap-2 text-sm text-gray-700">
                                        <span className="text-red-500 font-bold">!</span> {obj}
                                    </li>
                                ))}
                            </ul>
                        </div>

                        {/* Risk Heatmap */}
                        <div className="mb-6">
                            <RiskHeatmap
                                winRateImpact={result.win_rate_prediction}
                                marketReaction={result.market_reaction}
                                objectionsCount={result.new_objections?.length || 0}
                            />
                        </div>

                        <div>
                            <label className="text-xs font-medium text-gray-500 uppercase block mb-2">AI Recommended Counter-Strategy</label>
                            <div className="p-4 bg-green-50 text-green-900 rounded-lg border border-green-200">
                                <div className="flex items-start gap-3">
                                    <ShieldCheck className="mt-1 flex-shrink-0" size={20} />
                                    <p className="text-sm font-medium leading-relaxed">{result.recommended_response}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
