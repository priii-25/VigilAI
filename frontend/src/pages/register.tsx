import { useState } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import Link from 'next/link';
import { toast } from 'react-hot-toast';
import { authAPI } from '@/lib/api';
import { useAuthStore } from '@/store/authStore';
import { Sparkles, Mail, Lock, User, ArrowRight, CheckCircle } from 'lucide-react';

export default function Register() {
    const router = useRouter();
    const { setAuth } = useAuthStore();
    const [fullName, setFullName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        try {
            const response = await authAPI.register(email, password, fullName);

            if (response.data.access_token) {
                setAuth({ email, role: 'user' }, response.data.access_token);
                toast.success('Welcome to VigilAI!');
                router.push('/');
            } else {
                toast.success('Account created! Please login.');
                router.push('/login?registered=true');
            }
        } catch (err: any) {
            toast.error(err.response?.data?.detail || 'Registration failed');
        } finally {
            setLoading(false);
        }
    };

    const features = [
        'Real-time competitor monitoring',
        'AI-powered battlecard generation',
        'Predictive scenario analysis',
        'Automated intelligence reports',
    ];

    return (
        <>
            <Head>
                <title>Sign Up - VigilAI</title>
            </Head>

            <div className="min-h-screen flex">
                {/* Left Panel - Form */}
                <div className="flex-1 flex items-center justify-center p-8 bg-gradient-to-br from-gray-50 to-primary-50/30">
                    <div className="w-full max-w-md">
                        {/* Mobile Logo */}
                        <div className="lg:hidden text-center mb-8">
                            <div className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-primary-500 to-accent-500 rounded-xl text-white">
                                <Sparkles size={20} />
                                <span className="font-bold">VigilAI</span>
                            </div>
                        </div>

                        <div className="text-center mb-8">
                            <h1 className="text-3xl font-bold text-gray-900">Create your account</h1>
                            <p className="text-gray-500 mt-2">Start your competitive intelligence journey</p>
                        </div>

                        <div className="card">
                            <form onSubmit={handleSubmit} className="space-y-5">
                                <div>
                                    <label htmlFor="fullName" className="block text-sm font-semibold text-gray-700 mb-2">
                                        Full Name
                                    </label>
                                    <div className="relative">
                                        <User className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                                        <input
                                            id="fullName"
                                            type="text"
                                            value={fullName}
                                            onChange={(e) => setFullName(e.target.value)}
                                            className="w-full pl-11 pr-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary-500/20 focus:border-primary-400 transition-all text-gray-900"
                                            placeholder="John Doe"
                                            required
                                        />
                                    </div>
                                </div>

                                <div>
                                    <label htmlFor="email" className="block text-sm font-semibold text-gray-700 mb-2">
                                        Email Address
                                    </label>
                                    <div className="relative">
                                        <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                                        <input
                                            id="email"
                                            type="email"
                                            value={email}
                                            onChange={(e) => setEmail(e.target.value)}
                                            className="w-full pl-11 pr-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary-500/20 focus:border-primary-400 transition-all text-gray-900"
                                            placeholder="you@company.com"
                                            required
                                        />
                                    </div>
                                </div>

                                <div>
                                    <label htmlFor="password" className="block text-sm font-semibold text-gray-700 mb-2">
                                        Password
                                    </label>
                                    <div className="relative">
                                        <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                                        <input
                                            id="password"
                                            type="password"
                                            value={password}
                                            onChange={(e) => setPassword(e.target.value)}
                                            className="w-full pl-11 pr-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary-500/20 focus:border-primary-400 transition-all text-gray-900"
                                            placeholder="••••••••"
                                            required
                                        />
                                    </div>
                                </div>

                                <button
                                    type="submit"
                                    disabled={loading}
                                    className="w-full py-3.5 bg-gradient-to-r from-primary-500 to-primary-600 text-white font-semibold rounded-xl shadow-lg shadow-primary-500/30 hover:shadow-xl hover:shadow-primary-500/40 hover:-translate-y-0.5 transition-all duration-300 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0"
                                >
                                    {loading ? (
                                        <>
                                            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                            Creating Account...
                                        </>
                                    ) : (
                                        <>
                                            Get Started
                                            <ArrowRight size={18} />
                                        </>
                                    )}
                                </button>
                            </form>

                            <div className="mt-6 text-center text-sm text-gray-500">
                                Already have an account?{' '}
                                <Link href="/login" className="text-primary-600 hover:text-primary-700 font-semibold">
                                    Sign in
                                </Link>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right Panel - Decorative */}
                <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-accent-500 via-accent-600 to-primary-600 p-12 flex-col justify-between relative overflow-hidden">
                    {/* Background patterns */}
                    <div className="absolute inset-0 opacity-10">
                        <div className="absolute top-20 right-20 w-64 h-64 bg-white rounded-full blur-3xl" />
                        <div className="absolute bottom-20 left-20 w-96 h-96 bg-primary-300 rounded-full blur-3xl" />
                    </div>

                    <div className="relative">
                        <div className="flex items-center gap-3">
                            <div className="w-12 h-12 rounded-xl bg-white/20 backdrop-blur flex items-center justify-center">
                                <Sparkles className="text-white" size={24} />
                            </div>
                            <span className="text-2xl font-bold text-white">VigilAI</span>
                        </div>
                    </div>

                    <div className="relative">
                        <h2 className="text-4xl font-bold text-white mb-6">
                            Everything you need
                            <br />
                            to stay ahead
                        </h2>

                        <div className="space-y-4">
                            {features.map((feature, i) => (
                                <div key={i} className="flex items-center gap-3">
                                    <div className="w-6 h-6 rounded-full bg-white/20 flex items-center justify-center">
                                        <CheckCircle size={14} className="text-white" />
                                    </div>
                                    <span className="text-white/90">{feature}</span>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="relative">
                        <p className="text-white/60 text-sm">
                            Trusted by leading companies worldwide
                        </p>
                    </div>
                </div>
            </div>
        </>
    );
}
