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