import { useQuery } from '@tanstack/react-query';
import { dashboardAPI } from '@/lib/api';
import { format } from 'date-fns';

export default function RecentActivity() {
  const { data: activities, isLoading } = useQuery({
    queryKey: ['recent-activity'],
    queryFn: async () => {
      const response = await dashboardAPI.getRecentActivity();
      return response.data;
    },
  });

  if (isLoading) {
    return <div className="card">Loading activity...</div>;
  }

  const getImpactColor = (score: number) => {
    if (score >= 8) return 'text-red-600 bg-red-50';
    if (score >= 6) return 'text-orange-600 bg-orange-50';
    if (score >= 4) return 'text-yellow-600 bg-yellow-50';
    return 'text-green-600 bg-green-50';
  };

  return (
    <div className="card">
      <h2 className="text-xl font-bold text-gray-900 mb-4">Recent Activity</h2>
      
      <div className="space-y-4">
        {activities && activities.length > 0 ? (
          activities.map((activity: any, index: number) => (
            <div
              key={index}
              className="flex items-start gap-4 p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="font-semibold text-gray-900">{activity.title}</h3>
                  <span
                    className={`px-2 py-1 rounded text-xs font-medium ${getImpactColor(
                      activity.impact_score
                    )}`}
                  >
                    Impact: {activity.impact_score}/10
                  </span>
                </div>
                <p className="text-gray-600 text-sm mb-2">{activity.summary}</p>
                <div className="flex items-center gap-4 text-xs text-gray-500">
                  <span className="capitalize">{activity.category.replace('_', ' ')}</span>
                  <span>
                    {format(new Date(activity.timestamp), 'MMM d, yyyy h:mm a')}
                  </span>
                </div>
              </div>
            </div>
          ))
        ) : (
          <p className="text-gray-500 text-center py-8">No recent activity</p>
        )}
      </div>
    </div>
  );
}
