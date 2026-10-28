import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import { fetchAuditTrail, verifyAuditChain } from '@/lib/api';
import type { AuditEvent, ChainVerification } from '@/lib/mockData';
import { Link2, ShieldCheck, ShieldX, Loader2 } from 'lucide-react';

const shortHash = (h: string | null) => (h ? `${h.slice(0, 10)}…${h.slice(-6)}` : '—');

const AuditLedger: React.FC = () => {
  const [verification, setVerification] = useState<ChainVerification | null>(null);

  const { data: trail, isLoading } = useQuery<AuditEvent[]>({
    queryKey: ['auditTrail'],
    queryFn: () => fetchAuditTrail(50),
  });

  const verifyMutation = useMutation({
    mutationFn: verifyAuditChain,
    onSuccess: (v) => setVerification(v as ChainVerification),
  });

  return (
    <Card className="mb-6">
      <CardHeader className="pb-2 flex flex-row items-center justify-between space-y-0">
        <div className="flex items-center">
          <Link2 className="h-5 w-5 text-fiscal-600 mr-2" />
          <div>
            <CardTitle className="text-lg font-semibold">Tamper-Evident Audit Ledger</CardTitle>
            <p className="text-sm text-muted-foreground">
              SHA-256 hash chain - every row links to its predecessor from genesis.
            </p>
          </div>
        </div>
        <Button
          size="sm"
          variant="outline"
          className="gap-2 shrink-0"
          onClick={() => verifyMutation.mutate()}
          disabled={verifyMutation.isPending}
        >
          {verifyMutation.isPending
            ? <Loader2 className="h-4 w-4 animate-spin" />
            : <ShieldCheck className="h-4 w-4" />}
          Verify Integrity
        </Button>
      </CardHeader>

      <CardContent>
        {verification && (
          <div className={`mb-3 rounded-md border p-3 text-sm flex items-center gap-2 ${
            verification.ok
              ? 'bg-green-50 border-green-200 text-green-800'
              : 'bg-red-50 border-red-200 text-red-800'
          }`}>
            {verification.ok
              ? <ShieldCheck className="h-4 w-4 shrink-0" />
              : <ShieldX className="h-4 w-4 shrink-0" />}
            {verification.ok
              ? <>Chain intact - {verification.length} events verified, head <span className="font-mono text-xs">{shortHash(verification.head_hash)}</span></>
              : <>Tampering detected at log_id <span className="font-bold">{verification.broken_at}</span> ({verification.reason})</>}
          </div>
        )}

        {isLoading ? (
          <div className="space-y-2">
            {[1, 2, 3].map((i) => <div key={i} className="h-10 bg-slate-100 animate-pulse rounded" />)}
          </div>
        ) : (
          <div className="rounded-md border max-h-[380px] overflow-y-auto">
            <Table>
              <TableHeader>
                <TableRow className="bg-slate-50/50 sticky top-0">
                  <TableHead>#</TableHead>
                  <TableHead>Timestamp (UTC)</TableHead>
                  <TableHead>Action</TableHead>
                  <TableHead>Actor</TableHead>
                  <TableHead>Target</TableHead>
                  <TableHead>Payload Hash</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(trail ?? []).map((e) => (
                  <TableRow key={e.log_id}>
                    <TableCell className="font-mono text-xs">{e.log_id}</TableCell>
                    <TableCell className="text-xs">{e.timestamp}</TableCell>
                    <TableCell>
                      <Badge variant="secondary" className="text-xs font-mono">{e.action_type}</Badge>
                    </TableCell>
                    <TableCell className="text-xs">{e.actor_id}</TableCell>
                    <TableCell className="text-xs font-mono">{e.target_user_id ?? '—'}</TableCell>
                    <TableCell className="font-mono text-xs" title={`prev: ${e.prev_hash}`}>
                      {shortHash(e.payload_hash)}
                    </TableCell>
                  </TableRow>
                ))}
                {trail?.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center py-6 text-muted-foreground">
                      No ledger events yet
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default AuditLedger;
