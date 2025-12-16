import { Bell, Search, Settings } from 'lucide-react';
import { useAuthStore } from '@/store/authStore';

export default function Header() {
  const { user } = useAuthStore();

  const getInitials = (email: string) => {
    return email?.charAt(0).toUpperCase() || 'U';
  };

  return (
    <header className="bg-white/70 backdrop-blur-xl border-b border-gray-200/50 px-6 py-4 sticky top-0 z-50">
      <div className="flex items-center justify-between">
        {/* Search Bar */}
        <div className="flex-1 max-w-xl">
          <div className="relative group">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 group-focus-within:text-primary-500 transition-colors" size={20} />
            <input
              type="text"
              placeholder="Search competitors, battlecards, insights..."
              className="w-full pl-12 pr-4 py-3 bg-gray-50/80 border border-gray-200/80 rounded-xl 
                         focus:ring-2 focus:ring-primary-500/20 focus:border-primary-400 focus:bg-white
                         transition-all duration-300 placeholder:text-gray-400"
            />
            <kbd className="absolute right-4 top-1/2 transform -translate-y-1/2 hidden sm:inline-flex items-center gap-1 px-2 py-1 text-xs text-gray-400 bg-gray-100 rounded-md border border-gray-200">
              ⌘K
            </kbd>
          </div>
        </div>

        {/* Right Section */}
        <div className="flex items-center gap-3 ml-6">
          {/* Settings Button */}
          <button className="p-2.5 text-gray-500 hover:text-primary-600 hover:bg-primary-50 rounded-xl transition-all duration-300">
            <Settings size={20} />
          </button>

          {/* Notifications */}
          <button className="relative p-2.5 text-gray-500 hover:text-primary-600 hover:bg-primary-50 rounded-xl transition-all duration-300">
            <Bell size={20} />
            <span className="absolute top-2 right-2 w-2.5 h-2.5 bg-gradient-to-r from-rose-500 to-orange-500 rounded-full ring-2 ring-white">
              <span className="absolute inset-0 rounded-full bg-rose-500 animate-ping opacity-75" />
            </span>
          </button>

          {/* Divider */}
          <div className="w-px h-8 bg-gray-200 mx-2" />

          {/* User Profile */}
          <div className="flex items-center gap-3">
            <div className="text-right hidden sm:block">
              <p className="text-sm font-semibold text-gray-900">{user?.email?.split('@')[0] || 'User'}</p>
              <p className="text-xs text-gray-500 capitalize">{user?.role || 'Admin'}</p>
            </div>
            <div className="relative">
              <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center text-white font-bold text-lg shadow-lg shadow-primary-500/30 ring-2 ring-white">
                {getInitials(user?.email || '')}
              </div>
              <span className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 bg-emerald-500 rounded-full ring-2 ring-white" />
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
