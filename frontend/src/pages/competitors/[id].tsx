import { useState } from 'react';
import { useRouter } from 'next/router';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { competitorsAPI } from '@/lib/api';
import Head from 'next/head';
import Sidebar from '@/components/layout/Sidebar';
import Header from '@/components/layout/Header';
import { RefreshCw, ExternalLink, Globe, FileText, Briefcase, TrendingUp, AlertTriangle, ArrowLeft } from 'lucide-react';
import { toast } from 'react-hot-toast';
import StrategyDriftChart from '@/components/StrategyDriftChart';


interface CompetitorUpdate {
    id: number;
    competitor_id: number;
    update_type: 'pricing' | 'hiring' | 'content' | string;
    category: string;
    title: string;
    summary: string;
    impact_score: number;
    source_url: string;
    created_at: string;
}

interface Competitor {
    id: number;
    name: string;
    domain: string;
    description: string;
    industry: string;
    is_active: boolean;
    pricing_url: string;
    careers_url: string;
    blog_url: string;
    extra_data: Record<string, any>;
    created_at: string;
    updated_at: string;
}

export default function CompetitorDetail() {
    const router = useRouter();
    const { id } = router.query;
    const queryClient = useQueryClient();

    const { data: competitor, isLoading } = useQuery<Competitor>({
        queryKey: ['competitor', id],
        queryFn: async () => {
            if (!id) return null;
            const response = await competitorsAPI.get(Number(id));
            return response.data;
        },
        enabled: !!id,
    });

    const { data: updates, isLoading: isLoadingUpdates } = useQuery<CompetitorUpdate[]>({
        queryKey: ['competitor-updates', id],
        queryFn: async () => {
            if (!id) return [];
            const response = await competitorsAPI.getUpdates(Number(id));
            return response.data;
        },
        enabled: !!id,
    });

    const scrapeMutation = useMutation({
        mutationFn: (id: number) => competitorsAPI.triggerScrape(id),
        onSuccess: () => {
            toast.success('Analysis triggered successfully');
            queryClient.invalidateQueries({ queryKey: ['competitor', id] });
            queryClient.invalidateQueries({ queryKey: ['competitor-updates', id] });
        },
        onError: () => {
            toast.error('Failed to trigger analysis');
        }
    });

    if (isLoading || !competitor) {
        // We will replace this with a Skeleton later
        return (
            <div className="flex h-screen bg-gray-100">
                <Sidebar />
                <div className="flex-1 flex flex-col">
                    <Header />
                    <div className="flex-1 flex items-center justify-center">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
                    </div>
                </div>
            </div>
        );
    }

    // Helper to determine badge color based on update type
    const getUpdateBadgeColor = (type: string) => {
        switch (type) {
            case 'pricing': return 'bg-yellow-100 text-yellow-800';
            case 'hiring': return 'bg-blue-100 text-blue-800';
            case 'content': return 'bg-purple-100 text-purple-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    // Helper to ensure URL has protocol
    const ensureProtocol = (url: string) => {
        if (!url) return '#';
        if (url.startsWith('http://') || url.startsWith('https://')) return url;
        return `https://${url}`;
    };

    return (
        <>
            <Head>
                <title>{competitor.name} - VigilAI</title>
            </Head>

            <div className="flex h-screen bg-gray-100">
                <Sidebar />

                <div className="flex-1 flex flex-col overflow-hidden">
                    <Header />

                    <main className="flex-1 overflow-y-auto bg-gray-50">
                        {/* Hero / Header */}
                        <div className="bg-white border-b border-gray-200 px-8 py-8">
                            <div className="max-w-6xl mx-auto">
                                <button
                                    onClick={() => router.back()}
                                    className="flex items-center gap-2 text-gray-500 hover:text-gray-900 transition-colors mb-6 text-sm"
                                >
                                    <ArrowLeft size={16} />
                                    Back to Dashboard
                                </button>

                                <div className="flex items-start justify-between">
                                    <div className="flex items-center gap-6">
                                        <div className="w-20 h-20 bg-gray-100 rounded-xl flex items-center justify-center text-3xl font-bold text-gray-400">
                                            {competitor.name.charAt(0)}
                                        </div>
                                        <div>
                                            <h1 className="text-3xl font-bold text-gray-900 mb-2">{competitor.name}</h1>
                                            <div className="flex items-center gap-4 text-sm text-gray-500">
                                                <a href={ensureProtocol(competitor.domain)} target="_blank" className="flex items-center gap-1 hover:text-primary-600">
                                                    <Globe size={14} />
                                                    {competitor.domain}
                                                </a>
                                                <span className="w-1 h-1 bg-gray-300 rounded-full"></span>
                                                <span>{competitor.industry || 'Unknown Industry'}</span>
                                            </div>
                                        </div>
                                    </div>

                                    <button
                                        onClick={() => scrapeMutation.mutate(Number(id))}
                                        disabled={scrapeMutation.isPending}
                                        className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-all shadow-sm"
                                    >
                                        <RefreshCw size={18} className={scrapeMutation.isPending ? 'animate-spin' : ''} />
                                        {scrapeMutation.isPending ? 'Analyzing...' : 'Update Intelligence'}
                                    </button>
                                </div>
                            </div>
                        </div>

                        <div className="max-w-6xl mx-auto px-8 py-8">

                            {/* Quick Stats Grid */}
                            <div className="grid grid-cols-4 gap-6 mb-8">
                                <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                                    <p className="text-gray-500 text-sm font-medium mb-2">Market Sentiment</p>
                                    <div className="flex items-end gap-2">
                                        <span className="text-2xl font-bold text-green-600">Positive</span>
                                        <span className="text-sm text-gray-400 mb-1">Based on G2</span>
                                    </div>
                                </div>
                                <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                                    <p className="text-gray-500 text-sm font-medium mb-2">Price Change</p>
                                    <div className="flex items-end gap-2">
                                        <span className="text-2xl font-bold text-gray-900">Stable</span>
                                        <span className="text-sm text-gray-400 mb-1">Last 30 days</span>
                                    </div>
                                </div>
                                <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                                    <p className="text-gray-500 text-sm font-medium mb-2">Hiring Velocity</p>
                                    <div className="flex items-end gap-2">
                                        <span className="text-2xl font-bold text-orange-500">Medium</span>
                                        <span className="text-sm text-gray-400 mb-1">Active roles</span>
                                    </div>
                                </div>
                                <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                                    <p className="text-gray-500 text-sm font-medium mb-2">Recent Updates</p>
                                    <div className="flex items-end gap-2">
                                        <span className="text-2xl font-bold text-primary-600">{updates?.length || 0}</span>
                                        <span className="text-sm text-gray-400 mb-1">Detected events</span>
                                    </div>
                                </div>
                            </div>

                            <div className="grid grid-cols-3 gap-8">
                                {/* Main Content Column */}
                                <div className="col-span-2 space-y-8">

                                    {/* Latest Intelligence Feed */}
                                    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
                                        <h2 className="text-lg font-bold text-gray-900 mb-6 flex items-center gap-2">
                                            <AlertTriangle className="text-primary-600" size={20} />
                                            Latest Intelligence Detected
                                        </h2>

                                        <div className="space-y-6">
                                            {isLoadingUpdates ? (
                                                <div className="text-center py-8 text-gray-500">Loading intelligence...</div>
                                            ) : updates?.length === 0 ? (
                                                <div className="text-center py-8 text-gray-500">
                                                    No recent updates detected. Click "Update Intelligence" to scan for new data.
                                                </div>
                                            ) : (
                                                updates?.map((update: CompetitorUpdate, idx: number) => (
                                                    <div key={idx} className="flex gap-4">
                                                        <div className="flex flex-col items-center">
                                                            <div className="w-2 h-2 bg-primary-600 rounded-full"></div>
                                                            {idx !== updates.length - 1 && <div className="w-0.5 h-full bg-gray-100 my-1"></div>}
                                                        </div>
                                                        <div className="pb-6">
                                                            <span className="text-xs font-medium text-gray-500">
                                                                {new Date(update.created_at).toLocaleDateString()}
                                                            </span>
                                                            <h4 className="font-bold text-gray-900 mt-1">{update.title}</h4>
                                                            <p className="text-gray-600 text-sm mt-1">{update.summary}</p>
                                                            <span className={`inline-block mt-2 px-2 py-1 text-xs rounded ${getUpdateBadgeColor(update.update_type)}`}>
                                                                {update.category || update.update_type}
                                                            </span>
                                                        </div>
                                                    </div>
                                                ))
                                            )}
                                        </div>
                                    </div>

                                </div>

                                {/* Sidebar Info Column */}
                                <div className="space-y-6">
                                    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
                                        <h3 className="font-bold text-gray-900 mb-4">Monitored Assets</h3>
                                        <div className="space-y-3">
                                            <a href={ensureProtocol(competitor.pricing_url)} target="_blank" className="flex items-center justify-between p-3 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors group">
                                                <div className="flex items-center gap-3">
                                                    <div className="p-2 bg-white rounded border border-gray-200 text-green-600">
                                                        <TrendingUp size={16} />
                                                    </div>
                                                    <div>
                                                        <p className="text-sm font-medium text-gray-900">Pricing Page</p>
                                                        <p className="text-xs text-gray-500">Active</p>
                                                    </div>
                                                </div>
                                                <ExternalLink size={14} className="text-gray-400 group-hover:text-primary-600" />
                                            </a>

                                            <a href={ensureProtocol(competitor.careers_url)} target="_blank" className="flex items-center justify-between p-3 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors group">
                                                <div className="flex items-center gap-3">
                                                    <div className="p-2 bg-white rounded border border-gray-200 text-blue-600">
                                                        <Briefcase size={16} />
                                                    </div>
                                                    <div>
                                                        <p className="text-sm font-medium text-gray-900">Careers Page</p>
                                                        <p className="text-xs text-gray-500">Active</p>
                                                    </div>
                                                </div>
                                                <ExternalLink size={14} className="text-gray-400 group-hover:text-primary-600" />
                                            </a>

                                            <a href={ensureProtocol(competitor.blog_url)} target="_blank" className="flex items-center justify-between p-3 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors group">
                                                <div className="flex items-center gap-3">
                                                    <div className="p-2 bg-white rounded border border-gray-200 text-purple-600">
                                                        <FileText size={16} />
                                                    </div>
                                                    <div>
                                                        <p className="text-sm font-medium text-gray-900">Blog / News</p>
                                                        <p className="text-xs text-gray-500">Active</p>
                                                    </div>
                                                </div>
                                                <ExternalLink size={14} className="text-gray-400 group-hover:text-primary-600" />
                                            </a>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        {/* Strategy Drift Analysis */}
                        <div className="mt-8">
                            <StrategyDriftChart competitorId={Number(id)} />
                        </div>
                    </main>
                </div>
            </div>
        </>
    );
}
