'use client';

import { useQuery } from '@tanstack/react-query';
import { Activity, Instagram, Send, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { statsApi } from '@/lib/api';
import { Navigation } from '@/components/navigation';

export default function Dashboard() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['stats'],
    queryFn: async () => {
      const response = await statsApi.get();
      return response.data;
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  return (
    <>
      <Navigation />
      <main className="container mx-auto px-4 py-8">
        <div className="space-y-6">
          <h1 className="text-3xl font-bold">Dashboard</h1>
          
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : (
            <>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">
                      Perfis Totais
                    </CardTitle>
                    <Instagram className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{stats?.total_profiles || 0}</div>
                    <p className="text-xs text-muted-foreground">
                      {stats?.active_profiles || 0} ativos
                    </p>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">
                      Posts Baixados
                    </CardTitle>
                    <Send className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{stats?.total_posts || 0}</div>
                    <p className="text-xs text-muted-foreground">
                      Total de posts do feed
                    </p>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">
                      Stories Baixados
                    </CardTitle>
                    <Activity className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{stats?.total_stories || 0}</div>
                    <p className="text-xs text-muted-foreground">
                      Total de stories
                    </p>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">
                      Erros
                    </CardTitle>
                    <AlertCircle className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{stats?.total_errors || 0}</div>
                    <p className="text-xs text-muted-foreground">
                      Erros registrados
                    </p>
                  </CardContent>
                </Card>
              </div>
              
              <Card>
                <CardHeader>
                  <CardTitle>Última Atividade</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">
                    {stats?.last_check 
                      ? new Date(stats.last_check).toLocaleString('pt-BR')
                      : 'Nenhuma atividade registrada'}
                  </p>
                </CardContent>
              </Card>
            </>
          )}
        </div>
      </main>
    </>
  );
}
