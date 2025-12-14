import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { battlecardsAPI } from '@/lib/api';
import Head from 'next/head';
import Sidebar from '@/components/layout/Sidebar';
import Header from '@/components/layout/Header';
import { Edit, Save, ArrowLeft, Trash2, Printer, Share2 } from 'lucide-react';
import { toast } from 'react-hot-toast';

interface Battlecard {
    id: number;
    competitor_id: number;
    competitor_name?: string;
    title: string;
    category: string;
    overview: string;
    kill_points: string[];
    objection_handling: Record<string, string>;
    strengths: string[];
    weaknesses: string[];
    updated_at: string;
    notion_page_id?: string;
}

export default function BattlecardDetail() {
    const router = useRouter();
    const { id } = router.query;
    const queryClient = useQueryClient();
    const [isEditing, setIsEditing] = useState(false);
    const [formData, setFormData] = useState<Battlecard | null>(null);

    const { data: battlecard, isLoading } = useQuery({
        queryKey: ['battlecard', id],
        queryFn: async () => {
            if (!id) return null;
            const response = await battlecardsAPI.get(Number(id));
            return response.data;
        },
        enabled: !!id,
    });

    useEffect(() => {
        if (battlecard) {
            setFormData({
                ...battlecard,
                kill_points: battlecard.kill_points || [],
                objection_handling: battlecard.objection_handling || {},
            });
        }
    }, [battlecard]);

    const updateMutation = useMutation({
        mutationFn: (data: Battlecard) => battlecardsAPI.update(Number(id), data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['battlecard', id] });
            setIsEditing(false);
            toast.success('Battlecard updated successfully');
        },
        onError: () => {
            toast.error('Failed to update battlecard');
        }
    });

    const handlePrint = () => {
        window.print();
    };

    const handleShare = async () => {
        const url = window.location.href;
        if (navigator.share) {
            try {
                await navigator.share({
                    title: `Battlecard: ${battlecard.title}`,
                    text: `Check out this battlecard for ${battlecard.title}`,
                    url,
                });
            } catch (err) {
                // User cancelled or share failed
                console.error('Share failed:', err);
            }
        } else {
            try {
                await navigator.clipboard.writeText(url);
                toast.success('Link copied to clipboard');
            } catch (err) {
                toast.error('Failed to copy link');
            }
        }
    };

    const handleSave = () => {
        if (formData) {
            updateMutation.mutate(formData);
        }
    };

    if (isLoading || !battlecard) {
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

    return (
        <>
            <Head>
                <title>{battlecard.title} - UseVigil</title>
            </Head>

            <div className="flex h-screen bg-gray-100">
                <Sidebar />

                <div className="flex-1 flex flex-col overflow-hidden">
                    <Header />

                    <main className="flex-1 overflow-y-auto p-6">
                        <div className="max-w-5xl mx-auto">
                            {/* Header Actions */}
                            <div className="flex items-center justify-between mb-8">
                                <button
                                    onClick={() => router.back()}
                                    className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
                                >
                                    <ArrowLeft size={20} />
                                    Back to Battlecards
                                </button>

                                <div className="flex items-center gap-3">
                                    <button
                                        onClick={handlePrint}
                                        className="p-2 text-gray-500 hover:bg-gray-200 rounded-lg"
                                        title="Print/Export"
                                    >
                                        <Printer size={20} />
                                    </button>
                                    <button
                                        onClick={handleShare}
                                        className="p-2 text-gray-500 hover:bg-gray-200 rounded-lg"
                                        title="Share"
                                    >
                                        <Share2 size={20} />
                                    </button>
                                    {isEditing ? (
                                        <button
                                            onClick={handleSave}
                                            disabled={updateMutation.isPending}
                                            className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                                        >
                                            <Save size={18} />
                                            Save Changes
                                        </button>
                                    ) : (
                                        <button
                                            onClick={() => setIsEditing(true)}
                                            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                                        >
                                            <Edit size={18} />
                                            Edit Content
                                        </button>
                                    )}
                                </div>
                            </div>

                            {/* Content Card */}
                            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                                {/* Banner/Header */}
                                <div className="bg-gradient-to-r from-gray-900 to-gray-800 px-8 py-8 text-white">
                                    <div className="flex items-start justify-between">
                                        <div>
                                            <div className="flex items-center gap-3 mb-3">
                                                <span className="px-3 py-1 bg-white/20 rounded-full text-xs font-medium backdrop-blur-sm">
                                                    {battlecard.category}
                                                </span>
                                                <span className="text-gray-400 text-sm">Last updated: {new Date(battlecard.updated_at).toLocaleDateString()}</span>
                                            </div>
                                            <h1 className="text-3xl font-bold mb-2">{battlecard.title}</h1>
                                            <p className="text-gray-300 text-lg">vs. {battlecard.competitor_name}</p>
                                        </div>
                                    </div>
                                </div>

                                <div className="p-8">
                                    {/* Kill Points Section */}
                                    <div className="mb-8">
                                        <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                                            <span className="text-2xl">💪</span> Warning / Kill Points
                                        </h2>
                                        {isEditing ? (
                                            <div className="space-y-3">
                                                {formData?.kill_points?.map((point: string, idx: number) => (
                                                    <div key={idx} className="flex gap-2">
                                                        <input
                                                            type="text"
                                                            value={point}
                                                            onChange={(e) => {
                                                                if (!formData) return;
                                                                const newPoints = [...formData.kill_points];
                                                                newPoints[idx] = e.target.value;
                                                                setFormData({ ...formData, kill_points: newPoints });
                                                            }}
                                                            className="flex-1 p-2 border border-gray-300 rounded-lg text-gray-900"
                                                        />
                                                        <button
                                                            onClick={() => {
                                                                if (!formData) return;
                                                                const newPoints = formData.kill_points.filter((_: any, i: number) => i !== idx);
                                                                setFormData({ ...formData, kill_points: newPoints });
                                                            }}
                                                            className="text-red-500 p-2"
                                                        >
                                                            <Trash2 size={16} />
                                                        </button>
                                                    </div>
                                                ))}
                                                <button
                                                    onClick={() => {
                                                        if (!formData) return;
                                                        setFormData({ ...formData, kill_points: [...formData.kill_points, ''] });
                                                    }}
                                                    className="text-primary-600 text-sm font-medium"
                                                >
                                                    + Add Point
                                                </button>
                                            </div>
                                        ) : (
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                {battlecard.kill_points?.map((point: string, idx: number) => (
                                                    <div key={idx} className="flex items-start gap-3 p-4 bg-green-50 rounded-lg border border-green-100">
                                                        <div className="mt-1 w-5 h-5 rounded-full bg-green-200 flex items-center justify-center flex-shrink-0">
                                                            <span className="text-green-700 text-xs">✓</span>
                                                        </div>
                                                        <p className="text-gray-800 leading-relaxed font-medium">{point}</p>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>

                                    <hr className="my-8 border-gray-100" />

                                    {/* Objection Handling Section */}
                                    <div>
                                        <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                                            <span className="text-2xl">🛡️</span> Objection Handling
                                        </h2>
                                        <div className="space-y-6">
                                            {Object.entries(formData?.objection_handling || {}).map(([objection, response]: [string, any], idx) => (
                                                <div key={idx} className="bg-gray-50 rounded-xl p-6 border border-gray-200">
                                                    {isEditing ? (
                                                        <div className="space-y-3">
                                                            <input
                                                                value={objection}
                                                                className="w-full p-2 font-bold mb-2 border border-gray-300 rounded text-gray-900"
                                                                placeholder="Objection..."
                                                                onChange={(e) => {
                                                                    if (!formData) return;
                                                                    const newObj = { ...formData.objection_handling };
                                                                    delete newObj[objection];
                                                                    newObj[e.target.value] = response;
                                                                    setFormData({ ...formData, objection_handling: newObj });
                                                                }}
                                                            />
                                                            <textarea
                                                                value={response}
                                                                className="w-full p-2 border border-gray-300 rounded text-gray-900"
                                                                rows={3}
                                                                onChange={(e) => {
                                                                    if (!formData) return;
                                                                    const newObj = { ...formData.objection_handling };
                                                                    newObj[objection] = e.target.value;
                                                                    setFormData({ ...formData, objection_handling: newObj });
                                                                }}
                                                            />
                                                        </div>
                                                    ) : (
                                                        <>
                                                            <h3 className="text-lg font-bold text-gray-900 mb-3 flex items-start gap-3">
                                                                <span className="text-red-500 mt-1">"</span>
                                                                {objection}
                                                                <span className="text-red-500 mt-1">"</span>
                                                            </h3>
                                                            <div className="pl-6 border-l-4 border-primary-500">
                                                                <p className="text-gray-700 leading-relaxed">{response}</p>
                                                            </div>
                                                        </>
                                                    )}
                                                </div>
                                            ))}
                                        </div>
                                    </div>

                                </div>
                            </div>
                        </div>
                    </main>
                </div>
            </div>
        </>
    );
}
