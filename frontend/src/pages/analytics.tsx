import { useQuery } from '@tanstack/react-query';
import { analyticsAPI } from '@/lib/api';
import Head from 'next/head';
import Sidebar from '@/components/layout/Sidebar';
import Header from '@/components/layout/Header';
import { TrendingUp, TrendingDown, Users, Target, Award, Activity, BarChart3, Eye } from 'lucide-react';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
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
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

export default function Analytics() {
  const { data: metrics, isLoading } = useQuery({
    queryKey: ['analytics-metrics'],
    queryFn: async () => {
      const response = await analyticsAPI.getMetrics();
      return response.data;
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const { data: battlecardUsage } = useQuery({
    queryKey: ['battlecard-usage'],
    queryFn: async () => {
      const response = await analyticsAPI.getBattlecardUsage();
      return response.data;
    },
  });

  const { data: winRates } = useQuery({
    queryKey: ['win-rates'],
    queryFn: async () => {
      const response = await analyticsAPI.getWinRates();
      return response.data;
    },
  });

  const { data: impactScores } = useQuery({
    queryKey: ['impact-scores'],
    queryFn: async () => {
      const response = await analyticsAPI.getImpactScores();
      return response.data;
    },
  });

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  // Chart Data
  const winRateChartData = {
    labels: winRates?.timeline?.map((d: any) => d.date) || [],
    datasets: [
      {
        label: 'With Battlecard',
        data: winRates?.timeline?.map((d: any) => d.with_battlecard) || [],
        borderColor: 'rgb(34, 197, 94)',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        fill: true,
        tension: 0.4,
      },
      {
        label: 'Without Battlecard',
        data: winRates?.timeline?.map((d: any) => d.without_battlecard) || [],
        borderColor: 'rgb(239, 68, 68)',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        fill: true,
        tension: 0.4,
      },
    ],
  };

  const usageChartData = {
    labels: battlecardUsage?.top_cards?.map((c: any) => c.title) || [],
    datasets: [
      {
        label: 'Views',
        data: battlecardUsage?.top_cards?.map((c: any) => c.views) || [],
        backgroundColor: 'rgba(59, 130, 246, 0.8)',
      },
    ],
  };

  const impactChartData = {
    labels: ['Critical (9-10)', 'High (7-8)', 'Medium (4-6)', 'Low (0-3)'],
    datasets: [
      {
        data: [
          impactScores?.distribution?.critical || 0,
          impactScores?.distribution?.high || 0,
          impactScores?.distribution?.medium || 0,
          impactScores?.distribution?.low || 0,
        ],
        backgroundColor: [
          'rgba(239, 68, 68, 0.8)',
          'rgba(249, 115, 22, 0.8)',
          'rgba(234, 179, 8, 0.8)',
          'rgba(34, 197, 94, 0.8)',
        ],
      },
    ],
  };

  return (
    <>
      <Head>
        <title>Analytics - VigilAI</title>
      </Head>

      <div className="flex h-screen bg-gray-100">
        <Sidebar />
        
        <div className="flex-1 flex flex-col overflow-hidden">
          <Header />
          
          <main className="flex-1 overflow-y-auto p-6">
            <div className="max-w-7xl mx-auto">
              <h1 className="text-3xl font-bold text-gray-900 mb-6">Analytics Dashboard</h1>

              {/* Key Metrics */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
                <MetricCard
                  title="Win Rate"
                  value={`${metrics?.win_rate || 0}%`}
                  change={metrics?.win_rate_change || 0}
                  icon={<Award className="text-yellow-600" size={24} />}
                  trend={metrics?.win_rate_trend}
                />
                <MetricCard
                  title="Active Competitors"
                  value={metrics?.active_competitors || 0}
                  change={metrics?.competitor_change || 0}
                  icon={<Users className="text-blue-600" size={24} />}
                  trend={metrics?.competitor_trend}
                />
                <MetricCard
                  title="Battlecard Views"
                  value={metrics?.battlecard_views || 0}
                  change={metrics?.views_change || 0}
                  icon={<Eye className="text-green-600" size={24} />}
                  trend={metrics?.views_trend}
                />
                <MetricCard
                  title="Avg Impact Score"
                  value={metrics?.avg_impact_score?.toFixed(1) || '0.0'}
                  change={metrics?.impact_change || 0}
                  icon={<Activity className="text-purple-600" size={24} />}
                  trend={metrics?.impact_trend}
                />
              </div>

              {/* Charts Row 1 */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                {/* Win Rate Trend */}
                <div className="card">
                  <h2 className="text-lg font-bold text-gray-900 mb-4">Win Rate Trends</h2>
                  <Line
                    data={winRateChartData}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: { position: 'top' },
                        tooltip: {
                          callbacks: {
                            label: (context: any) => `${context.dataset.label}: ${context.parsed.y}%`,
                          },
                        },
                      },
                      scales: {
                        y: {
                          beginAtZero: true,
                          max: 100,
                          ticks: {
                            callback: (value: any) => `${value}%`,
                          },
                        },
                      },
                    }}
                    height={250}
                  />
                  <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                    <p className="text-sm text-blue-900">
                      <strong>Insight:</strong> Deals with battlecard usage show{' '}
                      {winRates?.improvement || 0}% higher win rate
                    </p>
                  </div>
                </div>

                {/* Top Battlecards */}
                <div className="card">
                  <h2 className="text-lg font-bold text-gray-900 mb-4">Most Viewed Battlecards</h2>
                  <Bar
                    data={usageChartData}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      indexAxis: 'y',
                      plugins: {
                        legend: { display: false },
                      },
                      scales: {
                        x: {
                          beginAtZero: true,
                        },
                      },
                    }}
                    height={250}
                  />
                </div>
              </div>

              {/* Charts Row 2 */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
                {/* Impact Score Distribution */}
                <div className="card">
                  <h2 className="text-lg font-bold text-gray-900 mb-4">Alert Impact Distribution</h2>
                  <Doughnut
                    data={impactChartData}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: { position: 'bottom' },
                      },
                    }}
                    height={200}
                  />
                </div>

                {/* Recent Activity */}
                <div className="card lg:col-span-2">
                  <h2 className="text-lg font-bold text-gray-900 mb-4">Recent Activity</h2>
                  <div className="space-y-3 max-h-[300px] overflow-y-auto">
                    {metrics?.recent_activity?.map((activity: any, idx: number) => (
                      <div key={idx} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                        <div className={`p-2 rounded-lg ${getActivityColor(activity.type)}`}>
                          {getActivityIcon(activity.type)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {activity.title}
                          </p>
                          <p className="text-xs text-gray-600 mt-1">{activity.description}</p>
                          <p className="text-xs text-gray-500 mt-1">
                            {new Date(activity.timestamp).toLocaleString()}
                          </p>
                        </div>
                        {activity.impact_score && (
                          <span className={`px-2 py-1 rounded text-xs font-medium ${getImpactBadge(activity.impact_score)}`}>
                            {activity.impact_score}/10
                          </span>
                        )}
                      </div>
                    )) || (
                      <p className="text-center text-gray-500 py-8">No recent activity</p>
                    )}
                  </div>
                </div>
              </div>

              {/* Competitor Performance */}
              <div className="card">
                <h2 className="text-lg font-bold text-gray-900 mb-4">Competitor Performance</h2>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-gray-200">
                        <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Competitor</th>
                        <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Win Rate vs Them</th>
                        <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Deals</th>
                        <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Avg Deal Size</th>
                        <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Trend</th>
                      </tr>
                    </thead>
                    <tbody>
                      {metrics?.competitor_performance?.map((comp: any) => (
                        <tr key={comp.id} className="border-b border-gray-100 hover:bg-gray-50">
                          <td className="py-3 px-4 text-sm font-medium text-gray-900">{comp.name}</td>
                          <td className="py-3 px-4 text-sm">
                            <span className={`font-semibold ${comp.win_rate >= 50 ? 'text-green-600' : 'text-red-600'}`}>
                              {comp.win_rate}%
                            </span>
                          </td>
                          <td className="py-3 px-4 text-sm text-gray-600">{comp.total_deals}</td>
                          <td className="py-3 px-4 text-sm text-gray-600">${comp.avg_deal_size?.toLocaleString()}</td>
                          <td className="py-3 px-4">
                            {comp.trend === 'up' ? (
                              <TrendingUp className="text-green-600" size={20} />
                            ) : (
                              <TrendingDown className="text-red-600" size={20} />
                            )}
                          </td>
                        </tr>
                      )) || (
                        <tr>
                          <td colSpan={5} className="text-center py-8 text-gray-500">
                            No data available
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </main>
        </div>
      </div>
    </>
  );
}

function MetricCard({ title, value, change, icon, trend }: any) {
  const isPositive = change >= 0;
  
  return (
    <div className="card">
      <div className="flex items-start justify-between mb-3">
        <div className="p-2 bg-gray-100 rounded-lg">{icon}</div>
        <div className={`flex items-center gap-1 text-sm font-medium ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
          {isPositive ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
          {Math.abs(change)}%
        </div>
      </div>
      <h3 className="text-2xl font-bold text-gray-900 mb-1">{value}</h3>
      <p className="text-sm text-gray-600">{title}</p>
    </div>
  );
}

function getActivityIcon(type: string) {
  switch (type) {
    case 'pricing':
      return <Target size={16} className="text-orange-600" />;
    case 'feature':
      return <BarChart3 size={16} className="text-blue-600" />;
    case 'battlecard':
      return <Eye size={16} className="text-green-600" />;
    default:
      return <Activity size={16} className="text-gray-600" />;
  }
}

function getActivityColor(type: string) {
  switch (type) {
    case 'pricing':
      return 'bg-orange-100';
    case 'feature':
      return 'bg-blue-100';
    case 'battlecard':
      return 'bg-green-100';
    default:
      return 'bg-gray-100';
  }
}

function getImpactBadge(score: number) {
  if (score >= 9) return 'bg-red-100 text-red-800';
  if (score >= 7) return 'bg-orange-100 text-orange-800';
  if (score >= 4) return 'bg-yellow-100 text-yellow-800';
  return 'bg-green-100 text-green-800';
}
