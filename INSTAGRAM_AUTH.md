# Autenticação do Instagram

## Visão Geral

O bot agora suporta autenticação com contas do Instagram para evitar as limitações severas do acesso anônimo.

## Configuração

### 1. Adicionar Conta Instagram

1. Acesse a página "Contas Instagram" no frontend
2. Clique em "Add Account"
3. Insira o username e senha da conta Instagram
4. Clique em "Create Account"

### 2. Fazer Login

1. Na lista de contas, clique em "Test Login" 
2. Digite a senha novamente (por segurança)
3. O bot fará login e salvará a sessão

### 3. Verificar Status

- **Session: Valid** - A conta está logada e pronta
- **Session: Invalid** - É necessário fazer login novamente

## Benefícios da Autenticação

- **Menos Rate Limits**: Contas autenticadas têm limites muito mais altos
- **Acesso a Stories**: Stories só são acessíveis com autenticação
- **Maior Estabilidade**: Menos erros 401 e timeouts
- **Sessão Persistente**: Login é salvo e reutilizado automaticamente

## Segurança

- Senhas são criptografadas com bcrypt no banco de dados
- Sessões são salvas em arquivos locais
- Cada conta pode ser ativada/desativada individualmente

## Teste Manual

Para testar o login via linha de comando:

```bash
cd backend
python test_login.py
```

## Troubleshooting

### Login Falha
- Verifique se as credenciais estão corretas
- Aguarde alguns minutos se houver muitas tentativas
- Tente em outro horário se o Instagram bloquear

### Sessão Expira
- Faça login novamente pela interface
- O bot tentará usar a sessão salva automaticamente

### Rate Limits Persistem
- Mesmo autenticado, o Instagram tem limites
- Aguarde entre requisições
- Use intervalos maiores entre checks