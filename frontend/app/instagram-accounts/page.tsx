'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useToast } from '@/hooks/use-toast'
import { Loader2, User, Check, X, Plus, Trash2, Eye, EyeOff } from 'lucide-react'
import api from '@/lib/api'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'

interface InstagramAccount {
  id: number
  username: string
  is_active: boolean
  last_login: string | null
  created_at: string
  updated_at: string
  has_valid_session: boolean
}

export default function InstagramAccountsPage() {
  const [accounts, setAccounts] = useState<InstagramAccount[]>([])
  const [loading, setLoading] = useState(true)
  const [isCreating, setIsCreating] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [newAccount, setNewAccount] = useState({ username: '', password: '' })
  const { toast } = useToast()
  const [isOpen, setIsOpen] = useState(false)
  const [testingLogin, setTestingLogin] = useState<number | null>(null)
  const [testPassword, setTestPassword] = useState('')

  useEffect(() => {
    fetchAccounts()
  }, [])

  const fetchAccounts = async () => {
    try {
      const response = await api.get('/api/instagram-accounts')
      setAccounts(response.data || [])
    } catch (error) {
      console.error('Error fetching accounts:', error)
      toast({
        title: 'Error',
        description: 'Failed to fetch Instagram accounts',
        variant: 'destructive'
      })
      setAccounts([])
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async () => {
    if (!newAccount.username || !newAccount.password) {
      toast({
        title: 'Error',
        description: 'Please provide both username and password',
        variant: 'destructive'
      })
      return
    }

    setIsCreating(true)
    try {
      await api.post('/api/instagram-accounts', newAccount)
      toast({
        title: 'Success',
        description: 'Instagram account created successfully'
      })
      setNewAccount({ username: '', password: '' })
      setIsOpen(false)
      fetchAccounts()
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to create account',
        variant: 'destructive'
      })
    } finally {
      setIsCreating(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this account?')) return

    try {
      await api.delete(`/api/instagram-accounts/${id}`)
      toast({
        title: 'Success',
        description: 'Instagram account deleted successfully'
      })
      fetchAccounts()
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to delete account',
        variant: 'destructive'
      })
    }
  }

  const handleTestLogin = async (account: InstagramAccount) => {
    if (!testPassword) {
      toast({
        title: 'Error',
        description: 'Please enter the password',
        variant: 'destructive'
      })
      return
    }

    setTestingLogin(account.id)
    try {
      const response = await api.post(`/api/instagram-accounts/${account.id}/test-login`, null, {
        params: { password: testPassword }
      })
      
      if (response.data.success) {
        toast({
          title: 'Success',
          description: 'Login successful! Session saved for future use.'
        })
        fetchAccounts()
      } else {
        toast({
          title: 'Error',
          description: response.data.message || 'Login failed',
          variant: 'destructive'
        })
      }
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to test login',
        variant: 'destructive'
      })
    } finally {
      setTestingLogin(null)
      setTestPassword('')
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    )
  }

  return (
    <div className="container mx-auto p-4">
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Instagram Accounts</h1>
          <p className="text-muted-foreground mt-2">
            Configure Instagram accounts for authenticated scraping
          </p>
        </div>
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Add Account
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add Instagram Account</DialogTitle>
              <DialogDescription>
                Add an Instagram account to use for authenticated scraping. This helps avoid rate limits.
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="username">Username</Label>
                <Input
                  id="username"
                  value={newAccount.username}
                  onChange={(e) => setNewAccount({ ...newAccount, username: e.target.value })}
                  placeholder="instagram_username"
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="password">Password</Label>
                <div className="relative">
                  <Input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    value={newAccount.password}
                    onChange={(e) => setNewAccount({ ...newAccount, password: e.target.value })}
                    placeholder="Enter password"
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button
                onClick={handleCreate}
                disabled={isCreating}
              >
                {isCreating ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Creating...
                  </>
                ) : (
                  'Create Account'
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {accounts.length === 0 ? (
        <Card>
          <CardContent className="text-center py-12">
            <User className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
            <h3 className="text-lg font-semibold mb-2">No Instagram Accounts</h3>
            <p className="text-muted-foreground mb-4">
              Add an Instagram account to enable authenticated scraping
            </p>
            <Button onClick={() => setIsOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Add Your First Account
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.isArray(accounts) && accounts.map((account) => (
            <Card key={account.id}>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="text-lg">@{account.username}</CardTitle>
                    <CardDescription>
                      Created {new Date(account.created_at).toLocaleDateString()}
                    </CardDescription>
                  </div>
                  <Badge variant={account.is_active ? 'default' : 'secondary'}>
                    {account.is_active ? 'Active' : 'Inactive'}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-muted-foreground">Session:</span>
                    {account.has_valid_session ? (
                      <Badge variant="outline" className="text-green-600">
                        <Check className="h-3 w-3 mr-1" />
                        Valid
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="text-red-600">
                        <X className="h-3 w-3 mr-1" />
                        Invalid
                      </Badge>
                    )}
                  </div>
                  {account.last_login && (
                    <div className="text-sm text-muted-foreground">
                      Last login: {new Date(account.last_login).toLocaleString()}
                    </div>
                  )}
                </div>
                <div className="flex gap-2 mt-4">
                  {!account.has_valid_session && (
                    <Dialog>
                      <DialogTrigger asChild>
                        <Button size="sm" variant="outline">
                          Test Login
                        </Button>
                      </DialogTrigger>
                      <DialogContent>
                        <DialogHeader>
                          <DialogTitle>Test Login for @{account.username}</DialogTitle>
                          <DialogDescription>
                            Enter the password to test the login and save a session.
                          </DialogDescription>
                        </DialogHeader>
                        <div className="grid gap-4 py-4">
                          <div className="grid gap-2">
                            <Label htmlFor="test-password">Password</Label>
                            <Input
                              id="test-password"
                              type="password"
                              value={testPassword}
                              onChange={(e) => setTestPassword(e.target.value)}
                              placeholder="Enter password"
                            />
                          </div>
                        </div>
                        <DialogFooter>
                          <Button
                            onClick={() => handleTestLogin(account)}
                            disabled={testingLogin === account.id}
                          >
                            {testingLogin === account.id ? (
                              <>
                                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                Testing...
                              </>
                            ) : (
                              'Test Login'
                            )}
                          </Button>
                        </DialogFooter>
                      </DialogContent>
                    </Dialog>
                  )}
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={() => handleDelete(account.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}