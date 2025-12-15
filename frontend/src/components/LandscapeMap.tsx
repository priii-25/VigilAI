import { useQuery } from '@tanstack/react-query';
import { Bubble } from 'react-chartjs-2';
import { analyticsAPI } from '@/lib/api';
import {
    Chart as ChartJS,
    LinearScale,
    PointElement,
    Tooltip,
    Legend,
} from 'chart.js';

ChartJS.register(LinearScale, PointElement, Tooltip, Legend);

interface LandscapeDataPoint {
    id: number;
    name: string;
    x: number;
    y: number;
    r: number;
    industry: string;
    color?: string;
}

export default function LandscapeMap() {
    // Fetch real landscape data from backend API
    const { data: landscapeData, isLoading, error } = useQuery<LandscapeDataPoint[]>({
        queryKey: ['competitive-landscape'],
        queryFn: async () => {
            const response = await analyticsAPI.getLandscape();
            return response.data;
        },
        staleTime: 60000, // Cache for 1 minute
    });

    const buildChartData = () => {
        if (!landscapeData || landscapeData.length === 0) {
            // Return placeholder when no data
            return {
                datasets: [{
                    label: 'No Competitors',
                    data: [{ x: 50, y: 50, r: 10, competitor: 'Add competitors to see map' }],
                    backgroundColor: 'rgba(156, 163, 175, 0.5)',
                }]
            };
        }

        return {
            datasets: [{
                label: 'Competitors',
                data: landscapeData.map((d) => ({
                    x: d.x,
                    y: d.y,
                    r: d.r,
                    competitor: d.name,
                    industry: d.industry
                })),
                backgroundColor: landscapeData.map(d => d.color || 'rgba(59, 130, 246, 0.6)'),
                hoverBackgroundColor: landscapeData.map(d =>
                    d.color?.replace('0.7', '0.9') || 'rgba(59, 130, 246, 0.8)'
                ),
            }]
        };
    };

    const chartData = buildChartData();

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
                        return [
                            `${point.competitor || 'Unknown'}`,
                            `Features: ${point.x}`,
                            `Price Tier: ${point.y}`,
                            point.industry ? `Industry: ${point.industry}` : ''
                        ].filter(Boolean);
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

    // Industry color legend
    const industryColors = [
        { label: 'Fintech', color: 'bg-blue-500' },
        { label: 'SaaS', color: 'bg-green-500' },
        { label: 'E-commerce', color: 'bg-orange-500' },
        { label: 'Healthcare', color: 'bg-red-500' },
        { label: 'Other', color: 'bg-gray-500' },
    ];

    if (isLoading) {
        return (
            <div className="card h-full animate-pulse">
                <div className="h-6 bg-gray-200 rounded w-1/2 mb-4"></div>
                <div className="h-[400px] bg-gray-100 rounded"></div>
            </div>
        );
    }

    return (
        <div className="card h-full">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Competitive Landscape Map</h3>
            <div className="h-[400px] relative">
                <Bubble options={options} data={chartData} />
            </div>
            <div className="mt-4 flex flex-wrap gap-3 text-sm text-gray-500 justify-center">
                {industryColors.map(({ label, color }) => (
                    <div key={label} className="flex items-center gap-1">
                        <div className={`w-3 h-3 rounded-full ${color}`}></div>
                        <span>{label}</span>
                    </div>
                ))}
            </div>
            {landscapeData && (
                <p className="text-center text-xs text-gray-400 mt-2">
                    Showing {landscapeData.length} competitor{landscapeData.length !== 1 ? 's' : ''}
                </p>
            )}
        </div>
    );
}
