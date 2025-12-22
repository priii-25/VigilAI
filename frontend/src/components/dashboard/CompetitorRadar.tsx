import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { dashboardAPI } from '@/lib/api';
import { Radar, ArrowUpRight, DollarSign, Package, AlertCircle } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import Link from 'next/link';

export default function CompetitorRadar() {
    const { data: activity, isLoading } = useQuery({
        queryKey: ['recent-activity'],
        queryFn: async () => {
            const res = await dashboardAPI.getRecentActivity(10);
            return res.data;
        },
        refetchInterval: 30000 // Poll every 30s for "Radar" feel
    });

    // Filter for "Radar-worthy" events: Pricing, Product, or High Impact
    const radarEvents = activity?.filter((item: any) =>
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
            case 'pricing': return 'bg-yellow-50 border-yellow-100';
            case 'product': return 'bg-blue-50 border-blue-100';
            case 'funding': return 'bg-green-50 border-green-100';
            default: return 'bg-primary-50 border-primary-100';
        }
    };

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
                <span className="text-xs font-medium text-gray-500 bg-white px-2 py-1 rounded-full border border-gray-200 shadow-sm">
                    Live Monitoring
                </span>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {isLoading ? (
                    [1, 2, 3].map(i => (
                        <div key={i} className="h-24 bg-gray-50 rounded-lg animate-pulse" />
                    ))
                ) : radarEvents.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-center p-8 text-gray-400">
                        <Radar size={48} className="mb-4 opacity-20" />
                        <p className="text-sm">No critical alerts detected in the last 24h.</p>
                        <p className="text-xs mt-1">Monitoring pricing & product changes...</p>
                    </div>
                ) : (
                    radarEvents.map((event: any, idx: number) => (
                        <Link
                            key={idx}
                            href={`/competitors/${event.competitor_id}`}
                            className={`block p-4 rounded-lg border transition-all hover:shadow-md ${getBgColor(event.category)}`}
                        >
                            <div className="flex justify-between items-start mb-2">
                                <span className="font-bold text-gray-900 text-sm flex items-center gap-2">
                                    {event.competitor_name}
                                </span>
                                <span className="text-xs font-medium text-gray-500 tabular-nums">
                                    {event.timestamp ? formatDistanceToNow(new Date(event.timestamp), { addSuffix: true }) : 'Just now'}
                                </span>
                            </div>

                            <h3 className="font-semibold text-gray-800 text-sm mb-1 line-clamp-1">
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
                                {event.impact_score >= 8 && (
                                    <span className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs font-bold border border-red-200">
                                        CRITICAL
                                    </span>
                                )}
                            </div>
                        </Link>
                    ))
                )}
            </div>
            <div className="p-3 bg-gray-50 border-t border-gray-100 text-center">
                <p className="text-xs text-gray-400 flex items-center justify-center gap-1">
                    <span className="w-1.5 h-1.5 bg-green-500 rounded-full"></span>
                    System Active • Monitoring {radarEvents.length} Alerts
                </p>
            </div>
        </div>
    );
}
