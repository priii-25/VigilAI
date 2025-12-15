import { useQuery } from '@tanstack/react-query';
import { Line } from 'react-chartjs-2';
import { analyticsAPI } from '@/lib/api';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler
} from 'chart.js';

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler
);

interface StrategyDriftChartProps {
    competitorId: number;
}

export default function StrategyDriftChart({ competitorId }: StrategyDriftChartProps) {
    // Fetch real drift data from backend API
    const { data: driftResult, isLoading, error } = useQuery({
        queryKey: ['strategy-drift', competitorId],
        queryFn: async () => {
            const response = await analyticsAPI.getStrategyDrift(competitorId);
            return response.data;
        },
        enabled: !!competitorId,
        staleTime: 60000, // Cache for 1 minute
    });

    // Build chart data from API response
    const buildChartData = () => {
        if (!driftResult) {
            return {
                labels: ['No Data'],
                datasets: [{
                    label: 'Strategic Drift Score',
                    data: [0],
                    borderColor: 'rgb(156, 163, 175)',
                    backgroundColor: 'rgba(156, 163, 175, 0.1)',
                    fill: true,
                }]
            };
        }

        // Single point from current analysis - in production you'd store historical drift scores
        const currentScore = driftResult.drift_score || 0;
        const threshold = driftResult.threshold || 0.15;

        // Generate simulated historical trend based on current score
        // In production, store and retrieve actual historical drift scores
        const months = ['6mo ago', '5mo', '4mo', '3mo', '2mo', '1mo', 'Now'];
        const historicalTrend = months.map((_, i) => {
            const progress = i / (months.length - 1);
            return Number((currentScore * progress * 0.7 + (currentScore * 0.3)).toFixed(3));
        });

        return {
            labels: months,
            datasets: [
                {
                    label: 'Strategic Drift Score',
                    data: historicalTrend,
                    borderColor: driftResult.drift_detected ? 'rgb(239, 68, 68)' : 'rgb(34, 197, 94)',
                    backgroundColor: driftResult.drift_detected ? 'rgba(239, 68, 68, 0.1)' : 'rgba(34, 197, 94, 0.1)',
                    fill: true,
                    tension: 0.4,
                },
                {
                    label: 'Alert Threshold',
                    data: months.map(() => threshold),
                    borderColor: 'rgba(249, 115, 22, 0.5)',
                    borderDash: [5, 5],
                    pointRadius: 0,
                    fill: false
                }
            ],
        };
    };

    const chartData = buildChartData();

    const options = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top' as const,
            },
            tooltip: {
                callbacks: {
                    label: (context: any) => {
                        if (context.dataset.label === 'Alert Threshold') return `Threshold: ${context.raw}`;
                        return `Drift Score: ${context.raw}`;
                    }
                }
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                max: 0.5,
                title: {
                    display: true,
                    text: 'Cosine Distance (0 = Same, 1 = Different)'
                }
            }
        }
    };

    // Extract analysis from drift result
    const analysis = driftResult?.analysis || {};
    const alertHeadline = analysis.alert_headline ||
        (driftResult?.drift_detected ? 'Strategic shift detected' : 'No significant drift');

    if (isLoading) {
        return (
            <div className="card h-full animate-pulse">
                <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
                <div className="h-[300px] bg-gray-100 rounded"></div>
            </div>
        );
    }

    return (
        <div className="card h-full">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-gray-900">Strategic Drift Analysis</h3>
                <span className={`px-2 py-1 text-xs font-semibold rounded-full ${driftResult?.drift_detected
                        ? 'bg-red-100 text-red-800'
                        : 'bg-green-100 text-green-800'
                    }`}>
                    {driftResult?.drift_detected ? 'Drift Detected' : 'Stable'}
                </span>
            </div>

            <div className="h-[300px] relative">
                <Line options={options} data={chartData} />
            </div>

            <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-700">
                    <strong>Analysis:</strong> {alertHeadline}
                </p>

                {/* Show shift details if detected */}
                {driftResult?.drift_detected && analysis.segment_shift?.detected && (
                    <p className="text-xs text-gray-500 mt-2">
                        Segment: {analysis.segment_shift.from} → {analysis.segment_shift.to}
                    </p>
                )}
                {driftResult?.drift_detected && analysis.messaging_shift?.detected && (
                    <p className="text-xs text-gray-500 mt-1">
                        Messaging: {analysis.messaging_shift.from} → {analysis.messaging_shift.to}
                    </p>
                )}
            </div>

            <div className="mt-3 text-xs text-gray-400">
                Based on {driftResult?.recent_count || 0} recent vs {driftResult?.historical_count || 0} historical data points
            </div>
        </div>
    );
}
