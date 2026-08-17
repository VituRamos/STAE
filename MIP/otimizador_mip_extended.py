import csv
import time
from pulp import (
    LpBinary,
    LpInteger,
    LpMinimize,
    LpProblem,
    LpVariable,
    lpSum,
    value,
    PULP_CBC_CMD,
)

# CONFIGURAÇÕES DOS ARQUIVOS
ARQUIVO_MATRIZ = "matriz_distancias_bage.csv"
ARQUIVO_ESCOLAS = "escolas_simuladas.csv"
LIMITE_INALCANSAVEL = 900000

# PARÂMETROS OPERACIONAIS (Inspirados na Tese)
MAX_ALUNOS_POR_TURMA = 30  # Limite máximo de alunos em uma sala de aula
HORAS_AULA_TURMA = 20  # Carga horária semanal necessária para atender uma turma
CARGA_HORARIA_PROFESSOR = 40  # Carga horária semanal de um contrato de professor


def carregar_dados():
  capacidades = {}
  with open(ARQUIVO_ESCOLAS, mode="r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for linha in reader:
      capacidades[linha["escola_id"]] = int(linha["vagas"])

  matriz_tempo = {}
  escolas_set = set()
  with open(ARQUIVO_MATRIZ, mode="r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for linha in reader:
      aluno, escola = linha["aluno_id"], linha["escola_id"]
      tempo = int(linha["tempo_segundos"])

      if tempo >= LIMITE_INALCANSAVEL:
        tempo = 50000

      if aluno not in matriz_tempo:
        matriz_tempo[aluno] = {}
      matriz_tempo[aluno][escola] = tempo
      escolas_set.add(escola)

  return matriz_tempo, capacidades, list(matriz_tempo.keys()), list(escolas_set)


MATRIZ_TEMPO, CAPACIDADES, LISTA_ALUNOS, LISTA_ESCOLAS = carregar_dados()

if __name__ == "__main__":
  t_inicio = time.time()
  print("Construindo o modelo matemático avançado (Alunos + Turmas + Professores)...")

  # 1. Cria o problema de Minimização
  modelo = LpProblem("Otimizacao_Sistema_Ensino_Completo", LpMinimize)

  # -------------------------------------------------------------
  # VARIÁVEIS DE DECISÃO
  # -------------------------------------------------------------
  # x[a][e]: Binária (0 ou 1) -> Aluno 'a' vai para a escola 'e'
  x = {}
  for a in LISTA_ALUNOS:
    x[a] = {}
    for e in LISTA_ESCOLAS:
      x[a][e] = LpVariable(f"aloca_{a}_{e}", cat=LpBinary)

    # y[e]: Inteira -> Quantas turmas abrir na escola 'e'
  y = {}
  for e in LISTA_ESCOLAS:
    max_turmas_possiveis = (
        CAPACIDADES[e] // MAX_ALUNOS_POR_TURMA
    ) + 1  # Limite físico
    y[e] = LpVariable(
        f"turmas_{e}", lowBound=0, upBound=max_turmas_possiveis, cat=LpInteger
    )

  # w[e]: Inteira -> Quantos professores contratar/alocar na escola 'e'
  w = {}
  for e in LISTA_ESCOLAS:
    w[e] = LpVariable(
        f"professores_{e}", lowBound=0, cat=LpInteger
    )  # Sem teto prévio, o solver decide

  # -------------------------------------------------------------
  # FUNÇÃO OBJETIVO
  # -------------------------------------------------------------
  # Minimizar o tempo total de transporte dos alunos
  # (Aqui você também poderia somar custos financeiros de professores: + lpSum(5000 * w[e] for e in LISTA_ESCOLAS))
  modelo += (
      lpSum(
          MATRIZ_TEMPO[a][e] * x[a][e]
          for a in LISTA_ALUNOS
          for e in LISTA_ESCOLAS
      ),
      "Tempo_Total_Deslocamento",
  )

  # -------------------------------------------------------------
  # RESTRIÇÕES
  # -------------------------------------------------------------

  # Restrição 1: Cada aluno deve ser alocado a exatamente 1 escola
  for a in LISTA_ALUNOS:
    modelo += lpSum(x[a][e] for e in LISTA_ESCOLAS) == 1, f"Demanda_Aluno_{a}"

  # Restrição 2: O total de alunos na escola não pode exceder as vagas físicas da instituição
  for e in LISTA_ESCOLAS:
    modelo += (
        lpSum(x[a][e] for a in LISTA_ALUNOS) <= CAPACIDADES[e],
        f"Limite_Fisico_Vagas_{e}",
    )

  # Restrição 3: O total de alunos alocados em uma escola deve caber estritamente dentro das turmas abertas
  for e in LISTA_ESCOLAS:
    modelo += (
        lpSum(x[a][e] for a in LISTA_ALUNOS) <= MAX_ALUNOS_POR_TURMA * y[e],
        f"Capacidade_Turmas_Abertas_{e}",
    )

  # Restrição 4: A carga horária total das turmas abertas deve ser suprida pelos professores contratados
  for e in LISTA_ESCOLAS:
    modelo += (
        HORAS_AULA_TURMA * y[e] <= CARGA_HORARIA_PROFESSOR * w[e],
        f"Dimensionamento_Carga_Horaria_Professores_{e}",
    )

  # ==========================================
  # RESOLUÇÃO DO PROBLEMA
  # ==========================================
  print("Iniciando o Solver MIP com restrições operacionais...")
  modelo.solve(PULP_CBC_CMD(msg=False))

  # ==========================================
  # RELATÓRIO DOS RESULTADOS EXPANDIDOS
  # ==========================================
  print("-" * 75)
  print("📋 RELATÓRIO DO MODELO MATEMÁTICO COMPLETO (ALUNOS, TURMAS E PROFESSORES):")
  print("-" * 75)

  ocupacao_final = {e: 0 for e in LISTA_ESCOLAS}
  tempo_valido_total = 0
  alunos_validos = 0

  for a in LISTA_ALUNOS:
    for e in LISTA_ESCOLAS:
      if value(x[a][e]) == 1.0:
        ocupacao_final[e] += 1
        tempo_real = MATRIZ_TEMPO[a][e]
        if tempo_real < 50000:
          tempo_valido_total += tempo_real
          alunos_validos += 1

  for e in sorted(LISTA_ESCOLAS):
    qtd_turmas = int(value(y[e]))
    qtd_prof = int(value(w[e]))
    print(
        f"-> {e.replace('_', ' ')}: Alunos: {ocupacao_final[e]}/{CAPACIDADES[e]}"
        f" | Turmas Abertas: {qtd_turmas} | Professores Alocados: {qtd_prof}"
    )

  print("-" * 75)
  tempo_medio = (
      (tempo_valido_total / alunos_validos) / 60 if alunos_validos > 0 else 0
  )
  print(f"⏱️ Tempo médio de deslocamento: {tempo_medio:.1f} minutos.")
  print(f"🚀 Otimização completa concluída em {time.time() - t_inicio:.2f} segundos.")