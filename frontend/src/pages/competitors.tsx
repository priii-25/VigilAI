import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { competitorsAPI } from '@/lib/api';
import Head from 'next/head';
import { useRouter } from 'next/router';
import Sidebar from '@/components/layout/Sidebar';
import Header from '@/components/layout/Header';
import { Plus, Trash2, Edit, RefreshCw, ExternalLink, TrendingUp, Eye } from 'lucide-react';

export default function Competitors() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingCompetitor, setEditingCompetitor] = useState(null);

  const { data: competitors, isLoading } = useQuery({
    queryKey: ['competitors'],
    queryFn: async () => {
      const response = await competitorsAPI.list();
      return response.data;
    },
  });

  const scrapeCompetitorMutation = useMutation({
    mutationFn: (competitorId: number) => competitorsAPI.triggerScrape(competitorId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['competitors'] });
      alert('Scraping initiated successfully!');
    },
  });

  const deleteCompetitorMutation = useMutation({
    mutationFn: (competitorId: number) => competitorsAPI.delete(competitorId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['competitors'] });
    },
  });

  const handleScrape = (competitorId: number) => {
    if (confirm('Start scraping this competitor?')) {
      scrapeCompetitorMutation.mutate(competitorId);
    }
  };

  const handleDelete = (competitorId: number, name: string) => {
    if (confirm(`Delete ${name}? This cannot be undone.`)) {
      deleteCompetitorMutation.mutate(competitorId);
    }
  };

  return (
    <>
      <Head>
        <title>Competitors - VigilAI</title>
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
                  <h1 className="text-3xl font-bold text-gray-900">Competitors</h1>
                  <p className="text-gray-600 mt-1">Monitor and analyze your competitors</p>
                </div>
                <button
                  onClick={() => setShowAddModal(true)}
                  className="flex items-center gap-2 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition-colors"
                >
                  <Plus size={20} />
                  Add Competitor
                </button>
              </div>

              {/* Competitors Grid */}
              {isLoading ? (
                <div className="text-center py-12">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
                  <p className="text-gray-600 mt-4">Loading competitors...</p>
                </div>
              ) : competitors && competitors.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {competitors.map((competitor: any) => (
                    <div key={competitor.id} className="card">
                      <div className="flex items-start justify-between mb-4">
                        <div>
                          <h3 className="text-xl font-bold text-gray-900">{competitor.name}</h3>
                          <a
                            href={`https://${competitor.domain}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-primary-600 hover:underline flex items-center gap-1 mt-1"
                          >
                            {competitor.domain}
                            <ExternalLink size={14} />
                          </a>
                        </div>
                        <span className={`px-2 py-1 rounded text-xs font-medium ${competitor.is_active
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                          }`}>
                          {competitor.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </div>

                      {competitor.description && (
                        <p className="text-gray-600 text-sm mb-4 line-clamp-2">
                          {competitor.description}
                        </p>
                      )}

                      {competitor.industry && (
                        <div className="mb-4">
                          <span className="inline-block bg-purple-100 text-purple-800 text-xs px-2 py-1 rounded">
                            {competitor.industry}
                          </span>
                        </div>
                      )}

                      {/* Monitoring URLs */}
                      <div className="space-y-1 mb-4 text-xs text-gray-500">
                        {competitor.pricing_url && (
                          <div className="flex items-center gap-1">
                            <TrendingUp size={12} />
                            <span>Pricing monitored</span>
                          </div>
                        )}
                        {competitor.careers_url && (
                          <div className="flex items-center gap-1">
                            <TrendingUp size={12} />
                            <span>Hiring monitored</span>
                          </div>
                        )}
                        {competitor.blog_url && (
                          <div className="flex items-center gap-1">
                            <TrendingUp size={12} />
                            <span>Content monitored</span>
                          </div>
                        )}
                      </div>

                      {/* Actions */}
                      <div className="flex gap-2 pt-4 border-t border-gray-200">
                        <button
                          onClick={() => handleScrape(competitor.id)}
                          className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-blue-50 text-blue-600 rounded hover:bg-blue-100 transition-colors text-sm"
                        >
                          <RefreshCw size={16} />
                          Scrape Now
                        </button>
                        <button
                          onClick={() => router.push(`/competitors/${competitor.id}`)}
                          className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors text-sm"
                        >
                          <Eye size={16} />
                          View Dashboard
                        </button>
                        <button
                          onClick={() => handleDelete(competitor.id, competitor.name)}
                          className="px-3 py-2 bg-red-50 text-red-600 rounded hover:bg-red-100 transition-colors"
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
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No competitors yet</h3>
                  <p className="text-gray-600 mb-4">Start monitoring your competitors by adding them here</p>
                  <button
                    onClick={() => setShowAddModal(true)}
                    className="inline-flex items-center gap-2 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700"
                  >
                    <Plus size={20} />
                    Add Your First Competitor
                  </button>
                </div>
              )}
            </div>
          </main>
        </div>
      </div>

      {/* Add/Edit Modal */}
      {showAddModal && (
        <CompetitorModal
          onClose={() => setShowAddModal(false)}
          competitor={editingCompetitor}
        />
      )}
    </>
  );
}

function CompetitorModal({ onClose, competitor }: any) {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState({
    name: competitor?.name || '',
    domain: competitor?.domain || '',
    description: competitor?.description || '',
    industry: competitor?.industry || '',
    pricing_url: competitor?.pricing_url || '',
    careers_url: competitor?.careers_url || '',
    blog_url: competitor?.blog_url || '',
  });

  const createMutation = useMutation({
    mutationFn: (data: any) => competitorsAPI.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['competitors'] });
      onClose();
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate(formData);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          {competitor ? 'Edit Competitor' : 'Add New Competitor'}
        </h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Company Name *
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Domain *
            </label>
            <input
              type="text"
              value={formData.domain}
              onChange={(e) => setFormData({ ...formData, domain: e.target.value })}
              placeholder="example.com"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Industry
            </label>
            <input
              type="text"
              value={formData.industry}
              onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
              placeholder="SaaS, E-commerce, etc."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>

          <div className="pt-4 border-t border-gray-200">
            <h3 className="text-lg font-medium text-gray-900 mb-3">Monitoring URLs</h3>

            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Pricing Page URL
                </label>
                <input
                  type="url"
                  value={formData.pricing_url}
                  onChange={(e) => setFormData({ ...formData, pricing_url: e.target.value })}
                  placeholder="https://example.com/pricing"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Careers Page URL
                </label>
                <input
                  type="url"
                  value={formData.careers_url}
                  onChange={(e) => setFormData({ ...formData, careers_url: e.target.value })}
                  placeholder="https://example.com/careers"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Blog/News URL
                </label>
                <input
                  type="url"
                  value={formData.blog_url}
                  onChange={(e) => setFormData({ ...formData, blog_url: e.target.value })}
                  placeholder="https://example.com/blog"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>
            </div>
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
              {createMutation.isPending ? 'Saving...' : competitor ? 'Update' : 'Add Competitor'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
