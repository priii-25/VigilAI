import Link from 'next/link';
import { useRouter } from 'next/router';
import { Home, Target, FileText, AlertCircle, BarChart3, LogOut } from 'lucide-react';
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
    { href: '/simulation', icon: Target, label: 'War Room' },
  ];

  return (
    <div className="w-64 bg-gray-900 text-white flex flex-col">
      <div className="p-6">
        <h1 className="text-2xl font-bold">VigilAI</h1>
        <p className="text-gray-400 text-sm mt-1">Intelligence Platform</p>
      </div>

      <nav className="flex-1 px-4 space-y-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = router.pathname === item.href;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${isActive
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-300 hover:bg-gray-800'
                }`}
            >
              <Icon size={20} />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="p-4">
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 px-4 py-3 w-full rounded-lg text-gray-300 hover:bg-gray-800 transition-colors"
        >
          <LogOut size={20} />
          <span>Logout</span>
        </button>
      </div>
    </div>
  );
}
