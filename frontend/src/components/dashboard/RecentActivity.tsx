import { useQuery } from '@tanstack/react-query';
import { dashboardAPI } from '@/lib/api';
import { format } from 'date-fns';
import { Clock, Zap, TrendingUp, DollarSign, Users, Briefcase } from 'lucide-react';

export default function RecentActivity() {
  const { data: activities, isLoading } = useQuery({
    queryKey: ['recent-activity'],
    queryFn: async () => {
      const response = await dashboardAPI.getRecentActivity();
      return response.data;
    },
  });

  if (isLoading) {
    return (
      <div className="card">
        <div className="h-6 bg-gray-200 rounded w-1/4 mb-6 animate-pulse"></div>
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="p-4 bg-gray-50 rounded-xl animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  const getImpactStyle = (score: number) => {
    if (score >= 8) return { bg: 'bg-rose-100', text: 'text-rose-700', border: 'border-rose-200' };
    if (score >= 6) return { bg: 'bg-amber-100', text: 'text-amber-700', border: 'border-amber-200' };
    if (score >= 4) return { bg: 'bg-sky-100', text: 'text-sky-700', border: 'border-sky-200' };
    return { bg: 'bg-emerald-100', text: 'text-emerald-700', border: 'border-emerald-200' };
  };

  const getCategoryIcon = (category: string) => {
    switch (category?.toLowerCase()) {
      case 'pricing': return DollarSign;
      case 'hiring': return Users;
      case 'strategy': return Briefcase;
      default: return Zap;
    }
  };

  const getCategoryStyle = (category: string) => {
    switch (category?.toLowerCase()) {
      case 'pricing': return 'from-emerald-500 to-teal-500';
      case 'hiring': return 'from-violet-500 to-purple-500';
      case 'strategy': return 'from-amber-500 to-orange-500';
      default: return 'from-primary-500 to-primary-600';
    }
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-gray-900">Recent Activity</h2>
        <span className="badge-primary">
          <Clock size={12} className="mr-1" />
          Live
        </span>
      </div>

      <div className="space-y-3">
        {activities && activities.length > 0 ? (
          activities.slice(0, 5).map((activity: any, index: number) => {
            const impactStyle = getImpactStyle(activity.impact_score);
            const CategoryIcon = getCategoryIcon(activity.category);
            const categoryGradient = getCategoryStyle(activity.category);

            return (
              <div
                key={index}
                className="flex items-start gap-4 p-4 bg-gradient-to-r from-gray-50/50 to-white rounded-xl border border-gray-100 hover:border-primary-200 hover:shadow-soft transition-all duration-300 group"
              >
                <div className={`p-2.5 rounded-xl bg-gradient-to-br ${categoryGradient} shadow-lg flex-shrink-0 group-hover:scale-110 transition-transform duration-300`}>
                  <CategoryIcon className="text-white" size={18} />
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1 flex-wrap">
                    <h3 className="font-semibold text-gray-900 truncate">{activity.title}</h3>
                    <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${impactStyle.bg} ${impactStyle.text} border ${impactStyle.border}`}>
                      {activity.impact_score}/10
                    </span>
                  </div>
                  <p className="text-gray-600 text-sm mb-2 line-clamp-2">{activity.summary}</p>
                  <div className="flex items-center gap-3 text-xs text-gray-400">
                    <span className="capitalize px-2 py-0.5 bg-gray-100 rounded-full">
                      {activity.category?.replace('_', ' ') || 'Update'}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock size={12} />
                      {format(new Date(activity.timestamp), 'MMM d, h:mm a')}
                    </span>
                  </div>
                </div>
              </div>
            );
          })
        ) : (
          <div className="text-center py-12">
            <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gray-100 flex items-center justify-center">
              <TrendingUp size={28} className="text-gray-300" />
            </div>
            <p className="text-gray-500 font-medium">No recent activity</p>
            <p className="text-sm text-gray-400 mt-1">Updates will appear here</p>
          </div>
        )}
      </div>
    </div>
  );
}
