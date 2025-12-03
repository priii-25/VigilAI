import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { logsAPI } from '@/lib/api';
import Head from 'next/head';
import Sidebar from '@/components/layout/Sidebar';
import Header from '@/components/layout/Header';
import { Search, AlertTriangle, Info, XCircle, CheckCircle, MessageSquare, Send, RefreshCw } from 'lucide-react';

export default function LogAnalysis() {
  const [searchQuery, setSearchQuery] = useState('');
  const [filterLevel, setFilterLevel] = useState('all');
  const [filterComponent, setFilterComponent] = useState('all');
  const [selectedAnomaly, setSelectedAnomaly] = useState<any>(null);
  const [chatMessages, setChatMessages] = useState<any[]>([]);
  const [chatInput, setChatInput] = useState('');

  const { data: logsData, isLoading, refetch } = useQuery({
    queryKey: ['logs-analysis'],
    queryFn: async () => {
      const response = await logsAPI.getAnalysis();
      return response.data;
    },
    refetchInterval: 60000, // Refresh every minute
  });

  const chatMutation = useMutation({
    mutationFn: async (message: string) => {
      const response = await logsAPI.chat({
        message,
        anomaly_id: selectedAnomaly?.anomaly_id,
      });
      return response.data;
    },
    onSuccess: (data) => {
      setChatMessages([...chatMessages, 
        { role: 'user', content: chatInput },
        { role: 'assistant', content: data.response }
      ]);
      setChatInput('');
    },
  });

  const handleChat = (e: React.FormEvent) => {
    e.preventDefault();
    if (chatInput.trim()) {
      chatMutation.mutate(chatInput);
    }
  };

  const anomalies = logsData?.anomalies || [];
  const logSummary = logsData?.log_summary || {};

  const filteredAnomalies = anomalies.filter((anomaly: any) => {
    const matchesSearch = anomaly.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         anomaly.affected_component.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesLevel = filterLevel === 'all' || anomaly.severity === filterLevel;
    const matchesComponent = filterComponent === 'all' || anomaly.affected_component === filterComponent;
    return matchesSearch && matchesLevel && matchesComponent;
  });

  const uniqueComponents = [...new Set(anomalies.map((a: any) => a.affected_component))];

  return (
    <>
      <Head>
        <title>Log Analysis - VigilAI</title>
      </Head>

      <div className="flex h-screen bg-gray-100">
        <Sidebar />
        
        <div className="flex-1 flex flex-col overflow-hidden">
          <Header />
          
          <main className="flex-1 overflow-hidden flex">
            {/* Left Panel - Anomalies List */}
            <div className="w-2/3 border-r border-gray-200 flex flex-col bg-white">
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h1 className="text-2xl font-bold text-gray-900">Log Analysis</h1>
                    <p className="text-sm text-gray-600 mt-1">AI-powered anomaly detection and root cause analysis</p>
                  </div>
                  <button
                    onClick={() => refetch()}
                    className="flex items-center gap-2 px-3 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                  >
                    <RefreshCw size={16} />
                    Refresh
                  </button>
                </div>

                {/* Summary Stats */}
                <div className="grid grid-cols-4 gap-4 mb-4">
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <p className="text-xs text-gray-600">Total Logs</p>
                    <p className="text-xl font-bold text-gray-900">{logsData?.total_logs || 0}</p>
                  </div>
                  <div className="p-3 bg-red-50 rounded-lg">
                    <p className="text-xs text-gray-600">Errors</p>
                    <p className="text-xl font-bold text-red-600">{logSummary.errors || 0}</p>
                  </div>
                  <div className="p-3 bg-yellow-50 rounded-lg">
                    <p className="text-xs text-gray-600">Warnings</p>
                    <p className="text-xl font-bold text-yellow-600">{logSummary.warnings || 0}</p>
                  </div>
                  <div className="p-3 bg-orange-50 rounded-lg">
                    <p className="text-xs text-gray-600">Anomalies</p>
                    <p className="text-xl font-bold text-orange-600">{logsData?.anomalies_detected || 0}</p>
                  </div>
                </div>

                {/* Filters */}
                <div className="flex gap-3">
                  <div className="flex-1 relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
                    <input
                      type="text"
                      placeholder="Search anomalies..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 text-sm"
                    />
                  </div>
                  <select
                    value={filterLevel}
                    onChange={(e) => setFilterLevel(e.target.value)}
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 text-sm"
                  >
                    <option value="all">All Severities</option>
                    <option value="critical">Critical</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                  </select>
                  <select
                    value={filterComponent}
                    onChange={(e) => setFilterComponent(e.target.value)}
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 text-sm"
                  >
                    <option value="all">All Components</option>
                    {(uniqueComponents as string[]).map((comp: string) => (
                      <option key={comp} value={comp}>{comp}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Anomalies List */}
              <div className="flex-1 overflow-y-auto p-6">
                {isLoading ? (
                  <div className="text-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
                    <p className="text-gray-600 mt-4">Analyzing logs...</p>
                  </div>
                ) : filteredAnomalies.length > 0 ? (
                  <div className="space-y-4">
                    {filteredAnomalies.map((anomaly: any) => (
                      <div
                        key={anomaly.anomaly_id}
                        onClick={() => {
                          setSelectedAnomaly(anomaly);
                          setChatMessages([{
                            role: 'assistant',
                            content: `I've detected a ${anomaly.severity} severity ${anomaly.anomaly_type} in ${anomaly.affected_component}. Ask me anything about this anomaly.`
                          }]);
                        }}
                        className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                          selectedAnomaly?.anomaly_id === anomaly.anomaly_id
                            ? 'border-primary-500 bg-primary-50'
                            : 'border-gray-200 hover:border-gray-300 bg-white'
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          <div className={`p-2 rounded-lg ${getSeverityBg(anomaly.severity)}`}>
                            {getSeverityIcon(anomaly.severity)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <span className={`px-2 py-0.5 rounded text-xs font-medium ${getSeverityBadge(anomaly.severity)}`}>
                                {anomaly.severity}
                              </span>
                              <span className="text-xs text-gray-500">{anomaly.affected_component}</span>
                              <span className="text-xs text-gray-400">
                                {new Date(anomaly.detected_at).toLocaleTimeString()}
                              </span>
                            </div>
                            <p className="text-sm font-medium text-gray-900 mb-1">{anomaly.description}</p>
                            {anomaly.rca?.root_cause && (
                              <p className="text-xs text-gray-600 line-clamp-2">
                                💡 {anomaly.rca.root_cause}
                              </p>
                            )}
                            <div className="flex items-center gap-2 mt-2">
                              <div className="flex items-center gap-1 text-xs text-gray-500">
                                <span className="px-2 py-0.5 bg-gray-100 rounded">
                                  {anomaly.log_entries?.length || 0} logs
                                </span>
                                <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded">
                                  {(anomaly.confidence_score * 100).toFixed(0)}% confidence
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <CheckCircle className="mx-auto text-green-500 mb-4" size={48} />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">All Clear!</h3>
                    <p className="text-gray-600">No anomalies detected in recent logs</p>
                  </div>
                )}
              </div>
            </div>

            {/* Right Panel - AI Chat for RCA */}
            <div className="w-1/3 bg-gray-50 flex flex-col">
              <div className="p-4 border-b border-gray-200 bg-white">
                <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                  <MessageSquare size={20} />
                  AI Root Cause Analysis
                </h2>
                <p className="text-xs text-gray-600 mt-1">
                  {selectedAnomaly ? 'Ask questions about this anomaly' : 'Select an anomaly to start'}
                </p>
              </div>

              {selectedAnomaly ? (
                <>
                  {/* Chat Messages */}
                  <div className="flex-1 overflow-y-auto p-4 space-y-4">
                    {chatMessages.map((msg, idx) => (
                      <div
                        key={idx}
                        className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div
                          className={`max-w-[85%] p-3 rounded-lg ${
                            msg.role === 'user'
                              ? 'bg-primary-600 text-white'
                              : 'bg-white border border-gray-200 text-gray-900'
                          }`}
                        >
                          <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                        </div>
                      </div>
                    ))}
                    {chatMutation.isPending && (
                      <div className="flex justify-start">
                        <div className="bg-white border border-gray-200 p-3 rounded-lg">
                          <div className="flex gap-1">
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Suggested Questions */}
                  {chatMessages.length === 1 && (
                    <div className="px-4 pb-4">
                      <p className="text-xs text-gray-600 mb-2">Suggested questions:</p>
                      <div className="space-y-2">
                        {[
                          'What caused this issue?',
                          'How can I fix this?',
                          'Is this related to recent deployments?',
                          'What are the affected services?'
                        ].map((question) => (
                          <button
                            key={question}
                            onClick={() => {
                              setChatInput(question);
                              chatMutation.mutate(question);
                            }}
                            className="w-full text-left px-3 py-2 text-xs bg-white border border-gray-200 rounded-lg hover:bg-gray-50 text-gray-700"
                          >
                            {question}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Chat Input */}
                  <form onSubmit={handleChat} className="p-4 bg-white border-t border-gray-200">
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={chatInput}
                        onChange={(e) => setChatInput(e.target.value)}
                        placeholder="Ask about this anomaly..."
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 text-sm"
                        disabled={chatMutation.isPending}
                      />
                      <button
                        type="submit"
                        disabled={!chatInput.trim() || chatMutation.isPending}
                        className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <Send size={18} />
                      </button>
                    </div>
                  </form>
                </>
              ) : (
                <div className="flex-1 flex items-center justify-center p-4">
                  <div className="text-center">
                    <MessageSquare className="mx-auto text-gray-300 mb-4" size={48} />
                    <p className="text-gray-500">Select an anomaly to analyze</p>
                  </div>
                </div>
              )}
            </div>
          </main>
        </div>
      </div>
    </>
  );
}

function getSeverityIcon(severity: string) {
  switch (severity) {
    case 'critical':
      return <XCircle className="text-red-600" size={20} />;
    case 'high':
      return <AlertTriangle className="text-orange-600" size={20} />;
    case 'medium':
      return <AlertTriangle className="text-yellow-600" size={20} />;
    default:
      return <Info className="text-blue-600" size={20} />;
  }
}

function getSeverityBg(severity: string) {
  switch (severity) {
    case 'critical':
      return 'bg-red-100';
    case 'high':
      return 'bg-orange-100';
    case 'medium':
      return 'bg-yellow-100';
    default:
      return 'bg-blue-100';
  }
}

function getSeverityBadge(severity: string) {
  switch (severity) {
    case 'critical':
      return 'bg-red-100 text-red-800';
    case 'high':
      return 'bg-orange-100 text-orange-800';
    case 'medium':
      return 'bg-yellow-100 text-yellow-800';
    default:
      return 'bg-blue-100 text-blue-800';
  }
}
