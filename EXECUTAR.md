# 🚀 Script para Executar o Instagram-Telegram Bot

## 📋 Comando Único (Copie e Cole no Terminal)

```bash
cd /home/obushido/instaloader/instagram-telegram-bot && \
echo "🔄 Limpando processos anteriores..." && \
pkill -f "uvicorn" 2>/dev/null || true && \
pkill -f "next" 2>/dev/null || true && \
lsof -ti:8000 | xargs kill -9 2>/dev/null || true && \
lsof -ti:3000 | xargs kill -9 2>/dev/null || true && \
echo "📦 Iniciando Backend..." && \
cd /home/obushido/instaloader/instagram-telegram-bot/backend && \
([ ! -d "venv" ] && python3 -m venv venv || true) && \
source venv/bin/activate && \
pip install -q -r requirements.txt && \
nohup uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > ../backend.log 2>&1 & \
BACKEND_PID=$! && \
echo "✅ Backend rodando (PID: $BACKEND_PID)" && \
sleep 3 && \
cd /home/obushido/instaloader/instagram-telegram-bot/frontend && \
echo "🎨 Iniciando Frontend Next.js..." && \
npm install --silent && \
nohup npm run dev > ../frontend.log 2>&1 & \
FRONTEND_PID=$! && \
echo "✅ Frontend rodando (PID: $FRONTEND_PID)" && \
sleep 5 && \
echo "" && \
echo "🎉 APLICAÇÃO INICIADA COM SUCESSO!" && \
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" && \
echo "📌 Acesse:" && \
echo "   • Frontend: http://localhost:3000" && \
echo "   • API Docs: http://localhost:8000/docs" && \
echo "" && \
echo "📋 Logs salvos em:" && \
echo "   • /home/obushido/instaloader/instagram-telegram-bot/backend.log" && \
echo "   • /home/obushido/instaloader/instagram-telegram-bot/frontend.log" && \
echo "" && \
echo "🛑 Para parar tudo:" && \
echo "   pkill -f uvicorn && pkill -f next" && \
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" && \
echo "" && \
echo "📊 Verificando status dos serviços..." && \
curl -s http://localhost:8000/api/stats > /dev/null 2>&1 && echo "   ✅ Backend está respondendo" || echo "   ⚠️  Backend ainda iniciando..." && \
curl -s http://localhost:3000 > /dev/null 2>&1 && echo "   ✅ Frontend está respondendo" || echo "   ⚠️  Frontend ainda iniciando..."
```

## 🎯 Script Bash Completo (Alternativa Mais Robusta)

Crie um arquivo `start.sh` com o conteúdo abaixo:

```bash
#!/bin/bash

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Diretório base
BASE_DIR="/home/obushido/instaloader/instagram-telegram-bot"

# Função para limpar processos
cleanup() {
    echo -e "${YELLOW}🔄 Limpando processos anteriores...${NC}"
    pkill -f "uvicorn" 2>/dev/null || true
    pkill -f "next" 2>/dev/null || true
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true
    echo -e "${GREEN}✅ Processos limpos${NC}"
}

# Função para verificar porta
check_port() {
    local port=$1
    local service=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${GREEN}✅ $service rodando na porta $port${NC}"
        return 0
    else
        echo -e "${RED}❌ $service não está rodando na porta $port${NC}"
        return 1
    fi
}

# Trap para CTRL+C
trap 'echo -e "\n${YELLOW}🛑 Parando servidores...${NC}"; cleanup; exit 0' INT

# Limpar processos anteriores
cleanup

# Navegar para o diretório base
cd "$BASE_DIR" || { echo -e "${RED}❌ Diretório não encontrado: $BASE_DIR${NC}"; exit 1; }

# Iniciar Backend
echo -e "${BLUE}📦 Iniciando Backend (FastAPI)...${NC}"
cd backend || { echo -e "${RED}❌ Diretório backend não encontrado${NC}"; exit 1; }

# Criar e ativar venv
if [ ! -d "venv" ]; then
    echo "Criando ambiente virtual..."
    python3 -m venv venv
fi
source venv/bin/activate

# Instalar dependências
echo "Instalando dependências do backend..."
pip install -q -r requirements.txt

# Iniciar backend
nohup uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > ../backend.log 2>&1 &
BACKEND_PID=$!

# Aguardar backend iniciar
echo "Aguardando backend iniciar..."
for i in {1..10}; do
    if check_port 8000 "Backend" >/dev/null 2>&1; then
        break
    fi
    sleep 1
done
check_port 8000 "Backend"

# Iniciar Frontend
echo -e "${BLUE}🎨 Iniciando Frontend (Next.js)...${NC}"
cd "$BASE_DIR/frontend" || { echo -e "${RED}❌ Diretório frontend não encontrado${NC}"; exit 1; }

# Instalar dependências
echo "Instalando dependências do frontend..."
npm install --silent

# Iniciar frontend
nohup npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!

# Aguardar frontend iniciar
echo "Aguardando frontend iniciar..."
for i in {1..15}; do
    if check_port 3000 "Frontend" >/dev/null 2>&1; then
        break
    fi
    sleep 1
done
check_port 3000 "Frontend"

# Exibir informações finais
echo ""
echo -e "${GREEN}🎉 APLICAÇÃO INICIADA COM SUCESSO!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BLUE}📌 URLs de Acesso:${NC}"
echo "   • Frontend: http://localhost:3000"
echo "   • API Docs: http://localhost:8000/docs"
echo ""
echo -e "${BLUE}📋 Logs em tempo real:${NC}"
echo "   • Backend:  tail -f $BASE_DIR/backend.log"
echo "   • Frontend: tail -f $BASE_DIR/frontend.log"
echo ""
echo -e "${YELLOW}🛑 Para parar: Pressione CTRL+C${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Manter script rodando
wait $BACKEND_PID $FRONTEND_PID
```

