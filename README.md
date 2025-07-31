# Instagram to Telegram Bot

Bot automatizado que monitora perfis do Instagram e envia conteúdos (posts e stories) para um canal do Telegram via webhook N8N.

⚠️ **Importante**: Este bot agora suporta autenticação do Instagram para evitar limites de taxa. Configure uma conta do Instagram nas configurações para melhor desempenho.

## 🚀 Funcionalidades

- ✅ Download automático de posts e stories do Instagram
- ✅ Interface web moderna com React e shadcn/ui
- ✅ Logs em tempo real via WebSocket
- ✅ Múltiplos perfis com configurações individuais
- ✅ Integração com N8N via webhook
- ✅ Armazenamento em SQLite (portável)
- ✅ Limpeza automática de mídias antigas
- ✅ Autenticação do Instagram para evitar limites de taxa
- ✅ Gerenciamento de sessões do Instagram

## 🛠️ Stack Tecnológica

### Backend
- FastAPI (Python)
- SQLModel (ORM)
- Instaloader (Scraping)
- APScheduler (Tarefas agendadas)
- SQLite (Banco de dados)

### Frontend
- Next.js 15 + TypeScript
- React 19
- shadcn/ui (Componentes)
- TailwindCSS
- React Query

## 📦 Instalação Local

### Pré-requisitos
- Python 3.9+
- Node.js 18+
- npm ou yarn

### Backend
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Script de Inicialização Rápida
```bash
# Na raiz do projeto
./start.sh
```

## 🚀 Deploy no Railway

1. Fork este repositório
2. Conecte sua conta Railway ao GitHub
3. Crie um novo projeto no Railway
4. Adicione os serviços:
   - Backend: Selecione o diretório `/backend`
   - Frontend: Selecione o diretório `/frontend`
5. Configure as variáveis de ambiente:
   - Backend: 
     - `BASE_URL` (URL do backend deployado)
     - `FRONTEND_URL` (URL do frontend deployado)
   - Frontend: 
     - `NEXT_PUBLIC_API_URL` (URL do backend)
6. Configure volumes para persistência:
   - `/app/media` - Armazenamento de mídia
   - `/app/sessions` - Sessões do Instagram
   - `/app/database` - Banco de dados SQLite

## 📝 Configuração

### 1. Interface Web
Acesse a interface web para:
- **Profiles**: Adicionar perfis do Instagram para monitorar
- **Instagram Accounts**: Configurar conta do Instagram para autenticação
- **Config**: Configurar URL do webhook N8N e outras opções
- **Logs**: Visualizar logs em tempo real

### 2. Autenticação do Instagram
1. Vá para "Instagram Accounts"
2. Adicione sua conta do Instagram
3. Teste o login para criar uma sessão
4. A sessão será usada automaticamente para scraping

### 3. Webhook N8N
O bot envia dados no seguinte formato:
```json
{
  "profile": "username",
  "type": "post|story",
  "caption": "Texto do post",
  "timestamp": "2025-01-31T10:00:00Z",
  "media": {
    "url": "https://bot.com/media/file.jpg",
    "type": "image|video",
    "expires_at": "2025-01-31T11:00:00Z"
  }
}
```

### 4. Configuração N8N
No N8N, crie um workflow com:
1. Webhook node para receber os dados
2. HTTP Request node para baixar a mídia
3. Telegram node para enviar ao canal

## ⚠️ Avisos Importantes

- Este bot faz scraping de perfis **públicos** do Instagram
- Use intervalos de checagem razoáveis (30+ minutos) para evitar bloqueios
- As mídias são temporárias e deletadas após 24 horas
- Respeite os termos de uso do Instagram
- **Autenticação**: Configure uma conta do Instagram para evitar limites severos
- **Rate Limits**: Mesmo com autenticação, o Instagram pode impor limites
- **Segurança**: As senhas são criptografadas com bcrypt

## 📊 Monitoramento

- Dashboard com estatísticas em tempo real
- Logs detalhados com níveis (info, warning, error)
- WebSocket para atualizações instantâneas

## 🔧 Desenvolvimento

### Estrutura do Projeto
```
instagram-telegram-bot/
├── frontend/          # Next.js app
├── backend/           # FastAPI app
├── railway.json       # Config Railway
├── start.sh          # Script de inicialização
├── .env.example      # Exemplo de variáveis de ambiente
└── README.md
```

### Comandos Úteis
```bash
# Backend - Criar tabelas do banco
cd backend
python -c "from app.database import create_db_and_tables; create_db_and_tables()"

# Backend - Executar em produção
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Frontend - Build produção
cd frontend
npm run build
npm start

# Inicialização rápida (desenvolvimento)
./start.sh
```

## 🔒 Segurança

- Senhas do Instagram são criptografadas com bcrypt
- Sessões são armazenadas localmente no servidor
- URLs de mídia temporárias expiram após o download
- CORS configurado para origens específicas

## 📄 Licença

MIT License - veja [LICENSE](LICENSE) para detalhes.