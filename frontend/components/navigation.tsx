'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Home, Settings, FileText, Instagram, User } from 'lucide-react';
import { cn } from '@/lib/utils';

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Contas Instagram', href: '/instagram-accounts', icon: User },
  { name: 'Configurações', href: '/config', icon: Settings },
  { name: 'Logs', href: '/logs', icon: FileText },
];

export function Navigation() {
  const pathname = usePathname();

  return (
    <div className="border-b">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Instagram className="h-8 w-8 text-primary" />
            <h1 className="text-2xl font-bold">Instagram to Telegram Bot</h1>
          </div>
          
          <nav className="flex gap-6">
            {navigation.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    'flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-md transition-colors',
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:text-foreground hover:bg-muted'
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </div>
      </div>
    </div>
  );
}