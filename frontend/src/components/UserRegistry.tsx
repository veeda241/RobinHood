
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchUsers, flagUser, sendNotice, addUser, processPayment } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import {
    UserPlus,
    Flag,
    Mail,
    CreditCard,
    Search,
    AlertTriangle,
    CheckCircle2,
    Clock
} from 'lucide-react';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogTrigger
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';

const UserRegistry: React.FC = () => {
    const queryClient = useQueryClient();
    const [searchTerm, setSearchTerm] = useState('');
    const [isAddUserOpen, setIsAddUserOpen] = useState(false);
    const [newUserId, setNewUserId] = useState('');
    const [newIncome, setNewIncome] = useState('');
    const [newTaxPaid, setNewTaxPaid] = useState('');

    const { data: users, isLoading } = useQuery({
        queryKey: ['users'],
        queryFn: fetchUsers,
    });

    const flagMutation = useMutation({
        mutationFn: flagUser,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['users'] });
            queryClient.invalidateQueries({ queryKey: ['stats'] });
            toast.success('User flag toggled');
        },
    });

    const addUserMutation = useMutation({
        mutationFn: addUser,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['users'] });
            queryClient.invalidateQueries({ queryKey: ['stats'] });
            setIsAddUserOpen(false);
            setNewUserId('');
            setNewIncome('');
            setNewTaxPaid('');
            toast.success('User added successfully');
        },
    });

    const handleAddUser = (e: React.FormEvent) => {
        e.preventDefault();
        addUserMutation.mutate({
            user_id: newUserId,
            declared_income: parseFloat(newIncome),
            tax_paid: parseFloat(newTaxPaid || '0'),
        });
    };

    const filteredUsers = users?.filter((user: any) =>
        user.user_id.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'Compliant':
                return <Badge className="bg-green-100 text-green-700 hover:bg-green-100 border-green-200"><CheckCircle2 className="w-3 h-3 mr-1" /> Compliant</Badge>;
            case 'Underpaid':
                return <Badge className="bg-amber-100 text-amber-700 hover:bg-amber-100 border-amber-200"><Clock className="w-3 h-3 mr-1" /> Underpaid</Badge>;
            default:
                return <Badge variant="outline">{status}</Badge>;
        }
    };

    return (
        <Card className="w-full">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
                <div>
                    <CardTitle className="text-xl font-bold">Taxpayer Registry</CardTitle>
                    <p className="text-sm text-muted-foreground mt-1">Manage and monitor taxpayer compliance</p>
                </div>
                <div className="flex gap-2">
                    <div className="relative w-64">
                        <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                        <Input
                            placeholder="Search User ID..."
                            className="pl-9 h-9"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>
                    <Dialog open={isAddUserOpen} onOpenChange={setIsAddUserOpen}>
                        <DialogTrigger asChild>
                            <Button size="sm" className="bg-fiscal-600 hover:bg-fiscal-700">
                                <UserPlus className="h-4 w-4 mr-2" /> Add Taxpayer
                            </Button>
                        </DialogTrigger>
                        <DialogContent>
                            <DialogHeader>
                                <DialogTitle>Add New Taxpayer</DialogTitle>
                            </DialogHeader>
                            <form onSubmit={handleAddUser} className="space-y-4 pt-4">
                                <div className="space-y-2">
                                    <Label htmlFor="uid">User ID</Label>
                                    <Input id="uid" value={newUserId} onChange={(e) => setNewUserId(e.target.value)} required />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="inc">Declared Income (₹)</Label>
                                    <Input id="inc" type="number" value={newIncome} onChange={(e) => setNewIncome(e.target.value)} required />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="tax">Tax Paid (₹)</Label>
                                    <Input id="tax" type="number" value={newTaxPaid} onChange={(e) => setNewTaxPaid(e.target.value)} />
                                </div>
                                <Button type="submit" className="w-full" disabled={addUserMutation.isPending}>
                                    {addUserMutation.isPending ? 'Registering...' : 'Register Taxpayer'}
                                </Button>
                            </form>
                        </DialogContent>
                    </Dialog>
                </div>
            </CardHeader>
            <CardContent>
                {isLoading ? (
                    <div className="space-y-2">
                        {[1, 2, 3].map((i) => (
                            <div key={i} className="h-12 w-full bg-slate-100 animate-pulse rounded" />
                        ))}
                    </div>
                ) : (
                    <div className="rounded-md border">
                        <Table>
                            <TableHeader>
                                <TableRow className="bg-slate-50/50">
                                    <TableHead>User ID</TableHead>
                                    <TableHead>Income</TableHead>
                                    <TableHead>Expected</TableHead>
                                    <TableHead>Paid</TableHead>
                                    <TableHead>Status</TableHead>
                                    <TableHead className="text-right">Actions</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {filteredUsers?.map((user: any) => (
                                    <TableRow key={user.user_id} className={user.flagged ? "bg-red-50/30" : ""}>
                                        <TableCell className="font-medium">
                                            <div className="flex items-center gap-2">
                                                {user.user_id}
                                                {user.flagged && <AlertTriangle className="h-3 w-3 text-red-500" />}
                                            </div>
                                        </TableCell>
                                        <TableCell>₹{user.declared_income.toLocaleString()}</TableCell>
                                        <TableCell>₹{user.expected_tax.toLocaleString()}</TableCell>
                                        <TableCell>₹{user.tax_paid.toLocaleString()}</TableCell>
                                        <TableCell>{getStatusBadge(user.compliance_status)}</TableCell>
                                        <TableCell className="text-right">
                                            <div className="flex justify-end gap-1">
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    title="Toggle Flag"
                                                    onClick={() => flagMutation.mutate(user.user_id)}
                                                    className={user.flagged ? "text-red-600 hover:text-red-700 hover:bg-red-50" : "text-slate-400"}
                                                >
                                                    <Flag className="h-4 w-4" />
                                                </Button>
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    title="Send Notice"
                                                    onClick={() => {
                                                        sendNotice(user.user_id, 'reminder');
                                                        toast.success('Notice sent to ' + user.user_id);
                                                    }}
                                                    className="text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                                                >
                                                    <Mail className="h-4 w-4" />
                                                </Button>
                                            </div>
                                        </TableCell>
                                    </TableRow>
                                ))}
                                {filteredUsers?.length === 0 && (
                                    <TableRow>
                                        <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                                            No taxpayers found
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

export default UserRegistry;
