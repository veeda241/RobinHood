import { useQuery } from '@tanstack/react-query';
import { fetchMe } from '@/lib/api';

export interface SessionPrincipal {
  mode: string | null;
  role: string | null;
  email?: string | null;
}

/** Reads the hybrid session: admin cookie role and/or Supabase citizen state. */
export function useMe() {
  return useQuery<SessionPrincipal>({
    queryKey: ['me'],
    queryFn: fetchMe,
    staleTime: 30_000,
  });
}
