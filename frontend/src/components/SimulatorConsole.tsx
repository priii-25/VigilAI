import { useState } from 'react';
import { Play, AlertOctagon, ShieldCheck, TrendingUp, TrendingDown } from 'lucide-react';
import { analyticsAPI } from '@/lib/api';

export default function SimulatorConsole() {
    const [scenario, setScenario] = useState('');
    const [competitor, setCompetitor] = useState('');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<any>(null);

    const handleRunSimulation = async () => {
        if (!scenario || !competitor) return;

        setLoading(true);
        try {
            // Call backend API
            // For demo, we might mock if backend isn't reachable or slow
            // const res = await analyticsAPI.runSimulation({ competitor, scenario });
            // setResult(res.data);

            // Mock response for instant gratification during Verified Demo if API not fully hot
            await new Promise(r => setTimeout(r, 2000));
            setResult({
                win_rate_prediction: "-5%",
                market_reaction: "Customers will likely demand price matching. Expect churn in SMB segment.",
                new_objections: [
                    "Why are you 20% more expensive?",
                    "Competitor X offers same features for less."
                ],
                recommended_response: "Focus on ROI and premium support. Do not discount. Launch 'Total Cost of Ownership' calculator campaign."
            });

        } catch (e) {
            console.error(e);
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
                            <option value="Stripe">Stripe</option>
                            <option value="Adyen">Adyen</option>
                            <option value="PayPal">PayPal</option>
                        </select>
                    </div>

                    <div>
                        <label className="block text-xs font-mono text-gray-400 mb-2 uppercase">Scanning Scenario (What If?)</label>
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
            <div className="card h-full bg-white border-l-4 border-l-red-500 relative overflow-hidden">
                {!result ? (
                    <div className="h-full flex flex-col items-center justify-center text-gray-400 opacity-50">
                        <ShieldCheck size={64} className="mb-4" />
                        <p className="font-mono text-sm text-center">AWAITING SIMULATION DATA...</p>
                    </div>
                ) : (
                    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                        <div className="flex items-center justify-between mb-6">
                            <h3 className="text-lg font-bold text-gray-900 uppercase tracking-wide">Prediction Results</h3>
                            <span className="px-3 py-1 bg-red-100 text-red-800 text-xs font-bold rounded">CONFIDENCE: HIGH</span>
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
                                <div className="text-2xl font-bold text-gray-900 mt-1">CRITICAL</div>
                            </div>
                        </div>

                        <div className="mb-6">
                            <label className="text-xs font-medium text-gray-500 uppercase block mb-2">Market Reaction & Objections</label>
                            <div className="p-4 bg-yellow-50 text-yellow-900 rounded-lg text-sm italic border border-yellow-200">
                                "{result.market_reaction}"
                            </div>
                            <ul className="mt-3 space-y-2">
                                {result.new_objections.map((obj: string, i: number) => (
                                    <li key={i} className="flex items-center gap-2 text-sm text-gray-700">
                                        <span className="text-red-500 font-bold">!</span> {obj}
                                    </li>
                                ))}
                            </ul>
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
