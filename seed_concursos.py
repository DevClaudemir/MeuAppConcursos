"""
Script para popular concursos, cargos e questões de exemplo com conteúdo teórico.
Execute: python seed_concursos.py
"""
import sqlite3
import os

def seed():
    if not os.path.exists("banco_questoes.db"):
        print("Execute antes: python database.py")
        return

    conn = sqlite3.connect("banco_questoes.db")
    c = conn.cursor()

    # 1. Inserir concursos
    concursos = [
        ("Câmara dos Deputados",),
        ("SEFAZ PA",),
    ]
    c.executemany("INSERT OR IGNORE INTO concursos (nome) VALUES (?)", concursos)
    conn.commit()

    # Buscar IDs dos concursos
    c.execute("SELECT id, nome FROM concursos")
    concursos_map = {nome: id_ for id_, nome in c.fetchall()}

    # 2. Inserir cargos (concurso_id, nome)
    cargos_data = [
        (concursos_map["Câmara dos Deputados"], "Policial Legislativo"),
        (concursos_map["Câmara dos Deputados"], "Fiscal"),
        (concursos_map["SEFAZ PA"], "Fiscal de Receitas Estaduais"),
    ]
    for concurso_id, nome in cargos_data:
        c.execute("INSERT OR IGNORE INTO cargos (concurso_id, nome) VALUES (?, ?)", (concurso_id, nome))
    conn.commit()

    # Garantir que cargos existem (se já existiam, pegar os ids)

    c.execute("SELECT id, concurso_id, nome FROM cargos")
    cargos_list = c.fetchall()
    # (id, concurso_id, nome) -> mapear por (concurso_nome, cargo_nome)
    c.execute("SELECT id, nome FROM concursos")
    id_to_concurso = {id_: nome for id_, nome in c.fetchall()}
    cargos_map = {}
    for id_, concurso_id, nome in cargos_list:
        conc_nome = id_to_concurso[concurso_id]
        cargos_map[(conc_nome, nome)] = id_

    # 3. Questões de exemplo com explicacao_teorica (enunciado, op_a, op_b, op_c, op_d, correta, materia, explicacao_teorica)
    # Câmara - Policial Legislativo
    pol_leg = cargos_map[("Câmara dos Deputados", "Policial Legislativo")]
    questoes_pol = [
        (
            "De acordo com a Lei nº 8.112/90, o servidor público que agir com dolo ou culpa responderá por seus atos perante a administração. Isso se refere à responsabilidade:",
            "Penal", "Civil", "Administrativa", "Política",
            "C", "Direito Administrativo",
            "**Responsabilidade administrativa** é a obrigação do servidor de responder por atos que violem deveres funcionais. A Lei 8.112/90 (regime jurídico dos servidores federais) prevê sanções como advertência, suspensão e demissão. Dolo é a intenção de violar o dever; culpa é a negligência ou imprudência. A responsabilidade civil e penal independem da administrativa e podem ser aplicadas cumulativamente."
        ),
        (
            "O princípio da administração pública que exige transparência e divulgação dos atos é o da:",
            "Legalidade", "Impessoalidade", "Moralidade", "Publicidade",
            "D", "Direito Administrativo",
            "O **princípio da publicidade** (CF, art. 37) impõe que os atos da administração sejam públicos, salvo quando a lei exija sigilo. Transparência, divulgação em órgãos oficiais e acesso a informações (Lei 12.527/2011) decorrem desse princípio. Legalidade = atuar conforme a lei; Impessoalidade = tratar todos de forma isonômica; Moralidade = probidade e boa-fé."
        ),
        (
            "A Constituição Federal de 1988 é classificada como:",
            "Outorgada", "Promulgada", "Cesarista", "Dualista",
            "B", "Direito Constitucional",
            "A CF/88 é **promulgada** (ou democrática): foi elaborada por uma Assembleia Nacional Constituinte eleita e instalada após o fim do regime autoritário. Constituições **outorgadas** são impostas pelo governante (ex.: 1937, 1967). O termo 'promulgada' destaca que foi aprovada e promulgada pelo poder constituinte originário."
        ),
    ]
    for q in questoes_pol:
        c.execute("""
            INSERT INTO questoes (cargo_id, enunciado, op_a, op_b, op_c, op_d, correta, materia, explicacao_teorica)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (pol_leg, q[0], q[1], q[2], q[3], q[4], q[5], q[6], q[7]))

    # Câmara - Fiscal
    fiscal_camara = cargos_map[("Câmara dos Deputados", "Fiscal")]
    questoes_fiscal_c = [
        (
            "A modalidade de licitação utilizada para a venda de bens móveis inservíveis é o:",
            "Pregão", "Convite", "Leilão", "Concurso",
            "C", "Direito Administrativo",
            "O **Leilão** (Lei 14.133/2021) é a modalidade de licitação para venda de bens móveis inservíveis ou para alienação de bens imóveis. Pregão é para compras e serviços comuns; Convite é para obras/serviços de pequeno valor; Concurso é para escolha de trabalho técnico, científico ou artístico."
        ),
        (
            "O prazo de validade de um concurso público pode ser de até:",
            "1 ano", "2 anos", "5 anos", "10 anos",
            "B", "Direito Administrativo",
            "O **prazo de validade do concurso** é de até **2 anos** (CF, art. 37, III), prorrogável uma vez por igual período. O edital deve estabelecer esse prazo. Após a nomeação, o candidato aprovado tem o direito subjetivo à nomeação dentro do prazo de validade."
        ),
    ]
    for q in questoes_fiscal_c:
        c.execute("""
            INSERT INTO questoes (cargo_id, enunciado, op_a, op_b, op_c, op_d, correta, materia, explicacao_teorica)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (fiscal_camara, q[0], q[1], q[2], q[3], q[4], q[5], q[6], q[7]))

    # SEFAZ PA - Fiscal de Receitas Estaduais
    fiscal_sefaz = cargos_map[("SEFAZ PA", "Fiscal de Receitas Estaduais")]
    questoes_sefaz = [
        (
            "Na sistemática do ICMS, a operação em que a base de cálculo é o valor da operação de circulação da mercadoria denomina-se:",
            "Tributação pelo valor agregado", "Tributação na origem", "Tributação no destino", "Tributação por substituição tributária",
            "A", "Direito Tributário",
            "O ICMS é um imposto **sobre o valor da operação de circulação** (valor agregado). A base de cálculo é o valor da operação (art. 13 do LC 87/96). Tributação na origem/destino refere-se ao momento e ao local do fato gerador; substituição tributária é quando um contribuinte recolhe o imposto devido por outros."
        ),
        (
            "Assinale a alternativa em que todos os vocábulos estejam acentuados pela mesma regra:",
            "vênus, hífen, fáceis", "saúde, egoísmo, atribuí-lo", "têm, convêm, mantém", "público, parágrafo, ética",
            "D", "Português",
            "Em **D**, todas as palavras são paroxítonas terminadas em **-o** e **-a** (público, parágrafo, ética), acentuadas pela regra das paroxítonas. Em A e B há mistura de regras (oxítonas, paroxítonas); em C, 'têm' e 'convêm' são formas verbais (acento diferencial). A regra das paroxítonas é uma das mais cobradas em concursos."
        ),
        (
            "Qual o valor de x na equação 2x + 10 = 30?",
            "5", "10", "15", "20",
            "B", "Matemática",
            "**Resolução:** 2x + 10 = 30 → 2x = 30 - 10 → 2x = 20 → x = 10. Isolamos a incógnita realizando a mesma operação nos dois membros (princípio da equivalência). Em concursos de nível médio, equações do 1º grau e interpretação de problemas são muito cobradas."
        ),
    ]
    for q in questoes_sefaz:
        c.execute("""
            INSERT INTO questoes (cargo_id, enunciado, op_a, op_b, op_c, op_d, correta, materia, explicacao_teorica)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (fiscal_sefaz, q[0], q[1], q[2], q[3], q[4], q[5], q[6], q[7]))

    conn.commit()
    conn.close()
    print("Seed concluído: 2 concursos, 3 cargos e questões de exemplo com conteúdo teórico inseridos.")

if __name__ == "__main__":
    seed()
