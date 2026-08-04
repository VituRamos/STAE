import csv
import random
import time

# CONFIGURAÇÕES DOS ARQUIVOS
ARQUIVO_MATRIZ = "matriz_distancias_bage.csv"
ARQUIVO_ESCOLAS = "escolas_simuladas.csv"

# PARÂMETROS DO ALGORITMO (Otimizados para preservação de restrições)
TAMANHO_POPULACAO = 60
NUM_GERACOES = 500
TAXA_MUTACAO = 0.30       # 30% de chance de ocorrer troca de alunos
LIMITE_INALCANSAVEL = 900000 # Filtro para identificar erros do OTP

# ==========================================
# CARREGAMENTO DINÂMICO DOS DADOS
# ==========================================
def carregar_capacidades_escolas(caminho_escolas):
    capacidades = {}
    with open(caminho_escolas, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for linha in reader:
            capacidades[linha['escola_id']] = int(linha['vagas'])
    return capacidades

def carregar_matriz_custo(caminho_matriz):
    matriz_tempo = {}
    escolas_set = set()
    with open(caminho_matriz, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for linha in reader:
            aluno = linha['aluno_id']
            escola = linha['escola_id']
            tempo = int(linha['tempo_segundos'])
            
            if aluno not in matriz_tempo:
                matriz_tempo[aluno] = {}
            matriz_tempo[aluno][escola] = tempo
            escolas_set.add(escola)
    return matriz_tempo, list(matriz_tempo.keys()), list(escolas_set)

CAPACIDADES_ESCOLAS = carregar_capacidades_escolas(ARQUIVO_ESCOLAS)
MATRIZ_TEMPO, LISTA_ALUNOS, LISTA_ESCOLAS = carregar_matriz_custo(ARQUIVO_MATRIZ)

# ==========================================
# OPERADORES DO ALGORITMO EVOLUTIVO
# ==========================================
def criar_individuo():
    """ Gera uma alocação inicial que respeita estritamente as vagas """
    pool_vagas = []
    for escola, vagas in CAPACIDADES_ESCOLAS.items():
        pool_vagas.extend([escola] * vagas)
    
    random.shuffle(pool_vagas)
    return pool_vagas[:len(LISTA_ALUNOS)]

def calcular_fitness(individuo):
    """ Retorna o tempo total de viagem. Penaliza severas conexões impossíveis """
    tempo_total = 0
    for idx_aluno, escola_alocada in enumerate(individuo):
        aluno_id = LISTA_ALUNOS[idx_aluno]
        tempo = MATRIZ_TEMPO[aluno_id][escola_alocada]
        
        if tempo >= LIMITE_INALCANSAVEL:
            tempo_total += 50000 # Penalidade alta por rota impossível, mas sem quebrar o gráfico
        else:
            tempo_total += tempo
            
    return tempo_total

def mutacao_por_troca(individuo):
    """ Altera as rotas trocando dois alunos de lugar sem quebrar as vagas """
    if random.random() < TAXA_MUTACAO:
        idx1 = random.randint(0, len(individuo) - 1)
        idx2 = random.randint(0, len(individuo) - 1)
        # Realiza o Swap
        individuo[idx1], individuo[idx2] = individuo[idx2], individuo[idx1]
    return individuo

# ==========================================
# EXECUÇÃO DO LOOP EVOLUTIVO
# ==========================================
if __name__ == "__main__":
    t_inicio = time.time()
    
    # População inicial nasce 100% válida em relação às vagas
    populacao = [criar_individuo() for _ in range(TAMANHO_POPULACAO)]
    
    print(f"Evoluindo alocação para {len(LISTA_ALUNOS)} alunos em {len(LISTA_ESCOLAS)} escolas...")
    print("-" * 70)
    
    for geracao in range(1, NUM_GERACOES + 1):
        # Avalia e ordena a população do menor tempo para o maior
        populacao_avaliada = sorted(populacao, key=calcular_fitness)
        melhor_f = calcular_fitness(populacao_avaliada[0])
        
        # Monitoramento do progresso
        if geracao % 50 == 0 or geracao == 1:
            # Conta quantos alunos estão em rotas inválidas no melhor indivíduo
            erros_rota = sum(1 for idx, esc in enumerate(populacao_avaliada[0]) if MATRIZ_TEMPO[LISTA_ALUNOS[idx]][esc] >= LIMITE_INALCANSAVEL)
            print(f"Geração {geracao:03d} | Custo Atual: {melhor_f} | Alunos sem ônibus: {erros_rota}")
            
        # Elitismo Estrito: Mantém a metade superior da população viva
        metade = TAMANHO_POPULACAO // 2
        nova_populacao = populacao_avaliada[:metade]
        
        # Gera clones com mutações por troca para preencher o resto da população
        while len(nova_populacao) < TAMANHO_POPULACAO:
            clone = list(random.choice(populacao_avaliada[:metade]))
            nova_populacao.append(mutacao_por_troca(clone))
            
        populacao = nova_populacao

    # ==========================================
    # EXIBIÇÃO DO RESULTADO FINAL CONSOLIDADO
    # ==========================================
    melhor_solucao = populacao_avaliada[0]
    custo_final = calcular_fitness(melhor_solucao)
    
    ocupacao_final = {escola: 0 for escola in LISTA_ESCOLAS}
    tempo_valido_total = 0
    alunos_validos = 0
    alunos_isolados = 0
    
    for idx, escola in enumerate(melhor_solucao):
        ocupacao_final[escola] += 1
        tempo = MATRIZ_TEMPO[LISTA_ALUNOS[idx]][escola]
        if tempo >= LIMITE_INALCANSAVEL:
            alunos_isolados += 1
        else:
            tempo_valido_total += tempo
            alunos_validos += 1

    print("-" * 70)
    print("📋 RELATÓRIO DE ALOCAÇÃO CONSOLIDADO (BAGÉ):")
    print("-" * 70)
    for escola in sorted(LISTA_ESCOLAS):
        print(f"-> {escola.replace('_', ' ')}: {ocupacao_final[escola]}/{CAPACIDADES_ESCOLAS[escola]} vagas ocupadas.")
        
    print("-" * 70)
    print(f"✔️ Solução converge com sucesso (0 estouros de vagas).")
    print(f"🚌 Alunos transportados com sucesso: {alunos_validos} de {len(LISTA_ALUNOS)}")
    if alunos_isolados > 0:
        print(f"⚠️ Alunos impossibilitados de usar ônibus (isolados geograficamente): {alunos_isolados}")
    
    tempo_medio = (tempo_valido_total / alunos_validos) / 60 if alunos_validos > 0 else 0
    print(f"⏱️ Tempo médio de deslocamento por aluno válido: {tempo_medio:.1f} minutos.")
    print(f"🚀 Algoritmo concluído em {time.time() - t_inicio:.2f} segundos.")