
import React from 'react';
import { Button } from '@/components/ui/button';
import { Bell, Settings, Search, Shield } from 'lucide-react';

const Header: React.FC = () => {
  return (
    <header className="bg-white shadow-sm py-4 px-6 flex justify-between items-center">
      <div className="flex items-center space-x-2">
        <Shield className="h-6 w-6 text-green-600" />
        <h1 className="text-2xl font-bold text-green-700">Robinhood AI Tax Monitor</h1>
      </div>
      
      <div className="flex-1 mx-8 hidden md:block">
        <div className="relative">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search tax anomalies, wealth patterns..."
            className="pl-10 py-2 w-full max-w-md rounded-md border border-input bg-white"
          />
        </div>
      </div>
      
      <div className="flex items-center space-x-4">
        <Button variant="ghost" size="icon">
          <Bell className="h-5 w-5" />
        </Button>
        <Button variant="ghost" size="icon">
          <Settings className="h-5 w-5" />
        </Button>
        <Button variant="default" className="bg-green-600 hover:bg-green-700">
          Dashboard
        </Button>
      </div>
    </header>
  );
};

export default Header;
