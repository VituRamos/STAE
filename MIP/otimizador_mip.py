import csv
import time
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpBinary, value, PULP_CBC_CMD

# CONFIGURAÇÕES DOS ARQUIVOS
ARQUIVO_MATRIZ = "matriz_distancias_bage.csv"
ARQUIVO_ESCOLAS = "escolas_simuladas.csv"
LIMITE_INALCANSAVEL = 900000 

# ==========================================
# CARREGAMENTO DOS DADOS 
# ==========================================
def carregar_dados():
    capacidades = {}
    with open(ARQUIVO_ESCOLAS, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for linha in reader:
            capacidades[linha['escola_id']] = int(linha['vagas'])

    matriz_tempo = {}
    escolas_set = set()
    with open(ARQUIVO_MATRIZ, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for linha in reader:
            aluno, escola = linha['aluno_id'], linha['escola_id']
            tempo = int(linha['tempo_segundos'])
            
            # Penalidade alta para rotas impossíveis direto na matriz
            if tempo >= LIMITE_INALCANSAVEL:
                tempo = 50000
                
            if aluno not in matriz_tempo:
                matriz_tempo[aluno] = {}
            matriz_tempo[aluno][escola] = tempo
            escolas_set.add(escola)
            
    return matriz_tempo, capacidades, list(matriz_tempo.keys()), list(escolas_set)

MATRIZ_TEMPO, CAPACIDADES, LISTA_ALUNOS, LISTA_ESCOLAS = carregar_dados()

# ==========================================
# MOTOR MATEMÁTICO (MIP via PuLP)
# ==========================================
if __name__ == "__main__":
    t_inicio = time.time()
    print("Construindo o modelo matemático...")

    # 1. Cria o problema de Minimização
    modelo = LpProblem("Otimizacao_Alocacao_Escolar", LpMinimize)

    # 2. Cria as variáveis de decisão x[aluno][escola] (Binárias 0 ou 1)
    # Ex: x['aluno_001']['Escola_Central_A']
    x = {}
    for a in LISTA_ALUNOS:
        x[a] = {}
        for e in LISTA_ESCOLAS:
            x[a][e] = LpVariable(f"aloca_{a}_{e}", cat=LpBinary)

    # 3. Função Objetivo: Somatório do (tempo * variável de alocação)
    modelo += lpSum(MATRIZ_TEMPO[a][e] * x[a][e] for a in LISTA_ALUNOS for e in LISTA_ESCOLAS), "Tempo_Total"

    # 4. Restrição 1: Cada aluno deve ser alocado a EXATAMENTE 1 escola
    for a in LISTA_ALUNOS:
        modelo += lpSum(x[a][e] for e in LISTA_ESCOLAS) == 1, f"Demanda_{a}"

    # 5. Restrição 2: O total de alunos em uma escola não pode exceder as vagas
    for e in LISTA_ESCOLAS:
        modelo += lpSum(x[a][e] for a in LISTA_ALUNOS) <= CAPACIDADES[e], f"Capacidade_{e}"

    # ==========================================
    # RESOLUÇÃO DO PROBLEMA
    # ==========================================
    print("Iniciando o Solver MIP...")
    # Usa o CBC (Solver open-source padrão do PuLP). msg=False oculta os logs do motor.
    modelo.solve(PULP_CBC_CMD(msg=False))

    # ==========================================
    # RELATÓRIO DOS RESULTADOS
    # ==========================================
    print("-" * 70)
    print("📋 RELATÓRIO DA SOLUÇÃO EXATA (MIP):")
    print("-" * 70)
    
    ocupacao_final = {e: 0 for e in LISTA_ESCOLAS}
    alunos_validos = 0
    alunos_isolados = 0
    tempo_valido_total = 0

    # Varre as variáveis para ver quais o Solver escolheu (valor == 1.0)
    for a in LISTA_ALUNOS:
        for e in LISTA_ESCOLAS:
            if value(x[a][e]) == 1.0:
                ocupacao_final[e] += 1
                tempo_real = MATRIZ_TEMPO[a][e]
                
                if tempo_real >= 50000: # Se for a penalidade
                    alunos_isolados += 1
                else:
                    tempo_valido_total += tempo_real
                    alunos_validos += 1

    for e in sorted(LISTA_ESCOLAS):
        print(f"-> {e.replace('_', ' ')}: {ocupacao_final[e]}/{CAPACIDADES[e]} vagas ocupadas.")

    print("-" * 70)
    print(f"🚌 Alunos transportados: {alunos_validos} de {len(LISTA_ALUNOS)}")
    print(f"⚠️ Alunos isolados geograficamente: {alunos_isolados}")
    tempo_medio = (tempo_valido_total / alunos_validos) / 60 if alunos_validos > 0 else 0
    print(f"⏱️ Tempo médio de deslocamento: {tempo_medio:.1f} minutos.")
    print(f"🚀 Otimização exata concluída em {time.time() - t_inicio:.2f} segundos.")