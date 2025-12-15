import React from 'react';

interface RiskHeatmapProps {
    winRateImpact: string;
    marketReaction: string;
    objectionsCount: number;
}

export default function RiskHeatmap({ winRateImpact, marketReaction, objectionsCount }: RiskHeatmapProps) {
    // Parse win rate impact to determine color
    const parseImpact = (impact: string): number => {
        const match = impact.match(/-?\d+/);
        return match ? parseInt(match[0]) : 0;
    };

    const impactValue = parseImpact(winRateImpact);

    // Calculate risk scores (0-100)
    const winRateRisk = Math.min(100, Math.max(0, Math.abs(impactValue) * 10));
    const marketRisk = marketReaction.toLowerCase().includes('churn') ||
        marketReaction.toLowerCase().includes('demand') ? 80 : 40;
    const objectionsRisk = Math.min(100, objectionsCount * 25);
    const overallRisk = Math.round((winRateRisk + marketRisk + objectionsRisk) / 3);

    const getRiskColor = (value: number) => {
        if (value >= 70) return 'bg-red-500';
        if (value >= 40) return 'bg-yellow-500';
        return 'bg-green-500';
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

    return (
        <div className="bg-gray-900 rounded-lg p-4 text-white">
            <div className="flex items-center justify-between mb-4">
                <h4 className="text-sm font-mono uppercase text-gray-400">Risk Heatmap</h4>
                <span className={`px-2 py-1 rounded text-xs font-bold ${getRiskColor(overallRisk)} text-white`}>
                    {getRiskLabel(overallRisk)} RISK
                </span>
            </div>

            <div className="space-y-3">
                {metrics.map((metric) => (
                    <div key={metric.label}>
                        <div className="flex justify-between text-xs mb-1">
                            <span className="text-gray-400">{metric.label}</span>
                            <span className="font-mono">{metric.value}%</span>
                        </div>
                        <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                            <div
                                className={`h-full ${getRiskColor(metric.value)} transition-all duration-500`}
                                style={{ width: `${metric.value}%` }}
                            />
                        </div>
                    </div>
                ))}
            </div>

            <div className="mt-4 pt-4 border-t border-gray-700">
                <div className="text-center">
                    <span className="text-2xl font-bold">{overallRisk}</span>
                    <span className="text-gray-400 text-sm ml-1">/ 100</span>
                </div>
                <p className="text-center text-xs text-gray-500 mt-1">Overall Threat Score</p>
            </div>
        </div>
    );
}