Para usar o script:
```bash
chmod +x start.sh
./start.sh
```

## 🛑 Comandos Úteis

### Parar todos os serviços:
```bash
pkill -f uvicorn && pkill -f next
```

### Ver logs em tempo real:
```bash
# Backend
tail -f /home/obushido/instaloader/instagram-telegram-bot/backend.log

# Frontend
tail -f /home/obushido/instaloader/instagram-telegram-bot/frontend.log

# Ambos simultaneamente
tail -f /home/obushido/instaloader/instagram-telegram-bot/*.log
```

### Verificar se os serviços estão rodando:
```bash
# Verificar processos
ps aux | grep -E "(uvicorn|next)" | grep -v grep

# Verificar portas
lsof -i :8000  # Backend
lsof -i :3000  # Frontend
```

### Testar se os serviços estão respondendo:
```bash
# Backend
curl http://localhost:8000/api/stats

# Frontend
curl -I http://localhost:3000
```

## ⚠️ Troubleshooting

### Erro: "Port already in use"
```bash
# Limpar todas as portas
lsof -ti:8000 | xargs kill -9
lsof -ti:3000 | xargs kill -9
```

### Erro: "Module not found" no Backend
```bash
cd /home/obushido/instaloader/instagram-telegram-bot/backend
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Erro: "Cannot find module" no Frontend
```bash
cd /home/obushido/instaloader/instagram-telegram-bot/frontend
rm -rf node_modules package-lock.json
npm install
```

### Erro: "SyntaxError: Unexpected end of JSON input"
Este erro ocorre quando há requisições POST sem body. Já foi corrigido no código, mas se persistir:
```bash
# Reinicie os serviços
pkill -f uvicorn && pkill -f next
# Execute o comando único novamente
```

### Erro do Next.js 15: "params should be awaited"
Este erro já foi corrigido. Se aparecer em outros arquivos:
- Adicione `await` antes de acessar `params`
- Exemplo: `(await params).path` ao invés de `params.path`

## 🧪 Testando a Aplicação

1. **Acesse o Frontend**: http://localhost:3000
2. **Vá para Configurações**
3. **Adicione um perfil do Instagram**
4. **Use o botão de teste** (ícone de tubo de ensaio) para verificar o scraping

## 💡 Dicas

### Criar alias para facilitar:
```bash
echo 'alias instagram-bot="cd /home/obushido/instaloader/instagram-telegram-bot && ./start.sh"' >> ~/.bashrc
source ~/.bashrc
# Depois é só digitar: instagram-bot
```

### Monitorar recursos:
```bash
# Ver uso de CPU e memória dos processos
htop -p $(pgrep -d, -f "uvicorn|next")
```

### Logs com cores:
```bash
# Backend com destaque de erros
tail -f backend.log | grep --color -E "ERROR|WARNING|$"

# Frontend com destaque de erros
tail -f frontend.log | grep --color -E "error|Error|ERROR|$"
```

## 📝 Notas Importantes

- O backend roda na porta **8000**
- O frontend roda na porta **3000**
- Os logs são salvos na raiz do projeto
- As mídias baixadas são temporárias (24h)
- Use intervalos de checagem razoáveis (30+ minutos)

---

**Última atualização**: $(date)