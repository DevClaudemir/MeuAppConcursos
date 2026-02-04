"""
Sistema de Scraping de Questões de Concursos
Coleta questões de sites públicos e adapta para evitar direitos autorais
"""
import sqlite3
import requests
from bs4 import BeautifulSoup
import re
import time
import hashlib
from urllib.parse import urljoin, urlparse
import random

class ScraperQuestoes:
    def __init__(self, db_path="banco_questoes.db"):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def gerar_hash_enunciado(self, texto):
        """Gera hash do enunciado para detectar duplicatas"""
        texto_limpo = re.sub(r'\s+', ' ', texto.lower().strip())
        return hashlib.md5(texto_limpo.encode()).hexdigest()

    def adaptar_texto(self, texto):
        """
        Adapta o texto para evitar direitos autorais.
        Técnicas: sinônimos, reordenação, paráfrase simples
        """
        if not texto:
            return texto
        
        # Normaliza espaços
        texto = re.sub(r'\s+', ' ', texto.strip())
        
        # Substituições comuns para adaptação
        substituicoes = {
            'de acordo com': 'conforme',
            'assinale a alternativa': 'marque a opção',
            'é correto afirmar': 'pode-se afirmar corretamente',
            'é incorreto afirmar': 'não se pode afirmar corretamente',
            'julgue os itens': 'avalie os itens',
            'com relação a': 'acerca de',
            'no que se refere a': 'quanto a',
        }
        
        texto_adaptado = texto
        for original, substituto in substituicoes.items():
            texto_adaptado = re.sub(
                re.escape(original), 
                substituto, 
                texto_adaptado, 
                flags=re.IGNORECASE
            )
        
        # Pequenas variações para evitar cópia exata
        # Se o texto for muito similar ao original, adiciona pequenas modificações
        if texto_adaptado == texto:
            # Adiciona variações sutis
            texto_adaptado = texto_adaptado.replace(' o ', ' o(a) ').replace(' a ', ' a(o) ')
            texto_adaptado = texto_adaptado.replace('é', 'é considerado').replace('são', 'são considerados')
        
        return texto_adaptado[:len(texto) + 50]  # Limita tamanho

    def extrair_questao_pci(self, url):
        """
        Extrai questão do PCI Concursos (exemplo de site público)
        Formato adaptável para outros sites
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Estrutura típica de sites de questões
            questao = {
                'enunciado': '',
                'op_a': '',
                'op_b': '',
                'op_c': '',
                'op_d': '',
                'op_e': '',
                'correta': '',
                'materia': '',
                'banca': '',
                'ano': None,
                'orgao': '',
            }
            
            # Tenta encontrar enunciado (ajuste conforme estrutura do site)
            enunciado_elem = soup.find('div', class_=re.compile('enunciado|questao|pergunta', re.I))
            if not enunciado_elem:
                enunciado_elem = soup.find('p', class_=re.compile('enunciado|questao', re.I))
            if enunciado_elem:
                questao['enunciado'] = enunciado_elem.get_text(strip=True)
            
            # Tenta encontrar alternativas
            alternativas = soup.find_all(['li', 'div', 'p'], class_=re.compile('alternativa|opcao|resposta', re.I))
            if alternativas:
                for i, alt in enumerate(alternativas[:5]):
                    texto = alt.get_text(strip=True)
                    if texto.startswith(('a)', 'A)', '(a)', '(A)')):
                        questao['op_a'] = re.sub(r'^[aA]\)\s*', '', texto)
                    elif texto.startswith(('b)', 'B)', '(b)', '(B)')):
                        questao['op_b'] = re.sub(r'^[bB]\)\s*', '', texto)
                    elif texto.startswith(('c)', 'C)', '(c)', '(C)')):
                        questao['op_c'] = re.sub(r'^[cC]\)\s*', '', texto)
                    elif texto.startswith(('d)', 'D)', '(d)', '(D)')):
                        questao['op_d'] = re.sub(r'^[dD]\)\s*', '', texto)
                    elif texto.startswith(('e)', 'E)', '(e)', '(E)')):
                        questao['op_e'] = re.sub(r'^[eE]\)\s*', '', texto)
            
            # Tenta encontrar gabarito
            gabarito_elem = soup.find(['div', 'span', 'p'], class_=re.compile('gabarito|resposta.*correta|correta', re.I))
            if gabarito_elem:
                texto_gab = gabarito_elem.get_text(strip=True).upper()
                match = re.search(r'([A-E])', texto_gab)
                if match:
                    questao['correta'] = match.group(1)
            
            # Metadados
            meta = soup.find_all(['span', 'div'], class_=re.compile('meta|info|dados', re.I))
            for m in meta:
                texto = m.get_text(strip=True)
                if re.search(r'banca|organizadora', texto, re.I):
                    questao['banca'] = re.sub(r'.*banca.*?:?\s*', '', texto, flags=re.I).strip()
                if re.search(r'ano|20\d{2}', texto):
                    ano_match = re.search(r'(20\d{2}|\d{4})', texto)
                    if ano_match:
                        questao['ano'] = int(ano_match.group(1))
                if re.search(r'órgão|orgao|instituição', texto, re.I):
                    questao['orgao'] = re.sub(r'.*órgão.*?:?\s*', '', texto, flags=re.I).strip()
            
            return questao if questao['enunciado'] else None
            
        except Exception as e:
            print(f"Erro ao extrair questão de {url}: {e}")
            return None

    def extrair_de_texto_bruto(self, texto_html, banca="", ano=None, orgao="", materia=""):
        """
        Extrai questões de HTML/texto bruto (útil para PDFs convertidos ou HTML simples)
        """
        soup = BeautifulSoup(texto_html, 'html.parser')
        questoes = []
        
        # Padrão comum: questões numeradas
        padrao_questao = re.compile(r'^\d+[\.\)]\s*(.+?)(?=\d+[\.\)]|$)', re.DOTALL | re.MULTILINE)
        matches = padrao_questao.findall(texto_html)
        
        for match in matches:
            texto_questao = match.strip()
            if len(texto_questao) < 50:  # Muito curto, provavelmente não é questão
                continue
            
            questao = {
                'enunciado': '',
                'op_a': '',
                'op_b': '',
                'op_c': '',
                'op_d': '',
                'op_e': '',
                'correta': '',
                'materia': materia,
                'banca': banca,
                'ano': ano,
                'orgao': orgao,
            }
            
            # Separa enunciado e alternativas
            linhas = texto_questao.split('\n')
            enunciado_parts = []
            alternativas = {}
            
            for linha in linhas:
                linha = linha.strip()
                if not linha:
                    continue
                
                # Detecta alternativas
                match_alt = re.match(r'^([A-E])[\.\)]\s*(.+)$', linha, re.I)
                if match_alt:
                    letra = match_alt.group(1).upper()
                    texto = match_alt.group(2)
                    alternativas[letra] = texto
                else:
                    # É parte do enunciado
                    enunciado_parts.append(linha)
            
            if not enunciado_parts or len(alternativas) < 4:
                continue
            
            questao['enunciado'] = ' '.join(enunciado_parts)
            questao['op_a'] = alternativas.get('A', '')
            questao['op_b'] = alternativas.get('B', '')
            questao['op_c'] = alternativas.get('C', '')
            questao['op_d'] = alternativas.get('D', '')
            questao['op_e'] = alternativas.get('E', '')
            
            questoes.append(questao)
        
        return questoes

    def salvar_questao(self, questao, cargo_id=None):
        """Salva questão no banco, evitando duplicatas"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Adapta textos
        enunciado_adaptado = self.adaptar_texto(questao['enunciado'])
        hash_enunciado = self.gerar_hash_enunciado(enunciado_adaptado)
        
        # Verifica duplicata
        existe = c.execute(
            "SELECT id FROM questoes WHERE hash_enunciado = ?",
            (hash_enunciado,)
        ).fetchone()
        
        if existe:
            conn.close()
            return False, "Questão duplicada"
        
        # Salva
        try:
            c.execute("""
                INSERT INTO questoes (
                    cargo_id, enunciado, op_a, op_b, op_c, op_d, op_e,
                    correta, materia, banca, ano, orgao, origem, hash_enunciado
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'scraping', ?)
            """, (
                cargo_id,
                enunciado_adaptado,
                self.adaptar_texto(questao.get('op_a', '')),
                self.adaptar_texto(questao.get('op_b', '')),
                self.adaptar_texto(questao.get('op_c', '')),
                self.adaptar_texto(questao.get('op_d', '')),
                self.adaptar_texto(questao.get('op_e', '')),
                questao.get('correta', ''),
                questao.get('materia', ''),
                questao.get('banca', ''),
                questao.get('ano'),
                questao.get('orgao', ''),
                hash_enunciado
            ))
            conn.commit()
            conn.close()
            return True, "Questão salva"
        except Exception as e:
            conn.close()
            return False, f"Erro: {e}"

    def processar_urls(self, urls, cargo_id=None, delay=2):
        """Processa múltiplas URLs com delay entre requisições"""
        sucesso = 0
        erros = 0
        duplicatas = 0
        
        for url in urls:
            questao = self.extrair_questao_pci(url)
            if questao and questao['enunciado']:
                ok, msg = self.salvar_questao(questao, cargo_id)
                if ok:
                    sucesso += 1
                    print(f"✓ Questão salva: {url[:50]}...")
                elif "duplicada" in msg.lower():
                    duplicatas += 1
                else:
                    erros += 1
                    print(f"✗ Erro: {msg}")
            else:
                erros += 1
            
            time.sleep(delay)  # Respeita o servidor
        
        return sucesso, erros, duplicatas

    def marcar_questoes_manuais_para_remocao(self):
        """Marca questões manuais (sem hash) para possível remoção"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Gera hash para questões antigas sem hash
        c.execute("SELECT id, enunciado FROM questoes WHERE hash_enunciado IS NULL")
        questoes_sem_hash = c.fetchall()
        
        for qid, enunciado in questoes_sem_hash:
            hash_enunciado = self.gerar_hash_enunciado(enunciado)
            c.execute(
                "UPDATE questoes SET hash_enunciado = ?, origem = 'manual' WHERE id = ?",
                (hash_enunciado, qid)
            )
        
        conn.commit()
        conn.close()
        print(f"Hash gerado para {len(questoes_sem_hash)} questões manuais")

    def remover_duplicatas_manuais(self):
        """Remove questões manuais que são duplicatas de questões com scraping"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Encontra duplicatas: mesmo hash, mas uma é manual e outra é scraping
        c.execute("""
            SELECT q1.id, q1.origem, q2.id, q2.origem
            FROM questoes q1
            JOIN questoes q2 ON q1.hash_enunciado = q2.hash_enunciado
            WHERE q1.id < q2.id
            AND (q1.origem = 'manual' OR q2.origem = 'manual')
        """)
        
        duplicatas = c.fetchall()
        ids_para_remover = []
        
        for q1_id, q1_origem, q2_id, q2_origem in duplicatas:
            # Remove a manual, mantém a do scraping (ou a primeira se ambas forem manuais)
            if q1_origem == 'manual':
                ids_para_remover.append(q1_id)
            elif q2_origem == 'manual':
                ids_para_remover.append(q2_id)
        
        if ids_para_remover:
            c.executemany("DELETE FROM questoes WHERE id = ?", [(id_,) for id_ in ids_para_remover])
            conn.commit()
            print(f"Removidas {len(ids_para_remover)} questões manuais duplicadas")
        else:
            print("Nenhuma duplicata encontrada")
        
        conn.close()

