import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { dashboardAPI } from '@/lib/api';
import { Radar, ArrowUpRight, DollarSign, Package, AlertCircle, AlertTriangle } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import Link from 'next/link';

interface ActivityItem {
    competitor_id: number;
    competitor_name: string;
    title: string;
    summary: string;
    category: string;
    impact_score: number;
    timestamp: string;
}

export default function CompetitorRadar() {
    const { data: activity, isLoading, isError } = useQuery<ActivityItem[]>({
        queryKey: ['recent-activity'],
        queryFn: async () => {
            const res = await dashboardAPI.getRecentActivity(10);
            return res.data;
        },
        refetchInterval: 30000,
        retry: 2
    });

    // Filter for "Radar-worthy" events: Pricing, Product, or High Impact
    const radarEvents = activity?.filter((item) =>
        ['pricing', 'product', 'acquisition', 'funding'].includes(item.category?.toLowerCase()) ||
        item.impact_score >= 7.0
    ) || [];

    const getIcon = (category: string) => {
        switch (category?.toLowerCase()) {
            case 'pricing': return <DollarSign className="text-yellow-600" size={18} />;
            case 'product': return <Package className="text-blue-600" size={18} />;
            case 'funding': return <ArrowUpRight className="text-green-600" size={18} />;
            default: return <AlertCircle className="text-primary-600" size={18} />;
        }
    };

    const getBgColor = (category: string) => {
        switch (category?.toLowerCase()) {
            case 'pricing': return 'bg-yellow-50 border-yellow-100 hover:border-yellow-200';
            case 'product': return 'bg-blue-50 border-blue-100 hover:border-blue-200';
            case 'funding': return 'bg-green-50 border-green-100 hover:border-green-200';
            default: return 'bg-primary-50 border-primary-100 hover:border-primary-200';
        }
    };

    if (isError) {
        return (
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden h-full flex flex-col items-center justify-center p-6 text-center">
                <AlertTriangle className="text-red-400 mb-2" size={32} />
                <h3 className="text-sm font-semibold text-gray-900">Connection Error</h3>
                <p className="text-xs text-gray-500 mt-1">Unable to connect to intelligence feed.</p>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden h-full flex flex-col">
            <div className="p-5 border-b border-gray-100 flex items-center justify-between bg-gray-50/50">
                <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                    <div className="relative">
                        <Radar className="text-primary-600" size={20} />
                        <span className="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>
                    </div>
                    Competitor Radar
                </h2>
                <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold text-green-600 bg-green-50 px-2 py-0.5 rounded-full border border-green-100 uppercase tracking-wide">
                        Active
                    </span>
                </div>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
                {isLoading ? (
                    [...Array(3)].map((_, i) => (
                        <div key={i} className="h-24 bg-gray-50 rounded-lg animate-pulse border border-gray-100" />
                    ))
                ) : radarEvents.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-center p-8 text-gray-400">
                        <Radar size={48} className="mb-4 opacity-10" />
                        <p className="text-sm font-medium text-gray-500">No critical alerts</p>
                        <p className="text-xs mt-1 text-gray-400">Monitoring pricing & product changes...</p>
                    </div>
                ) : (
                    radarEvents.map((event, idx) => (
                        <Link
                            key={idx}
                            href={`/competitors/${event.competitor_id}`}
                            className={`block p-4 rounded-lg border transition-all hover:shadow-md group relative ${getBgColor(event.category)}`}
                        >
                            <div className="flex justify-between items-start mb-2">
                                <span className="font-bold text-gray-900 text-sm flex items-center gap-2">
                                    {event.competitor_name}
                                </span>
                                <span className="text-xs font-medium text-gray-500 tabular-nums">
                                    {event.timestamp ? formatDistanceToNow(new Date(event.timestamp), { addSuffix: true }) : 'Just now'}
                                </span>
                            </div>

                            <h3 className="font-semibold text-gray-800 text-sm mb-1 line-clamp-1 group-hover:text-primary-700 transition-colors">
                                {event.title}
                            </h3>

                            <p className="text-xs text-gray-600 leading-relaxed line-clamp-2 mb-3">
                                {event.summary}
                            </p>

                            <div className="flex items-center gap-2">
                                <span className="flex items-center gap-1.5 px-2 py-1 bg-white/60 rounded text-xs font-medium text-gray-700 border border-gray-200/50">
                                    {getIcon(event.category)}
                                    {event.category?.toUpperCase() || 'UPDATE'}
                                </span>
                                {event.impact_score >= 7.5 && (
                                    <span className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs font-bold border border-red-200 flex items-center gap-1">
                                        CRITICAL
                                    </span>
                                )}
                            </div>
                        </Link>
                    ))
                )}
            </div>
            <div className="p-3 bg-gray-50 border-t border-gray-100 text-center">
                <p className="text-[10px] text-gray-400 flex items-center justify-center gap-1.5 uppercase tracking-wider font-medium">
                    <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></span>
                    Monitoring {radarEvents.length} Active Targets
                </p>
            </div>
        </div>
    );
}
