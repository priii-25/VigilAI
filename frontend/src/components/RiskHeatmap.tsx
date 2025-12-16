import React from 'react';
import { Flame } from 'lucide-react';

interface RiskHeatmapProps {
    winRateImpact: string;
    marketReaction: string;
    objectionsCount: number;
}

export default function RiskHeatmap({ winRateImpact, marketReaction, objectionsCount }: RiskHeatmapProps) {
    const parseImpact = (impact: string): number => {
        const match = impact.match(/-?\d+/);
        return match ? parseInt(match[0]) : 0;
    };

    const impactValue = parseImpact(winRateImpact);

    const winRateRisk = Math.min(100, Math.max(0, Math.abs(impactValue) * 10));
    const marketRisk = marketReaction.toLowerCase().includes('churn') ||
        marketReaction.toLowerCase().includes('demand') ? 80 : 40;
    const objectionsRisk = Math.min(100, objectionsCount * 25);
    const overallRisk = Math.round((winRateRisk + marketRisk + objectionsRisk) / 3);

    const getRiskColor = (value: number) => {
        if (value >= 70) return { bg: 'bg-rose-500', light: 'bg-rose-100', text: 'text-rose-600' };
        if (value >= 40) return { bg: 'bg-amber-500', light: 'bg-amber-100', text: 'text-amber-600' };
        return { bg: 'bg-emerald-500', light: 'bg-emerald-100', text: 'text-emerald-600' };
    };

    const getRiskLabel = (value: number) => {
        if (value >= 70) return 'HIGH';
        if (value >= 40) return 'MEDIUM';
        return 'LOW';
    };

    const metrics = [
        { label: 'Win Rate Risk', value: winRateRisk },
        { label: 'Market Impact', value: marketRisk },
        { label: 'Objection Severity', value: objectionsRisk },
    ];

    const overallColor = getRiskColor(overallRisk);

    return (
        <div className="p-5 rounded-xl bg-gradient-to-br from-gray-50 to-gray-100 border border-gray-200">
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <Flame size={18} className="text-gray-500" />
                    <h4 className="text-sm font-semibold text-gray-700">Risk Assessment</h4>
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-bold ${overallColor.light} ${overallColor.text}`}>
                    {getRiskLabel(overallRisk)} RISK
                </span>
            </div>

            <div className="space-y-3">
                {metrics.map((metric) => {
                    const color = getRiskColor(metric.value);
                    return (
                        <div key={metric.label}>
                            <div className="flex justify-between text-xs mb-1.5">
                                <span className="text-gray-500 font-medium">{metric.label}</span>
                                <span className="font-semibold text-gray-700">{metric.value}%</span>
                            </div>
                            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                                <div
                                    className={`h-full ${color.bg} transition-all duration-700 ease-out rounded-full`}
                                    style={{ width: `${metric.value}%` }}
                                />
                            </div>
                        </div>
                    );
                })}
            </div>

            <div className="mt-5 pt-4 border-t border-gray-200">
                <div className="flex items-center justify-center gap-3">
                    <div className={`w-14 h-14 rounded-xl ${overallColor.light} flex items-center justify-center`}>
                        <span className={`text-2xl font-bold ${overallColor.text}`}>{overallRisk}</span>
                    </div>
                    <div>
                        <p className="text-xs text-gray-500">Overall Threat Score</p>
                        <p className={`text-sm font-semibold ${overallColor.text}`}>{getRiskLabel(overallRisk)} Priority</p>
                    </div>
                </div>
            </div>
        </div>
    );
}
