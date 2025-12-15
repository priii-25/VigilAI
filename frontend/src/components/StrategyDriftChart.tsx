import { Line } from 'react-chartjs-2';
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
    data?: any; // Start with loose typing for flexibility, tighten later
}

export default function StrategyDriftChart({ competitorId, data }: StrategyDriftChartProps) {
    // If data is passed directly (ssr/prop), use it. Otherwise we might fetch.
    // For now, let's assume parent fetches or we mock if missing for demo.

    const driftData = data || {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        datasets: [
            {
                label: 'Strategic Drift Score',
                data: [0.05, 0.06, 0.08, 0.12, 0.14, 0.18], // Rising drift
                borderColor: 'rgb(249, 115, 22)', // Orange
                backgroundColor: 'rgba(249, 115, 22, 0.1)',
                fill: true,
                tension: 0.4,
            },
            {
                label: 'Threshold',
                data: [0.15, 0.15, 0.15, 0.15, 0.15, 0.15],
                borderColor: 'rgba(239, 68, 68, 0.5)', // Red dashed
                borderDash: [5, 5],
                pointRadius: 0,
                fill: false
            }
        ],
    };

    const options = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top' as const,
            },
            title: {
                display: false,
                text: 'Strategic Drift Over Time',
            },
            tooltip: {
                callbacks: {
                    label: (context: any) => {
                        if (context.dataset.label === 'Threshold') return 'Alert Threshold: 0.15';
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
                    text: 'Cosine Distance (0 = Same, 1 = Diff)'
                }
            }
        }
    };

    return (
        <div className="card h-full">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-gray-900">Strategic Drift Analysis</h3>
                <span className="px-2 py-1 bg-orange-100 text-orange-800 text-xs font-semibold rounded-full">
                    High Alert
                </span>
            </div>
            <div className="h-[300px] relative">
                <Line options={options} data={driftData} />
            </div>
            <p className="text-sm text-gray-600 mt-4">
                <strong>Analysis:</strong> Competitor is drifting towards <em>Enterprise Security</em> messaging based on recent whitepapers and hiring trends.
            </p>
        </div>
    );
}
