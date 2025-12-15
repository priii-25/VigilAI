import Head from 'next/head';
import Sidebar from '@/components/layout/Sidebar';
import Header from '@/components/layout/Header';
import SimulatorConsole from '@/components/SimulatorConsole';

export default function SimulationPage() {
    return (
        <>
            <Head>
                <title>War Room Simulator - VigilAI</title>
            </Head>

            <div className="flex h-screen bg-gray-100">
                <Sidebar />

                <div className="flex-1 flex flex-col overflow-hidden">
                    <Header />

                    <main className="flex-1 overflow-y-auto p-6 bg-gray-50">
                        <div className="max-w-7xl mx-auto">
                            <div className="mb-6">
                                <h1 className="text-3xl font-bold text-gray-900">Competitive War Room</h1>
                                <p className="text-gray-600">Simulate competitive moves and predict market outcomes using AI.</p>
                            </div>

                            <SimulatorConsole />

                        </div>
                    </main>
                </div>
            </div>
        </>
    );
}
