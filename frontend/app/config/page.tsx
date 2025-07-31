'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Trash2, Play, Pause, RefreshCw, FlaskConical, X } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { profilesApi, ProfileCreate, TestResult } from '@/lib/api';
import { Navigation } from '@/components/navigation';

export default function Config() {
  const queryClient = useQueryClient();
  const [showAddForm, setShowAddForm] = useState(false);
  const [testingProfile, setTestingProfile] = useState<number | null>(null);
  const [testResults, setTestResults] = useState<TestResult | null>(null);
  const [showTestModal, setShowTestModal] = useState(false);
  const [formData, setFormData] = useState<ProfileCreate>({
    username: '',
    webhook_url: '',
    check_interval: 30,
    download_posts: true,
    download_stories: true,
  });

  const { data: profiles, isLoading } = useQuery({
    queryKey: ['profiles'],
    queryFn: async () => {
      const response = await profilesApi.list();
      return response.data;
    },
  });

  const createMutation = useMutation({
    mutationFn: profilesApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profiles'] });
      setShowAddForm(false);
      setFormData({
        username: '',
        webhook_url: '',
        check_interval: 30,
        download_posts: true,
        download_stories: true,
      });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) =>
      profilesApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profiles'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: profilesApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profiles'] });
    },
  });

  const forceCheckMutation = useMutation({
    mutationFn: profilesApi.forceCheck,
  });

  const testScrapingMutation = useMutation({
    mutationFn: profilesApi.testScraping,
    onSuccess: (response) => {
      console.log('🎯 [TEST] Teste concluído com sucesso:', response.data);
      setTestResults(response.data);
      setTestingProfile(null);
    },
    onError: (error) => {
      console.error('💥 [TEST] Erro durante o teste:', error);
      setTestingProfile(null);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate(formData);
  };

  const toggleActive = (id: number, currentState: boolean) => {
    updateMutation.mutate({ id, data: { is_active: !currentState } });
  };

  const handleForceCheck = (id: number) => {
    forceCheckMutation.mutate(id);
  };

  const handleTestScraping = (id: number, username: string) => {
    console.log(`🚀 [TEST] Iniciando teste para @${username} (ID: ${id})`);
    setTestingProfile(id);
    setTestResults(null);
    setShowTestModal(true);
    testScrapingMutation.mutate(id);
  };

  return (
    <>
      <Navigation />
      <main className="container mx-auto px-4 py-8">
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <h1 className="text-3xl font-bold">Configurações</h1>
            <Button onClick={() => setShowAddForm(!showAddForm)}>
              <Plus className="mr-2 h-4 w-4" />
              Adicionar Perfil
            </Button>
          </div>

          {showAddForm && (
            <Card>
              <CardHeader>
                <CardTitle>Adicionar Novo Perfil</CardTitle>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="username">Username do Instagram</Label>
                      <Input
                        id="username"
                        placeholder="username (sem @)"
                        value={formData.username}
                        onChange={(e) =>
                          setFormData({ ...formData, username: e.target.value })
                        }
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="webhook_url">URL do Webhook (N8N)</Label>
                      <Input
                        id="webhook_url"
                        type="url"
                        placeholder="https://n8n.example.com/webhook/..."
                        value={formData.webhook_url}
                        onChange={(e) =>
                          setFormData({ ...formData, webhook_url: e.target.value })
                        }
                        required
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="check_interval">Intervalo de Checagem</Label>
                    <Select
                      value={formData.check_interval.toString()}
                      onValueChange={(value) =>
                        setFormData({
                          ...formData,
                          check_interval: parseInt(value),
                        })
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="15">15 minutos</SelectItem>
                        <SelectItem value="30">30 minutos</SelectItem>
                        <SelectItem value="60">1 hora</SelectItem>
                        <SelectItem value="120">2 horas</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="flex gap-6">
                    <div className="flex items-center space-x-2">
                      <Switch
                        id="download_posts"
                        checked={formData.download_posts}
                        onCheckedChange={(checked) =>
                          setFormData({ ...formData, download_posts: checked })
                        }
                      />
                      <Label htmlFor="download_posts">Baixar Posts do Feed</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Switch
                        id="download_stories"
                        checked={formData.download_stories}
                        onCheckedChange={(checked) =>
                          setFormData({ ...formData, download_stories: checked })
                        }
                      />
                      <Label htmlFor="download_stories">Baixar Stories</Label>
                    </div>
                  </div>

                  <Button type="submit" disabled={createMutation.isPending}>
                    {createMutation.isPending ? 'Adicionando...' : 'Adicionar Perfil'}
                  </Button>
                </form>
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle>Perfis Configurados</CardTitle>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="flex justify-center p-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
              ) : profiles && profiles.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Username</TableHead>
                      <TableHead>Webhook</TableHead>
                      <TableHead>Intervalo</TableHead>
                      <TableHead>Posts</TableHead>
                      <TableHead>Stories</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Ações</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {profiles.map((profile) => (
                      <TableRow key={profile.id}>
                        <TableCell className="font-medium">
                          @{profile.username}
                        </TableCell>
                        <TableCell className="max-w-xs truncate">
                          {profile.webhook_url}
                        </TableCell>
                        <TableCell>{profile.check_interval} min</TableCell>
                        <TableCell>
                          {profile.download_posts ? '✓' : '✗'}
                        </TableCell>
                        <TableCell>
                          {profile.download_stories ? '✓' : '✗'}
                        </TableCell>
                        <TableCell>
                          <span
                            className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                              profile.is_active
                                ? 'bg-green-100 text-green-800'
                                : 'bg-red-100 text-red-800'
                            }`}
                          >
                            {profile.is_active ? 'Ativo' : 'Inativo'}
                          </span>
                        </TableCell>
                        <TableCell>
                          <div className="flex gap-2">
                            <Button
                              size="icon"
                              variant="ghost"
                              onClick={() => toggleActive(profile.id, profile.is_active)}
                            >
                              {profile.is_active ? (
                                <Pause className="h-4 w-4" />
                              ) : (
                                <Play className="h-4 w-4" />
                              )}
                            </Button>
                            <Button
                              size="icon"
                              variant="ghost"
                              onClick={() => handleForceCheck(profile.id)}
                              disabled={!profile.is_active}
                              title="Forçar checagem"
                            >
                              <RefreshCw className="h-4 w-4" />
                            </Button>
                            <Button
                              size="icon"
                              variant="ghost"
                              onClick={() => handleTestScraping(profile.id, profile.username)}
                              disabled={testingProfile === profile.id}
                              title="Testar scraping"
                            >
                              <FlaskConical className="h-4 w-4" />
                            </Button>
                            <Button
                              size="icon"
                              variant="ghost"
                              onClick={() => deleteMutation.mutate(profile.id)}
                              title="Deletar perfil"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <p className="text-center text-muted-foreground py-8">
                  Nenhum perfil configurado ainda.
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      </main>

      {/* Modal de Teste */}
      {showTestModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="w-full max-w-2xl max-h-[80vh] overflow-hidden">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Teste de Scraping</CardTitle>
              <Button
                size="icon"
                variant="ghost"
                onClick={() => {
                  setShowTestModal(false);
                  setTestResults(null);
                  setTestingProfile(null);
                }}
              >
                <X className="h-4 w-4" />
              </Button>
            </CardHeader>
            <CardContent className="overflow-y-auto max-h-[calc(80vh-100px)]">
              {testingProfile && !testResults ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                  </div>
                  <p className="text-center text-muted-foreground">
                    Executando teste de scraping...
                  </p>
                  <div className="bg-yellow-100 text-yellow-800 p-3 rounded-lg text-sm">
                    <p className="font-semibold">⚠️ Importante:</p>
                    <p>O Instagram limita requisições anônimas. Se receber erro 401, aguarde 5-10 minutos antes de tentar novamente.</p>
                  </div>
                </div>
              ) : testResults ? (
                <div className="space-y-4">
                  {/* Warning */}
                  {testResults.warning && (
                    <div className="bg-yellow-100 text-yellow-800 p-3 rounded-lg text-sm">
                      <p>{testResults.warning}</p>
                    </div>
                  )}
                  
                  {/* Status Geral */}
                  <div className={`p-4 rounded-lg ${testResults.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                    <h3 className="font-semibold">
                      {testResults.success ? '✅ Teste Concluído com Sucesso' : '❌ Teste Falhou'}
                    </h3>
                    <p className="text-sm mt-1">Perfil: @{testResults.profile}</p>
                    {testResults.error && (
                      <p className="text-sm mt-2 font-mono">{testResults.error}</p>
                    )}
                  </div>

                  {/* Steps */}
                  <div className="space-y-2">
                    <h4 className="font-semibold">Etapas do Teste:</h4>
                    {testResults.steps.map((step, index) => (
                      <div key={index} className="flex items-start gap-2 text-sm">
                        <span className={`mt-0.5 ${
                          step.status === 'completed' ? '✅' : 
                          step.status === 'failed' ? '❌' : '⏳'
                        }`} />
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{step.step}</span>
                            <span className="text-xs text-muted-foreground">
                              {new Date(step.timestamp).toLocaleTimeString()}
                            </span>
                          </div>
                          {step.details && (
                            <p className="text-muted-foreground">{step.details}</p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Media Found */}
                  {testResults.media_found && (
                    <div className="space-y-2 p-4 bg-muted rounded-lg">
                      <h4 className="font-semibold">Mídia Encontrada:</h4>
                      <div className="text-sm space-y-1">
                        <p>Tipo: {testResults.media_found.type} {testResults.media_found.is_video ? '(vídeo)' : '(imagem)'}</p>
                        {testResults.media_found.shortcode && (
                          <p>Código: {testResults.media_found.shortcode}</p>
                        )}
                        <p>Timestamp: {new Date(testResults.media_found.timestamp).toLocaleString()}</p>
                        {testResults.media_found.download_skipped && (
                          <p className="text-yellow-600">
                            ⚠️ Download não realizado: {testResults.media_found.reason}
                          </p>
                        )}
                        {testResults.media_found.caption && (
                          <p className="mt-2 p-2 bg-background rounded">
                            Caption: {testResults.media_found.caption}...
                          </p>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Webhook Result */}
                  {testResults.webhook_result && (
                    <div className="space-y-2 p-4 bg-muted rounded-lg">
                      <h4 className="font-semibold">Configuração do Webhook:</h4>
                      <div className="text-sm space-y-1">
                        {testResults.webhook_result.configured ? (
                          <>
                            <p className="text-green-600">✅ Webhook configurado</p>
                            {testResults.webhook_result.test_skipped && (
                              <p className="text-yellow-600">
                                ⚠️ Teste não realizado: {testResults.webhook_result.reason}
                              </p>
                            )}
                          </>
                        ) : (
                          <p className={testResults.webhook_result.success ? 'text-green-600' : 'text-red-600'}>
                            {testResults.webhook_result.success ? '✅ Enviado com sucesso' : '❌ Falha no envio'}
                          </p>
                        )}
                        <p className="text-xs font-mono">{testResults.webhook_result.url}</p>
                      </div>
                    </div>
                  )}
                </div>
              ) : null}
            </CardContent>
          </Card>
        </div>
      )}
    </>
  );
}