import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Shield, LogOut, LayoutDashboard, UserCog } from 'lucide-react';
import { useMe } from '@/lib/auth';
import { adminLogout } from '@/lib/api';

const Header: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data: me } = useMe();
  const isAdmin = me?.role === 'admin';

  const logoutMutation = useMutation({
    mutationFn: adminLogout,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['me'] });
      navigate('/');
    },
  });

  return (
    <header className="bg-white shadow-sm py-4 px-6 flex justify-between items-center">
      <Link to="/" className="flex items-center space-x-2">
        <Shield className="h-6 w-6 text-green-600" />
        <h1 className="text-2xl font-bold text-green-700">Robinhood AI</h1>
      </Link>

      <div className="flex items-center space-x-4">
        {isAdmin && (
          <Badge variant="outline" className="border-green-300 text-green-700">
            Admin session active
          </Badge>
        )}
        <Button variant="ghost" size="sm" className="gap-2" asChild>
          <Link to="/">
            <LayoutDashboard className="h-4 w-4" /> Citizen Portal
          </Link>
        </Button>
        {isAdmin ? (
          <Button
            variant="ghost"
            size="sm"
            className="gap-2 text-red-600 hover:text-red-700"
            onClick={() => logoutMutation.mutate()}
            disabled={logoutMutation.isPending}
          >
            <LogOut className="h-4 w-4" /> Sign out
          </Button>
        ) : (
          <Button
            size="sm"
            className="bg-green-600 hover:bg-green-700 gap-2"
            asChild
          >
            <Link to="/admin">
              <UserCog className="h-4 w-4" /> Admin Command Center
            </Link>
          </Button>
        )}
      </div>
    </header>
  );
};

export default Header;
