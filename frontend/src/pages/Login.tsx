import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { adminLogin, ApiError } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { ShieldCheck, Loader2 } from 'lucide-react';

const Login: React.FC = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const loginMutation = useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      adminLogin(email, password),
    onSuccess: () => navigate('/admin'),
  });

  const error = loginMutation.error
    ? loginMutation.error instanceof ApiError && loginMutation.error.status === 429
      ? 'Too many attempts - wait a minute and try again.'
      : loginMutation.error.message
    : null;

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-2 text-center">
          <div className="mx-auto h-12 w-12 rounded-full bg-green-100 flex items-center justify-center">
            <ShieldCheck className="h-6 w-6 text-green-700" />
          </div>
          <CardTitle className="text-2xl font-bold">Admin Command Center</CardTitle>
          <p className="text-sm text-muted-foreground">
            Signed session with rate-limited login (5/min). All access is recorded
            in the tamper-evident audit ledger.
          </p>
        </CardHeader>
        <CardContent>
          <form
            className="space-y-4"
            onSubmit={(e) => {
              e.preventDefault();
              loginMutation.mutate({ email, password });
            }}
          >
            <div className="space-y-2">
              <Label htmlFor="email">Admin email</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="username"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
              />
            </div>
            {error && (
              <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded p-2">
                {error}
              </p>
            )}
            <Button type="submit" className="w-full bg-green-700 hover:bg-green-800" disabled={loginMutation.isPending}>
              {loginMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
              Sign in
            </Button>
            <p className="text-xs text-muted-foreground text-center">
              Offline demo fallback: admin@robinhood.gov.in / admin-demo-123
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default Login;
