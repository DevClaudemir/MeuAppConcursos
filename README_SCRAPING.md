# 🕷️ Sistema de Scraping e Admin - Guia Completo

## 📋 O que foi implementado

### ✅ 1. Schema do Banco Atualizado
- Campos adicionados: `banca`, `ano`, `orgao`, `origem`, `hash_enunciado`
- Tabela `admins` para controle de acesso administrativo

### ✅ 2. Sistema de Scraping (`scraper_questoes.py`)
- **Adaptação automática de textos** para evitar direitos autorais
- **Detecção de duplicatas** via hash do enunciado
- **Extração de metadados**: banca, ano, órgão, cargo
- **Suporte a múltiplas fontes**: URLs, HTML bruto, PDFs convertidos

### ✅ 3. Painel Admin no App
- **Adicionar/Editar conteúdo teórico** por questão
- **Gerenciar questões**: visualizar, filtrar, deletar
- **Executar scraping** diretamente pela interface
- **Configurações**: tornar usuários admin

### ✅ 4. Detecção e Remoção de Duplicatas
- Identifica questões manuais duplicadas
- Remove automaticamente mantendo versões do scraping

---

## 🚀 Como Usar

### Passo 1: Atualizar o Banco
```bash
python database.py
```

### Passo 2: Criar um Admin
```bash
python criar_admin.py
```
Isso torna o primeiro usuário cadastrado em admin.

**OU** faça login no app e use a aba "Configurações" do painel admin para tornar outros usuários admin.

### Passo 3: Acessar o Painel Admin
1. Faça login no app (`streamlit run app_web.py`)
2. Clique em **"Acessar Admin"** na sidebar
3. Você terá acesso a 4 abas:
   - **📝 Conteúdo Teórico**: Adicionar explicações às questões
   - **🔍 Gerenciar Questões**: Ver estatísticas, filtrar, deletar
   - **🕷️ Scraping**: Executar scraping de URLs
   - **⚙️ Configurações**: Gerenciar admins

---

## 🕷️ Como Usar o Scraping

### Opção 1: Via Interface Web (Recomendado)
1. Acesse o **Painel Admin** → aba **"Scraping"**
2. Cole as URLs das questões (uma por linha)
3. Selecione o cargo (opcional)
4. Clique em **"Executar Scraping"**

### Opção 2: Via Script Python
```python
from scraper_questoes import ScraperQuestoes

scraper = ScraperQuestoes()

# Lista de URLs para processar
urls = [
    "https://exemplo.com/questao1",
    "https://exemplo.com/questao2",
]

# Processar (cargo_id é opcional)
sucesso, erros, duplicatas = scraper.processar_urls(
    urls, 
    cargo_id=1,  # ID do cargo ou None
    delay=2  # Delay entre requisições (segundos)
)

print(f"✅ {sucesso} salvas | ❌ {erros} erros | 🔄 {duplicatas} duplicatas")
```

### Opção 3: Processar HTML/Texto Bruto
```python
html_texto = """
1. Qual é a capital do Brasil?
A) São Paulo
B) Rio de Janeiro
C) Brasília
D) Belo Horizonte
"""

questoes = scraper.extrair_de_texto_bruto(
    html_texto,
    banca="CESPE",
    ano=2024,
    orgao="IBGE",
    materia="Geografia"
)

for q in questoes:
    scraper.salvar_questao(q, cargo_id=1)
```

---

## 🧹 Limpeza de Duplicatas

### Gerar Hash para Questões Antigas
```python
scraper = ScraperQuestoes()
scraper.marcar_questoes_manuais_para_remocao()
```

### Remover Duplicatas
```python
scraper.remover_duplicatas_manuais()
```

**OU** use o botão **"Remover Questões Manuais Duplicadas"** no painel admin.

---

## 📝 Adicionar Conteúdo Teórico

1. Acesse **Painel Admin** → **"Conteúdo Teórico"**
2. Selecione a questão pelo ID ou enunciado
3. Digite a explicação teórica (suporta **negrito** com `**texto**`)
4. Clique em **"Salvar Conteúdo Teórico"**

O conteúdo aparecerá automaticamente no modo revisão dos simulados!

---

## 🔧 Adaptação de Textos (Anti-Direitos Autorais)

O sistema adapta automaticamente os textos usando:
- **Substituições de sinônimos**: "de acordo com" → "conforme"
- **Variações de linguagem**: "assinale" → "marque"
- **Reformulação**: mantém o sentido, muda a forma
- **Hash para detecção**: evita duplicatas mesmo com adaptação

**Importante**: A adaptação é automática, mas você pode revisar manualmente no painel admin.

---

## 📊 Estrutura de Dados

Cada questão agora possui:
- `enunciado`: Texto da questão (adaptado)
- `op_a` a `op_e`: Alternativas (adaptadas)
- `correta`: Letra da resposta correta
- `materia`: Matéria/disciplina
- `banca`: CESPE, FGV, VUNESP, etc.
- `ano`: Ano da prova
- `orgao`: Órgão/instituição
- `origem`: "manual" ou "scraping"
- `hash_enunciado`: Hash para detecção de duplicatas
- `explicacao_teorica`: Conteúdo teórico (editável pelo admin)

---

## ⚠️ Importante

1. **Respeite os termos de uso** dos sites que você está fazendo scraping
2. **Use delays** entre requisições para não sobrecarregar servidores
3. **Revise as questões** coletadas antes de publicar
4. **Adaptação automática** ajuda, mas não substitui revisão manual
5. **Conteúdo teórico** deve ser adicionado manualmente por professores/admin

---

## 🎯 Próximos Passos Sugeridos

- Integrar com APIs de bancas (quando disponíveis)
- Sistema de OCR para PDFs de provas
- Machine Learning para melhorar adaptação de textos
- Exportação de questões em formatos padrão (QTI, etc.)
- Sistema de tags e categorização automática
