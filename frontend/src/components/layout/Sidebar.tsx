import Link from 'next/link';
import { useRouter } from 'next/router';
import { Home, Target, FileText, AlertCircle, BarChart3, LogOut, Zap, Sparkles } from 'lucide-react';
import { useAuthStore } from '@/store/authStore';

export default function Sidebar() {
  const router = useRouter();
  const { logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  const navItems = [
    { href: '/', icon: Home, label: 'Dashboard' },
    { href: '/competitors', icon: Target, label: 'Competitors' },
    { href: '/battlecards', icon: FileText, label: 'Battlecards' },
    { href: '/logs', icon: AlertCircle, label: 'Log Analysis' },
    { href: '/analytics', icon: BarChart3, label: 'Analytics' },
    { href: '/simulation', icon: Zap, label: 'War Room' },
  ];

  return (
    <div className="w-72 bg-white/70 backdrop-blur-xl border-r border-gray-200/50 flex flex-col shadow-soft">
      {/* Logo Section */}
      <div className="p-6 border-b border-gray-100">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center shadow-lg shadow-primary-500/30">
            <Sparkles className="text-white" size={20} />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gradient">VigilAI</h1>
            <p className="text-xs text-gray-500">Intelligence Platform</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-1.5">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = router.pathname === item.href;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 group ${isActive
                  ? 'bg-gradient-to-r from-primary-500 to-primary-600 text-white shadow-lg shadow-primary-500/30'
                  : 'text-gray-600 hover:bg-primary-50 hover:text-primary-600'
                }`}
            >
              <Icon
                size={20}
                className={`transition-transform duration-300 ${!isActive && 'group-hover:scale-110'}`}
              />
              <span className="font-medium">{item.label}</span>
              {isActive && (
                <div className="ml-auto w-2 h-2 rounded-full bg-white/50 animate-pulse" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* Pro Badge */}
      <div className="mx-4 mb-4 p-4 rounded-xl bg-gradient-to-r from-primary-50 to-accent-50 border border-primary-100">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-6 h-6 rounded-lg bg-gradient-to-r from-primary-500 to-accent-500 flex items-center justify-center">
            <Zap size={14} className="text-white" />
          </div>
          <span className="text-sm font-semibold text-gray-700">Pro Plan</span>
        </div>
        <p className="text-xs text-gray-500">Full access to AI features</p>
      </div>

      {/* Logout */}
      <div className="p-4 border-t border-gray-100">
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 px-4 py-3 w-full rounded-xl text-gray-500 hover:bg-rose-50 hover:text-rose-600 transition-all duration-300"
        >
          <LogOut size={20} />
          <span className="font-medium">Logout</span>
        </button>
      </div>
    </div>
  );
}
