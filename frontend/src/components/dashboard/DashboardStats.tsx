import { useQuery } from '@tanstack/react-query';
import { dashboardAPI } from '@/lib/api';
import { Target, TrendingUp, FileText, AlertTriangle, ArrowUpRight, ArrowDownRight } from 'lucide-react';

export default function DashboardStats() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const response = await dashboardAPI.getStats();
      return response.data;
    },
  });

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="card animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
            <div className="h-8 bg-gray-200 rounded w-1/3"></div>
          </div>
        ))}
      </div>
    );
  }

  const statCards = [
    {
      title: 'Active Competitors',
      value: stats?.competitors || 0,
      change: '+2 this week',
      trend: 'up',
      icon: Target,
      gradient: 'from-primary-500 to-primary-600',
      lightBg: 'from-primary-50 to-primary-100/50',
    },
    {
      title: 'Recent Updates',
      value: stats?.recent_updates || 0,
      change: '+12 today',
      trend: 'up',
      icon: TrendingUp,
      gradient: 'from-accent-500 to-accent-600',
      lightBg: 'from-accent-50 to-accent-100/50',
    },
    {
      title: 'Battlecards',
      value: stats?.battlecards || 0,
      change: '+3 published',
      trend: 'up',
      icon: FileText,
      gradient: 'from-violet-500 to-violet-600',
      lightBg: 'from-violet-50 to-violet-100/50',
    },
    {
      title: 'Open Incidents',
      value: stats?.open_incidents || 0,
      change: stats?.open_incidents > 0 ? 'Needs attention' : 'All clear',
      trend: stats?.open_incidents > 0 ? 'down' : 'up',
      icon: AlertTriangle,
      gradient: stats?.open_incidents > 0 ? 'from-rose-500 to-rose-600' : 'from-emerald-500 to-emerald-600',
      lightBg: stats?.open_incidents > 0 ? 'from-rose-50 to-rose-100/50' : 'from-emerald-50 to-emerald-100/50',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {statCards.map((stat) => {
        const Icon = stat.icon;
        return (
          <div
            key={stat.title}
            className="card-hover relative overflow-hidden group"
          >
            {/* Background decoration */}
            <div className={`absolute -top-4 -right-4 w-24 h-24 bg-gradient-to-br ${stat.lightBg} rounded-full opacity-60 group-hover:scale-110 transition-transform duration-500`} />

            <div className="relative">
              <div className="flex items-start justify-between mb-4">
                <div className={`p-3 rounded-xl bg-gradient-to-br ${stat.gradient} shadow-lg`}>
                  <Icon className="text-white" size={22} />
                </div>
                <div className={`flex items-center gap-1 text-xs font-medium ${stat.trend === 'up' ? 'text-emerald-600' : 'text-rose-600'
                  }`}>
                  {stat.trend === 'up' ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
                  <span>{stat.change}</span>
                </div>
              </div>

              <div>
                <p className="text-sm font-medium text-gray-500">{stat.title}</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">{stat.value}</p>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
