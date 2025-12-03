import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { battlecardsAPI } from '@/lib/api';
import Head from 'next/head';
import { useRouter } from 'next/router';
import Sidebar from '@/components/layout/Sidebar';
import Header from '@/components/layout/Header';
import { Plus, Edit, Trash2, Eye, Copy, Download, Search } from 'lucide-react';

export default function Battlecards() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState('');
  const [filterCategory, setFilterCategory] = useState('all');
  const [showCreateModal, setShowCreateModal] = useState(false);

  const { data: battlecards, isLoading } = useQuery({
    queryKey: ['battlecards'],
    queryFn: async () => {
      const response = await battlecardsAPI.list();
      return response.data;
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => battlecardsAPI.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['battlecards'] });
    },
  });

  const duplicateMutation = useMutation({
    mutationFn: (id: number) => battlecardsAPI.duplicate(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['battlecards'] });
      alert('Battlecard duplicated successfully!');
    },
  });

  const handleDelete = (id: number, title: string) => {
    if (confirm(`Delete battlecard "${title}"? This cannot be undone.`)) {
      deleteMutation.mutate(id);
    }
  };

  const filteredBattlecards = battlecards?.filter((card: any) => {
    const matchesSearch = card.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         card.competitor_name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter = filterCategory === 'all' || card.category === filterCategory;
    return matchesSearch && matchesFilter;
  }) || [];

  return (
    <>
      <Head>
        <title>Battlecards - VigilAI</title>
      </Head>

      <div className="flex h-screen bg-gray-100">
        <Sidebar />
        
        <div className="flex-1 flex flex-col overflow-hidden">
          <Header />
          
          <main className="flex-1 overflow-y-auto p-6">
            <div className="max-w-7xl mx-auto">
              {/* Header */}
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900">Battlecards</h1>
                  <p className="text-gray-600 mt-1">Competitive intelligence and objection handling</p>
                </div>
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="flex items-center gap-2 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700"
                >
                  <Plus size={20} />
                  Create Battlecard
                </button>
              </div>

              {/* Filters */}
              <div className="card mb-6">
                <div className="flex gap-4 flex-wrap">
                  <div className="flex-1 min-w-[300px]">
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
                      <input
                        type="text"
                        placeholder="Search battlecards..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                      />
                    </div>
                  </div>
                  <select
                    value={filterCategory}
                    onChange={(e) => setFilterCategory(e.target.value)}
                    className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  >
                    <option value="all">All Categories</option>
                    <option value="pricing">Pricing</option>
                    <option value="features">Features</option>
                    <option value="security">Security</option>
                    <option value="performance">Performance</option>
                    <option value="support">Support</option>
                  </select>
                </div>
              </div>

              {/* Battlecards Grid */}
              {isLoading ? (
                <div className="text-center py-12">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
                  <p className="text-gray-600 mt-4">Loading battlecards...</p>
                </div>
              ) : filteredBattlecards.length > 0 ? (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {filteredBattlecards.map((card: any) => (
                    <div key={card.id} className="card hover:shadow-lg transition-shadow">
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex-1">
                          <h3 className="text-xl font-bold text-gray-900">{card.title}</h3>
                          <p className="text-sm text-gray-600 mt-1">vs {card.competitor_name}</p>
                        </div>
                        <span className="px-3 py-1 bg-primary-100 text-primary-800 rounded-full text-sm font-medium">
                          {card.category}
                        </span>
                      </div>

                      {/* Kill Points Preview */}
                      {card.kill_points && card.kill_points.length > 0 && (
                        <div className="mb-4">
                          <h4 className="text-sm font-semibold text-gray-700 mb-2">💪 Kill Points:</h4>
                          <ul className="space-y-1">
                            {card.kill_points.slice(0, 3).map((point: string, idx: number) => (
                              <li key={idx} className="text-sm text-gray-600 flex items-start gap-2">
                                <span className="text-green-600 mt-0.5">✓</span>
                                <span className="line-clamp-1">{point}</span>
                              </li>
                            ))}
                            {card.kill_points.length > 3 && (
                              <li className="text-sm text-primary-600">
                                +{card.kill_points.length - 3} more...
                              </li>
                            )}
                          </ul>
                        </div>
                      )}

                      {/* Objection Handling Preview */}
                      {card.objection_handling && Object.keys(card.objection_handling).length > 0 && (
                        <div className="mb-4">
                          <h4 className="text-sm font-semibold text-gray-700 mb-2">🛡️ Objections Handled:</h4>
                          <div className="flex flex-wrap gap-2">
                            {Object.keys(card.objection_handling).slice(0, 3).map((objection: string) => (
                              <span key={objection} className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                                {objection}
                              </span>
                            ))}
                            {Object.keys(card.objection_handling).length > 3 && (
                              <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                                +{Object.keys(card.objection_handling).length - 3} more
                              </span>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Metadata */}
                      <div className="flex items-center gap-4 text-xs text-gray-500 mb-4">
                        <span>Updated {new Date(card.updated_at).toLocaleDateString()}</span>
                        {card.auto_generated && (
                          <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded">AI Generated</span>
                        )}
                      </div>

                      {/* Actions */}
                      <div className="flex gap-2 pt-4 border-t border-gray-200">
                        <button
                          onClick={() => router.push(`/battlecards/${card.id}`)}
                          className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-primary-50 text-primary-600 rounded hover:bg-primary-100 text-sm"
                        >
                          <Eye size={16} />
                          View Full
                        </button>
                        <button
                          onClick={() => router.push(`/battlecards/${card.id}/edit`)}
                          className="flex items-center gap-2 px-3 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 text-sm"
                        >
                          <Edit size={16} />
                          Edit
                        </button>
                        <button
                          onClick={() => duplicateMutation.mutate(card.id)}
                          className="px-3 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                          title="Duplicate"
                        >
                          <Copy size={16} />
                        </button>
                        <button
                          onClick={() => handleDelete(card.id, card.title)}
                          className="px-3 py-2 bg-red-50 text-red-600 rounded hover:bg-red-100"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 card">
                  <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Plus size={32} className="text-gray-400" />
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    {searchQuery || filterCategory !== 'all' ? 'No battlecards found' : 'No battlecards yet'}
                  </h3>
                  <p className="text-gray-600 mb-4">
                    {searchQuery || filterCategory !== 'all'
                      ? 'Try adjusting your search or filters'
                      : 'Create your first battlecard to start tracking competitive intelligence'}
                  </p>
                  {!searchQuery && filterCategory === 'all' && (
                    <button
                      onClick={() => setShowCreateModal(true)}
                      className="inline-flex items-center gap-2 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700"
                    >
                      <Plus size={20} />
                      Create Your First Battlecard
                    </button>
                  )}
                </div>
              )}
            </div>
          </main>
        </div>
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <BattlecardCreateModal onClose={() => setShowCreateModal(false)} />
      )}
    </>
  );
}

function BattlecardCreateModal({ onClose }: any) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState({
    title: '',
    competitor_id: '',
    category: 'features',
    kill_points: [''],
    objections: [{ objection: '', response: '' }],
  });

  const { data: competitors } = useQuery({
    queryKey: ['competitors'],
    queryFn: async () => {
      const response = await fetch('/api/competitors');
      return response.json();
    },
  });

  const createMutation = useMutation({
    mutationFn: (data: any) => battlecardsAPI.create(data),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['battlecards'] });
      router.push(`/battlecards/${response.data.id}/edit`);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Transform objections to object format
    const objection_handling = formData.objections
      .filter(o => o.objection && o.response)
      .reduce((acc, o) => ({ ...acc, [o.objection]: o.response }), {});

    createMutation.mutate({
      ...formData,
      kill_points: formData.kill_points.filter(p => p.trim()),
      objection_handling,
    });
  };

  const addKillPoint = () => {
    setFormData({ ...formData, kill_points: [...formData.kill_points, ''] });
  };

  const addObjection = () => {
    setFormData({ ...formData, objections: [...formData.objections, { objection: '', response: '' }] });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg p-6 max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Create Battlecard</h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Title *</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              placeholder="e.g., Feature Comparison: AI Capabilities"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Competitor *</label>
              <select
                value={formData.competitor_id}
                onChange={(e) => setFormData({ ...formData, competitor_id: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                required
              >
                <option value="">Select competitor...</option>
                {competitors?.map((comp: any) => (
                  <option key={comp.id} value={comp.id}>{comp.name}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Category *</label>
              <select
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              >
                <option value="pricing">Pricing</option>
                <option value="features">Features</option>
                <option value="security">Security</option>
                <option value="performance">Performance</option>
                <option value="support">Support</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">💪 Kill Points</label>
            <div className="space-y-2">
              {formData.kill_points.map((point, idx) => (
                <input
                  key={idx}
                  type="text"
                  value={point}
                  onChange={(e) => {
                    const newPoints = [...formData.kill_points];
                    newPoints[idx] = e.target.value;
                    setFormData({ ...formData, kill_points: newPoints });
                  }}
                  placeholder="Why we win..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                />
              ))}
            </div>
            <button
              type="button"
              onClick={addKillPoint}
              className="mt-2 text-sm text-primary-600 hover:text-primary-700"
            >
              + Add Kill Point
            </button>
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
            >
              {createMutation.isPending ? 'Creating...' : 'Create & Edit Details'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
