# 🚀 SimuConcursos 2026

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![CustomTkinter](https://img.shields.io/badge/UI-CustomTkinter-blue?style=for-the-badge)
![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white)

O **SimuConcursos 2026** é um simulador de questões para concursos públicos desenvolvido em Python. O projeto permite a criação de simulados personalizados por matéria, controle de tempo e acompanhamento de desempenho através de gráficos.

## ✨ Funcionalidades

- **Simulados Personalizados**: Escolha quais matérias quer estudar e a quantidade exata de questões para cada uma.
- **Cronômetro Inteligente**: Controle de 120 segundos por questão para treinar agilidade.
- **Modo Revisão**: Após o término, revise apenas as questões que você respondeu, visualizando os erros e acertos com destaque visual.
- **Dashboard de Progresso**: Gráficos integrados que mostram sua evolução histórica de acertos.
- **Navegação Intuitiva**: Sistema de setas para avançar ou retroceder entre as questões durante a resolução ou revisão.

## 🛠️ Tecnologias Utilizadas

- **Linguagem**: Python 3.10+
- **Interface Gráfica**: `CustomTkinter` (Interface Moderna/Dark Mode)
- **Banco de Dados**: `SQLite3` (Armazenamento local de questões e histórico)
- **Visualização de Dados**: `Matplotlib` e `Pandas` para geração de gráficos.

## 🚀 Como Executar o Projeto

1. **Clone o repositório**:
   git clone [https://github.com/DevClaudemir/MeuAppConcursos.git](https://github.com/DevClaudemir/MeuAppConcursos.git)
   cd MeuAppConcursos
2. **Crie e ative o ambiente virtual (Recomendado):**
    python -m venv venv
    # No Windows:
    .\venv\Scripts\activate
3. **Instale as dependências:**
    pip install customtkinter matplotlib pandas
4. **Execute o aplicativo:**
    python main_app.py
📂 Estrutura de Arquivos
    main_app.py: O núcleo do simulador.
    grafico.py: Módulo responsável pela visualização de desempenho.
    banco_questoes.db: Banco de dados contendo as questões e o histórico de resultados.
    importar_planilha.py: Script para alimentação em massa do banco via CSV.

Desenvolvido por DevClaudemir 🎯