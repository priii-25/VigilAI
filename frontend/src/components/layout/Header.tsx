import { Bell, Search } from 'lucide-react';
import { useAuthStore } from '@/store/authStore';

export default function Header() {
  const { user } = useAuthStore();

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex-1 max-w-lg">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="Search competitors, battlecards..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          <button className="relative p-2 text-gray-600 hover:bg-gray-100 rounded-lg">
            <Bell size={20} />
            <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
          </button>
          
          <div className="flex items-center gap-3">
            <div className="text-right">
              <p className="text-sm font-medium text-gray-900">{user?.email || 'User'}</p>
              <p className="text-xs text-gray-500 capitalize">{user?.role || 'user'}</p>
            </div>
            <div className="w-10 h-10 bg-primary-600 rounded-full flex items-center justify-center text-white font-medium">
              {user?.email?.charAt(0).toUpperCase() || 'U'}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
