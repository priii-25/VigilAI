import Head from 'next/head';
import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';
import { useAuthStore } from '@/store/authStore';
import Sidebar from '@/components/layout/Sidebar';
import Header from '@/components/layout/Header';
import DashboardStats from '@/components/dashboard/DashboardStats';
import RecentActivity from '@/components/dashboard/RecentActivity';

export default function Home() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (mounted && !isAuthenticated()) {
      router.push('/login');
    }
  }, [mounted, isAuthenticated, router]);

  if (!mounted || !isAuthenticated()) {
    return null;
  }

  return (
    <>
      <Head>
        <title>VigilAI - Competitive Intelligence Platform</title>
        <meta name="description" content="Automated competitive intelligence and AIOps platform" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>
      
      <div className="flex h-screen bg-gray-100">
        <Sidebar />
        
        <div className="flex-1 flex flex-col overflow-hidden">
          <Header />
          
          <main className="flex-1 overflow-y-auto p-6">
            <div className="max-w-7xl mx-auto">
              <h1 className="text-3xl font-bold text-gray-900 mb-6">
                Dashboard
              </h1>
              
              <DashboardStats />
              
              <div className="mt-8">
                <RecentActivity />
              </div>
            </div>
          </main>
        </div>
      </div>
    </>
  );
}
