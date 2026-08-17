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

# CONFIGURAÇÕES DOS FICHEIROS
ARQUIVO_MATRIZ = "matriz_distancias_bage.csv"
ARQUIVO_ESCOLAS = "escolas_simuladas.csv"
LIMITE_INALCANSAVEL = 900000

# PARÂMETROS OPERACIONAIS
MAX_ALUNOS_POR_TURMA = 30
HORAS_AULA_TURMA = 20
CARGA_HORARIA_PROFESSOR = 40

# =============================================================
# PARÂMETROS DE CUSTO FINANCEIRO (Valores simulados para o modelo)
# =============================================================
CUSTO_TRANSPORTE_POR_SEGUNDO = (
    0.02  # Custo proporcional ao tempo de viagem por aluno
)
CUSTO_SUBSIDIO_PRIVADO = (
    3500.0  # Custo mensal/anual do subsídio para aluno na rede privada
)
CUSTO_CONTRATACAO_PROFESSOR = (
    4500.0  # Custo financeiro de um contrato docente por escola
)


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
  print("A construir o modelo matemático com relatórios financeiros...")

  modelo = LpProblem("MDESL_MIP_Custos_Detalhados", LpMinimize)

  # 1. VARIÁVEIS DE DECISÃO
  x = {}
  for a in LISTA_ALUNOS:
    x[a] = {}
    for e in LISTA_ESCOLAS:
      x[a][e] = LpVariable(f"aloca_{a}_{e}", cat=LpBinary)

  z = {}
  for a in LISTA_ALUNOS:
    z[a] = LpVariable(f"subsidio_{a}", cat=LpBinary)

  y = {}
  for e in LISTA_ESCOLAS:
    max_turmas_fisicas = (CAPACIDADES[e] // MAX_ALUNOS_POR_TURMA) + 1
    y[e] = LpVariable(
        f"turmas_{e}", lowBound=0, upBound=max_turmas_fisicas, cat=LpInteger
    )

  w = {}
  for e in LISTA_ESCOLAS:
    w[e] = LpVariable(f"professores_{e}", lowBound=0, cat=LpInteger)

  # 2. FUNÇÃO OBJETIVO FINANCEIRA GLOBAL
  custo_transporte_total = lpSum(
      CUSTO_TRANSPORTE_POR_SEGUNDO * MATRIZ_TEMPO[a][e] * x[a][e]
      for a in LISTA_ALUNOS
      for e in LISTA_ESCOLAS
  )

  custo_subsidios_total = lpSum(
      CUSTO_SUBSIDIO_PRIVADO * z[a] for a in LISTA_ALUNOS
  )

  custo_professores_total = lpSum(
      CUSTO_CONTRATACAO_PROFESSOR * w[e] for e in LISTA_ESCOLAS
  )

  modelo += (
      custo_transporte_total + custo_subsidios_total + custo_professores_total,
      "Custo_Financeiro_Global",
  )

  # 3. RESTRIÇÕES
  for a in LISTA_ALUNOS:
    modelo += (
        lpSum(x[a][e] for e in LISTA_ESCOLAS) + z[a] == 1,
        f"Demanda_Atendida_{a}",
    )

  for e in LISTA_ESCOLAS:
    modelo += (
        lpSum(x[a][e] for a in LISTA_ALUNOS) <= CAPACIDADES[e],
        f"Limite_Fisico_Vagas_{e}",
    )
    modelo += (
        lpSum(x[a][e] for a in LISTA_ALUNOS) <= MAX_ALUNOS_POR_TURMA * y[e],
        f"Capacidade_Turmas_{e}",
    )
    modelo += (
        HORAS_AULA_TURMA * y[e] <= CARGA_HORARIA_PROFESSOR * w[e],
        f"Carga_Horaria_Professores_{e}",
    )

  # 4. RESOLUÇÃO VIA SOLVER MIP
  print("A executar o Solver CBC...")
  modelo.solve(PULP_CBC_CMD(msg=False))

  # =============================================================
  # 5. CÁLCULO E EXIBIÇÃO DE CUSTOS TOTAIS E POR SETOR (ESCOLA)
  # =============================================================
  print("-" * 88)
  print("💰 RELATÓRIO FINANCEIRO GLOBAL E POR SETOR (UNIDADE ESCOLAR):")
  print("-" * 88)

  custo_transporte_real = 0
  custo_subsidio_real = 0
  custo_professores_real = 0

  # Acumuladores por setor (escola)
  custo_por_escola = {e: 0.0 for e in LISTA_ESCOLAS}
  alunos_por_escola = {e: 0 for e in LISTA_ESCOLAS}
  total_subsidiados = 0

  for a in LISTA_ALUNOS:
    if value(z[a]) > 0.5:
      total_subsidiados += 1
      custo_subsidio_real += CUSTO_SUBSIDIO_PRIVADO
    else:
      for e in LISTA_ESCOLAS:
        if value(x[a][e]) > 0.5:
          alunos_por_escola[e] += 1
          tempo = MATRIZ_TEMPO[a][e]
          if tempo < 50000:
            custo_t = CUSTO_TRANSPORTE_POR_SEGUNDO * tempo
            custo_transporte_real += custo_t
            custo_por_escola[e] += custo_t  # Atribui custo proporcional ao setor

  for e in LISTA_ESCOLAS:
    custo_prof = CUSTO_CONTRATACAO_PROFESSOR * value(w[e])
    custo_professores_real += custo_prof
    custo_por_escola[e] += (
        custo_prof  # Adiciona professores ao custo do setor escolar
    )

  custo_total_geral = (
      custo_transporte_real + custo_subsidio_real + custo_professores_real
  )

  print(f"📊 COMPONENTES DO CUSTO GLOBAL DO SISTEMA:")
  print(f"   • Custo Total de Transporte: R$ {custo_transporte_real:,.2f}")
  print(
      f"   • Custo Total de Subsídios (Rede Privada): R$"
      f" {custo_subsidio_real:,.2f} ({total_subsidiados} alunos)"
  )
  print(
      f"   • Custo Total de Contratação Docente: R$"
      f" {custo_professores_real:,.2f}"
  )
  print(
      f"========================================================================================"
  )
  print(f"💵 CUSTO TOTAL DA REDE DE ENSINO: R$ {custo_total_geral:,.2f}")
  print(
      f"----------------------------------------------------------------------------------------"
  )

  print(f"🏫 DETALHAMENTO DE CUSTOS POR SETOR (UNIDADE ESCOLAR):")
  for e in sorted(LISTA_ESCOLAS):
    qtd_turmas = int(value(y[e]))
    qtd_prof = int(value(w[e]))
    ocupacao = alunos_por_escola[e]
    custo_setor = custo_por_escola[e]
    print(
        f"-> {e.replace('_', ' ')}:"
        f" Alunos={ocupacao}/{CAPACIDADES[e]} | Turmas={qtd_turmas}"
        f" | Professores={qtd_prof} | Custo Setor=R$ {custo_setor:,.2f}"
    )

  print("-" * 88)
  print(
      f"🚀 Otimização financeira concluída em {time.time() - t_inicio:.2f}"
      " segundos."
  )