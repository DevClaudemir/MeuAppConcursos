# 💳 Sistema de Assinaturas e Admin - Guia Completo

## 🎯 O que foi implementado

### ✅ 1. Sistema de Admin (Apenas Dono)
- **Apenas você é admin** - usuários não podem se tornar admin
- Configure seu usuário admin em `config.py` → `ADMIN_DONO = "seu_usuario"`
- Painel admin completo para gerenciar tudo

### ✅ 2. Sistema de Assinaturas (R$ 5/mês)
- **Bloqueio automático** para não assinantes
- Tela de assinatura com opções de pagamento
- Gerenciamento completo de assinaturas no painel admin
- Ativação manual pelo admin

### ✅ 3. Sistema de Comentários
- Usuários podem comentar questões durante a revisão
- Admin pode gerenciar/comentar/deletar comentários
- Comentários visíveis para todos os assinantes

---

## 🚀 Como Configurar

### Passo 1: Configure seu usuário admin

1. Abra `config.py` e altere:
   ```python
   ADMIN_DONO = "seu_usuario"  # <-- Coloque seu nome de usuário aqui
   ```

2. Crie sua conta no app (se ainda não tiver):
   ```bash
   streamlit run app_web.py
   ```
   - Vá em "Criar Conta" → crie com o nome que você colocou em `ADMIN_DONO`

3. Execute o script para tornar-se admin:
   ```bash
   python configurar_admin_dono.py
   ```

### Passo 2: Atualize o banco de dados
```bash
python database.py
```

---

## 💳 Como Funciona o Sistema de Assinaturas

### Para Usuários:
1. **Cadastro**: Criar conta normalmente
2. **Login**: Fazer login
3. **Bloqueio**: Se não tiver assinatura, aparece tela de assinatura
4. **Assinar**: Clicar em "Assinar Agora" → escolher meses → método de pagamento
5. **Ativação**: Admin ativa manualmente (por enquanto) ou integração futura com gateway

### Para Admin (Você):
1. **Ativar Assinatura Manualmente**:
   - Painel Admin → aba "💳 Assinaturas"
   - Selecionar usuário → meses → "Ativar Assinatura"
   
2. **Ver Estatísticas**:
   - Total de assinaturas
   - Assinaturas ativas/expiradas
   - Lista completa de assinantes

---

## 📝 Funcionalidades do Painel Admin

### Aba 1: 📝 Conteúdo Teórico
- Adicionar/editar explicações teóricas nas questões
- Buscar questões sem conteúdo teórico

### Aba 2: 🔍 Gerenciar Questões
- Ver estatísticas (total, sem teoria, do scraping, manuais)
- Filtrar questões
- Deletar questões

### Aba 3: 🕷️ Scraping
- Executar scraping de URLs
- Remover duplicatas

### Aba 4: 💳 Assinaturas
- Ver estatísticas de assinaturas
- Ativar assinaturas manualmente
- Listar todas as assinaturas

### Aba 5: 💬 Comentários
- Ver todos os comentários
- Deletar comentários

---

## 💬 Sistema de Comentários

### Para Usuários:
- Durante a **revisão** de questões (após finalizar simulado)
- Ver comentários de outros usuários
- Adicionar seus próprios comentários
- Comentários ficam públicos para todos os assinantes

### Para Admin:
- Ver todos os comentários em "💬 Comentários"
- Deletar comentários inadequados
- Gerenciar conteúdo

---

## 🔒 Segurança

- **Apenas você é admin** - não há como usuários se tornarem admin
- **Assinaturas obrigatórias** - acesso bloqueado sem assinatura ativa
- **Hash de senhas** - senhas são criptografadas
- **Validação de assinaturas** - verificação automática de data de expiração

---

## 📊 Estrutura do Banco de Dados

### Tabela `assinaturas`:
- `usuario_id`: ID do usuário
- `data_inicio`: Data de início
- `data_fim`: Data de término
- `valor_pago`: Valor pago (R$ 5.00/mês)
- `status`: 'ativa' ou 'expirada'
- `metodo_pagamento`: Método usado

### Tabela `comentarios_questoes`:
- `questao_id`: ID da questão
- `usuario_id`: ID do usuário que comentou
- `comentario`: Texto do comentário
- `data_criacao`: Data/hora do comentário

---

## 🎨 Próximos Passos (Opcional)

1. **Integração com Gateway de Pagamento**:
   - Mercado Pago
   - PagSeguro
   - Stripe

2. **Renovação Automática**:
   - Assinaturas recorrentes
   - Notificações de expiração

3. **Relatórios**:
   - Receita mensal
   - Usuários mais ativos
   - Questões mais comentadas

---

## ⚠️ Importante

- **Configure `config.py`** antes de usar
- **Execute `configurar_admin_dono.py`** após criar sua conta
- **Assinaturas são ativadas manualmente** por enquanto (integração futura)
- **Apenas você pode ser admin** - sistema de segurança implementado
