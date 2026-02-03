import customtkinter as ctk
import sqlite3
import sys

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class AppConcursos(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Meu Simulador de Concursos 2026")
        self.geometry("650x700")
        self.preparar_banco()
        self.timer_id = None
        self.modo_revisao = False
        self.mostrar_menu_inicial()

    def preparar_banco(self):
        conexao = sqlite3.connect('banco_questoes.db')
        cursor = conexao.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS historico 
                          (id INTEGER PRIMARY KEY AUTOINCREMENT, data TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
                          acertos INTEGER, total INTEGER, percentual REAL)''')
        conexao.commit()
        conexao.close()

    def mostrar_menu_inicial(self):
        if self.timer_id: self.after_cancel(self.timer_id)
        for widget in self.winfo_children(): widget.destroy()
        self.modo_revisao = False
        self.entradas_materias = {} # Guarda os campos de texto
        self.checks_materias = {}   # Guarda os checkboxes

        ctk.CTkLabel(self, text="CONFIGURAR SIMULADO", font=("Arial Bold", 24)).pack(pady=15)
        
        # Frame de instrução
        instrucao = ctk.CTkLabel(self, text="Selecione as matérias e a quantidade de questões:", font=("Arial", 14))
        instrucao.pack(pady=5)

        self.frame_scroll = ctk.CTkScrollableFrame(self, width=580, height=400)
        self.frame_scroll.pack(pady=10, padx=20, fill="both", expand=True)

        # Buscar matérias no banco
        conexao = sqlite3.connect('banco_questoes.db')
        cursor = conexao.cursor()
        cursor.execute('SELECT DISTINCT materia FROM questoes ORDER BY materia')
        materias = [row[0] for row in cursor.fetchall()]
        conexao.close()

        # Criar uma linha para cada matéria
        for mat in materias:
            linha = ctk.CTkFrame(self.frame_scroll, fg_color="transparent")
            linha.pack(pady=5, fill="x", padx=10)

            check = ctk.CTkCheckBox(linha, text=mat.upper(), width=250)
            check.pack(side="left")
            self.checks_materias[mat] = check

            entry = ctk.CTkEntry(linha, width=60, placeholder_text="Qtd")
            entry.insert(0, "5") # Sugestão padrão
            entry.pack(side="right")
            self.entradas_materias[mat] = entry

        # Botão de Ação Principal
        ctk.CTkButton(self, text="INICIAR SIMULADO PERSONALIZADO", 
                      fg_color="#1f538d", height=50, font=("Arial Bold", 16),
                      command=self.gerar_simulado_composto).pack(pady=15, padx=20, fill="x")

        ctk.CTkButton(self, text="VER MEU PROGRESSO (GRÁFICO)", fg_color="green", 
                      command=self.abrir_grafico).pack(pady=5)

    def gerar_simulado_composto(self):
        self.questoes = []
        conexao = sqlite3.connect('banco_questoes.db')
        cursor = conexao.cursor()

        for mat, check in self.checks_materias.items():
            if check.get() == 1: # Se estiver marcado
                try:
                    qtd = int(self.entradas_materias[mat].get())
                except:
                    qtd = 0
                
                if qtd > 0:
                    cursor.execute('SELECT enunciado, op_a, op_b, op_c, op_d, correta FROM questoes WHERE materia = ? ORDER BY RANDOM() LIMIT ?', (mat, qtd))
                    self.questoes.extend(cursor.fetchall())

        conexao.close()

        if not self.questoes:
            # Se nada foi selecionado, avisar o usuário (opcional)
            return

        import random
        random.shuffle(self.questoes) # Mistura as matérias para não vir tudo em bloco
        
        self.indice = 0
        self.acertos = 0
        self.respostas_usuario = [None] * len(self.questoes)
        self.montar_tela_questoes()

    def montar_tela_questoes(self):
        for widget in self.winfo_children(): widget.destroy()
        
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(pady=10, fill="x", padx=20)

        # Timer (120s agora)
        self.lbl_timer = ctk.CTkLabel(header, text="120s", font=("Arial Bold", 20), text_color="yellow")
        self.lbl_timer.pack(side="left")

        if not self.modo_revisao:
            ctk.CTkButton(header, text="SAIR E SALVAR", fg_color="#cc3300", width=100,
                          command=self.finalizar).pack(side="right")
        else:
            ctk.CTkButton(header, text="SAIR REVISÃO", fg_color="#3d3d3d", width=100,
                          command=self.finalizar).pack(side="right")

        self.lbl_pergunta = ctk.CTkLabel(self, text="", wraplength=550, font=("Arial", 18))
        self.lbl_pergunta.pack(pady=20)

        self.botoes_ops = {}
        for letra in ["A", "B", "C", "D"]:
            btn = ctk.CTkButton(self, text=letra, command=lambda l=letra: self.verificar(l))
            btn.pack(pady=8, padx=60, fill="x")
            self.botoes_ops[letra] = btn

        # Frame de Navegação (Setas)
        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.pack(pady=20, fill="x", padx=60)

        self.btn_ant = ctk.CTkButton(nav_frame, text="← ANTERIOR", width=120, command=self.questao_anterior)
        self.btn_ant.pack(side="left")

        self.btn_prox = ctk.CTkButton(nav_frame, text="PRÓXIMA →", width=120, command=self.proxima_manual)
        self.btn_prox.pack(side="right")
        
        self.atualizar_questao_tela()

    def atualizar_cronometro(self):
        if self.modo_revisao: return
        if self.tempo_restante > 0:
            self.tempo_restante -= 1
            self.lbl_timer.configure(text=f"{self.tempo_restante}s")
            if self.tempo_restante <= 15: self.lbl_timer.configure(text_color="red")
            self.timer_id = self.after(1000, self.atualizar_cronometro)
        else:
            self.verificar("TEMPO ESGOTADO")

    def atualizar_questao_tela(self):
        if self.timer_id: self.after_cancel(self.timer_id)
        
        q = self.questoes[self.indice]
        self.lbl_pergunta.configure(text=f"Questão {self.indice + 1} de {len(self.questoes)}:\n\n{q[0]}")
        
        opcoes = ["A", "B", "C", "D"]
        for i, letra in enumerate(opcoes):
            texto_op = f"{letra}) {q[i+1]}"
            self.botoes_ops[letra].configure(text=texto_op, fg_color=["#3a7ebf", "#1f538d"]) # Reset cor padrão

            # Se já respondeu ou está em revisão, mostrar cores
            resp = self.respostas_usuario[self.indice]
            correta = q[5]

            if self.modo_revisao or resp is not None:
                if letra == correta:
                    self.botoes_ops[letra].configure(fg_color="green")
                elif letra == resp:
                    self.botoes_ops[letra].configure(fg_color="red")
                
                # Desativa botões para não mudar a resposta
                self.botoes_ops[letra].configure(state="disabled")
            else:
                self.botoes_ops[letra].configure(state="normal")

        # Controle das setas
        self.btn_ant.configure(state="normal" if self.indice > 0 else "disabled")
        
        if not self.modo_revisao:
            self.tempo_restante = 120 # Novo tempo: 2 minutos
            self.lbl_timer.configure(text_color="yellow", text="120s")
            self.atualizar_cronometro()

    def verificar(self, escolha):
        if self.respostas_usuario[self.indice] is None:
            self.respostas_usuario[self.indice] = escolha
            if escolha == self.questoes[self.indice][5]:
                self.acertos += 1
            self.atualizar_questao_tela()
            # Espera 1 segundo para o usuário ver se acertou antes de pular
            self.after(1000, self.proxima_manual)

    def questao_anterior(self):
        if self.indice > 0:
            self.indice -= 1
            self.atualizar_questao_tela()

    def proxima_manual(self):
        if self.indice < len(self.questoes) - 1:
            self.indice += 1
            self.atualizar_questao_tela()
        elif not self.modo_revisao:
            self.finalizar()

    def finalizar(self):
        if self.timer_id: self.after_cancel(self.timer_id)
        
        # Filtra apenas o que foi respondido para não poluir a revisão
        self.questoes_respondidas = []
        self.respostas_efetivas = []
        
        for i, resp in enumerate(self.respostas_usuario):
            if resp is not None:
                self.questoes_respondidas.append(self.questoes[i])
                self.respostas_efetivas.append(resp)

        if not self.modo_revisao and len(self.respostas_efetivas) > 0:
            self.salvar_resultado_personalizado(len(self.respostas_efetivas))
            
        for widget in self.winfo_children(): widget.destroy()
        
        status_txt = "REVISÃO CONCLUÍDA" if self.modo_revisao else "SIMULADO FINALIZADO!"
        ctk.CTkLabel(self, text=status_txt, font=("Arial Bold", 22), text_color="#50fa7b").pack(pady=30)
        
        total_respondido = len(self.respostas_efetivas)
        if total_respondido > 0:
            percent = (self.acertos/total_respondido)*100
            ctk.CTkLabel(self, text=f"Você resolveu {total_respondido} questões.", font=("Arial", 18)).pack(pady=5)
            ctk.CTkLabel(self, text=f"Acertos: {self.acertos} ({percent:.1f}%)", font=("Arial", 18)).pack(pady=10)
            
            # Só mostra o botão de revisão se houver o que revisar
            ctk.CTkButton(self, text="REVISAR APENAS AS RESPONDIDAS", fg_color="#e67e22", 
                          command=self.iniciar_revisao_filtrada).pack(pady=10)
        else:
            ctk.CTkLabel(self, text="Nenhuma questão foi respondida.", font=("Arial", 18)).pack(pady=10)
        
        ctk.CTkButton(self, text="VOLTAR AO MENU", command=self.mostrar_menu_inicial).pack(pady=10)
        ctk.CTkButton(self, text="FECHAR", command=self.quit, fg_color="red").pack(pady=10)

    def iniciar_revisao_filtrada(self):
        # Substitui a lista de questões original apenas pelas que você respondeu
        self.questoes = self.questoes_respondidas
        self.respostas_usuario = self.respostas_efetivas
        self.modo_revisao = True
        self.indice = 0
        self.montar_tela_questoes()

    def salvar_resultado_personalizado(self, total):
        conexao = sqlite3.connect('banco_questoes.db')
        cursor = conexao.cursor()
        cursor.execute('INSERT INTO historico (acertos, total, percentual) VALUES (?, ?, ?)', 
                       (self.acertos, total, (self.acertos/total)*100))
        conexao.commit()
        conexao.close()

    def abrir_grafico(self):
        import subprocess
        subprocess.Popen([sys.executable, "grafico.py"])

if __name__ == "__main__":
    app = AppConcursos()
    app.mainloop()