if __name__ == "__main__":
    scraper = ScraperQuestoes()
    
    # Exemplo de uso
    print("=== Sistema de Scraping de Questões ===")
    print("\n1. Gerando hash para questões manuais existentes...")
    scraper.marcar_questoes_manuais_para_remocao()
    
    print("\n2. Removendo duplicatas (mantém questões do scraping)...")
    scraper.remover_duplicatas_manuais()
    
    print("\n=== Para usar o scraper ===")
    print("Exemplo:")
    print("  scraper = ScraperQuestoes()")
    print("  urls = ['https://exemplo.com/questao1', 'https://exemplo.com/questao2']")
    print("  sucesso, erros, duplicatas = scraper.processar_urls(urls, cargo_id=1)")
    
    def verificar_dados():
        conn = sqlite3.connect("banco_questoes.db")
        c = conn.cursor()
    
    # 1. Verificar se a tabela existe
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='questoes'")
        if not c.fetchone():
            print("❌ ERRO: A tabela 'questoes' não existe no banco!")
            return

    # 2. Contar questões totais
        total = c.execute("SELECT COUNT(*) FROM questoes").fetchone()[0]
        print(f"📊 Total de questões no banco: {total}")

    # 3. Ver matérias encontradas
        materias = c.execute("SELECT DISTINCT materia FROM questoes").fetchall()
        print(f"📚 Matérias registradas: {[m[0] for m in materias]}")
    
        conn.close()

if __name__ == "__main__":
    verificar_dados()