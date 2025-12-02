import { useQuery } from '@tanstack/react-query';
import { dashboardAPI } from '@/lib/api';
import { Target, TrendingUp, FileText, AlertTriangle } from 'lucide-react';

export default function DashboardStats() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const response = await dashboardAPI.getStats();
      return response.data;
    },
  });

  if (isLoading) {
    return <div className="text-gray-600">Loading stats...</div>;
  }

  const statCards = [
    {
      title: 'Active Competitors',
      value: stats?.competitors || 0,
      icon: Target,
      color: 'bg-blue-500',
    },
    {
      title: 'Recent Updates',
      value: stats?.recent_updates || 0,
      icon: TrendingUp,
      color: 'bg-green-500',
    },
    {
      title: 'Battlecards',
      value: stats?.battlecards || 0,
      icon: FileText,
      color: 'bg-purple-500',
    },
    {
      title: 'Open Incidents',
      value: stats?.open_incidents || 0,
      icon: AlertTriangle,
      color: 'bg-red-500',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {statCards.map((stat) => {
        const Icon = stat.icon;
        return (
          <div key={stat.title} className="card">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-gray-600 text-sm">{stat.title}</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{stat.value}</p>
              </div>
              <div className={`${stat.color} p-3 rounded-lg`}>
                <Icon className="text-white" size={24} />
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
