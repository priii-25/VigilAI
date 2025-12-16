import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Play, Zap, Shield, TrendingDown, Sparkles, AlertTriangle } from 'lucide-react';
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
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Input Console */}
            <div className="card bg-gradient-to-br from-primary-50/50 to-accent-50/50 border border-primary-100/50">
                <div className="flex items-center gap-3 mb-6 pb-4 border-b border-primary-100">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center shadow-lg shadow-primary-500/30">
                        <Zap className="text-white" size={20} />
                    </div>
                    <div>
                        <h2 className="text-lg font-bold text-gray-900">Scenario Simulator</h2>
                        <p className="text-sm text-gray-500">Predict outcomes with AI</p>
                    </div>
                </div>

                <div className="space-y-5">
                    <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">Target Competitor</label>
                        <select
                            className="w-full px-4 py-3 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary-500/20 focus:border-primary-400 transition-all"
                            value={competitor}
                            onChange={(e) => setCompetitor(e.target.value)}
                        >
                            <option value="">Select a competitor...</option>
                            {competitors?.map((c) => (
                                <option key={c.id} value={c.name}>{c.name}</option>
                            ))}
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">What-If Scenario</label>
                        <textarea
                            className="w-full px-4 py-3 bg-white border border-gray-200 rounded-xl h-32 focus:ring-2 focus:ring-primary-500/20 focus:border-primary-400 transition-all resize-none"
                            placeholder="Example: Competitor drops pricing by 20% for Enterprise tier..."
                            value={scenario}
                            onChange={(e) => setScenario(e.target.value)}
                        />
                    </div>

                    <button
                        onClick={handleRunSimulation}
                        disabled={loading || !competitor || !scenario}
                        className={`w-full py-4 rounded-xl font-semibold flex items-center justify-center gap-2 transition-all duration-300
                            ${loading
                                ? 'bg-gray-200 text-gray-500 cursor-wait'
                                : 'bg-gradient-to-r from-primary-500 to-primary-600 text-white shadow-lg shadow-primary-500/30 hover:shadow-xl hover:shadow-primary-500/40 hover:-translate-y-0.5'
                            } disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0`}
                    >
                        {loading ? (
                            <>
                                <div className="w-5 h-5 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" />
                                Running Simulation...
                            </>
                        ) : (
                            <>
                                <Play size={18} />
                                Run Simulation
                            </>
                        )}
                    </button>
                </div>
            </div>

            {/* Output / Results */}
            <div className="card overflow-auto max-h-[80vh]">
                {!result ? (
                    <div className="h-full min-h-[400px] flex flex-col items-center justify-center text-gray-400">
                        <div className="w-16 h-16 rounded-2xl bg-gray-100 flex items-center justify-center mb-4">
                            <Sparkles size={28} className="text-gray-300" />
                        </div>
                        <p className="text-sm font-medium">Awaiting simulation...</p>
                        <p className="text-xs text-gray-400 mt-1">Configure a scenario to get started</p>
                    </div>
                ) : (
                    <div className="animate-in space-y-6">
                        <div className="flex items-center justify-between">
                            <h3 className="text-lg font-bold text-gray-900">Prediction Results</h3>
                            <span className="badge-primary">
                                <Sparkles size={12} className="mr-1" />
                                AI Powered
                            </span>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="p-4 rounded-xl bg-gradient-to-br from-rose-50 to-orange-50 border border-rose-100">
                                <label className="text-xs font-medium text-gray-500 uppercase">Win Rate Impact</label>
                                <div className="flex items-center gap-2 text-2xl font-bold text-rose-600 mt-1">
                                    <TrendingDown size={24} />
                                    {result.win_rate_prediction}
                                </div>
                            </div>
                            <div className="p-4 rounded-xl bg-gradient-to-br from-amber-50 to-yellow-50 border border-amber-100">
                                <label className="text-xs font-medium text-gray-500 uppercase">Risk Level</label>
                                <div className="flex items-center gap-2 text-2xl font-bold text-amber-600 mt-1">
                                    <AlertTriangle size={24} />
                                    {result.win_rate_prediction?.includes('-') ? 'High' : 'Moderate'}
                                </div>
                            </div>
                        </div>

                        <div>
                            <label className="text-xs font-medium text-gray-500 uppercase block mb-2">Market Reaction</label>
                            <div className="p-4 bg-amber-50/50 text-amber-900 rounded-xl text-sm border border-amber-100 italic">
                                "{result.market_reaction}"
                            </div>
                        </div>

                        <div>
                            <label className="text-xs font-medium text-gray-500 uppercase block mb-2">Expected Objections</label>
                            <ul className="space-y-2">
                                {result.new_objections?.map((obj: string, i: number) => (
                                    <li key={i} className="flex items-start gap-3 p-3 bg-rose-50/50 rounded-xl border border-rose-100">
                                        <span className="w-6 h-6 rounded-lg bg-rose-100 flex items-center justify-center text-rose-600 font-bold text-xs flex-shrink-0">!</span>
                                        <span className="text-sm text-gray-700">{obj}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>

                        {/* Risk Heatmap */}
                        <RiskHeatmap
                            winRateImpact={result.win_rate_prediction}
                            marketReaction={result.market_reaction}
                            objectionsCount={result.new_objections?.length || 0}
                        />

                        <div>
                            <label className="text-xs font-medium text-gray-500 uppercase block mb-2">Recommended Counter-Strategy</label>
                            <div className="p-4 bg-gradient-to-br from-emerald-50 to-teal-50 rounded-xl border border-emerald-100">
                                <div className="flex items-start gap-3">
                                    <div className="w-8 h-8 rounded-lg bg-emerald-100 flex items-center justify-center flex-shrink-0">
                                        <Shield size={18} className="text-emerald-600" />
                                    </div>
                                    <p className="text-sm text-emerald-900 font-medium leading-relaxed">{result.recommended_response}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
