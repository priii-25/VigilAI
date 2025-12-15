import { Bubble } from 'react-chartjs-2';
import {
    Chart as ChartJS,
    LinearScale,
    PointElement,
    Tooltip,
    Legend,
} from 'chart.js';

ChartJS.register(LinearScale, PointElement, Tooltip, Legend);

interface LandscapeMapProps {
    data?: any;
}

export default function LandscapeMap({ data }: LandscapeMapProps) {
    const chartData = data ? {
        datasets: [{
            label: 'Competitors',
            data: data.map((d: any) => ({
                x: d.x,
                y: d.y,
                r: d.r,
                competitor: d.name
            })),
            backgroundColor: 'rgba(59, 130, 246, 0.6)', // Blue
            hoverBackgroundColor: 'rgba(59, 130, 246, 0.8)',
        }]
    } : {
        datasets: [
            {
                label: 'Competitors',
                data: [
                    { x: 80, y: 30, r: 15, competitor: 'Competitor A' }, // High Impact, Low Velocity (Legacy)
                    { x: 40, y: 80, r: 20, competitor: 'Competitor B' }, // Med Impact, High Velocity (Challenger)
                    { x: 20, y: 20, r: 10, competitor: 'Competitor C' }, // Low Impact, Low Velocity (Niche)
                ],
                backgroundColor: [
                    'rgba(239, 68, 68, 0.6)',  // Red
                    'rgba(34, 197, 94, 0.6)',  // Green
                    'rgba(59, 130, 246, 0.6)', // Blue
                ],
            },
        ],
    };

    const options = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
            title: {
                display: true,
                text: 'Competitive Landscape (Feature Strength vs Pricing)'
            },
            tooltip: {
                callbacks: {
                    label: (context: any) => {
                        const point = context.raw;
                        return `${point.competitor || 'Unknown'}: Features ${point.x}, Price Tier ${point.y}`;
                    }
                }
            }
        },
        scales: {
            x: {
                title: { display: true, text: 'Feature Strength (0-100)' },
                min: 0,
                max: 100,
            },
            y: {
                title: { display: true, text: 'Pricing Position (Low → High)' },
                min: 0,
                max: 100,
            },
        },
    };

    return (
        <div className="card h-full">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Competitive Landscape Map</h3>
            <div className="h-[400px] relative">
                <Bubble options={options} data={chartData} />
            </div>
            <div className="mt-4 flex gap-4 text-sm text-gray-500 justify-center">
                <div className="flex items-center gap-1">
                    <div className="w-3 h-3 rounded-full bg-green-500"></div> Challenger
                </div>
                <div className="flex items-center gap-1">
                    <div className="w-3 h-3 rounded-full bg-red-500"></div> Legacy Leader
                </div>
                <div className="flex items-center gap-1">
                    <div className="w-3 h-3 rounded-full bg-blue-500"></div> Niche Player
                </div>
            </div>
        </div>
    );
}
