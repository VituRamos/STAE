import random
import csv

# Configurações do limite urbano de Bagé
LAT_MIN, LAT_MAX = -31.3500, -31.3100
LON_MIN, LON_MAX = -54.1300, -54.0800

NUM_ALUNOS = 500

# 1. GERAR ESCOLAS (10 escolas distribuídas pela cidade)
# Coordenadas baseadas em centros de bairros reais e centro urbano de Bagé
escolas_base = [
    {"id": "Escola_Central_A", "lat": -31.3301, "lon": -54.1065, "vagas": 60},
    {"id": "Escola_Central_B", "lat": -31.3280, "lon": -54.1020, "vagas": 60},
    {"id": "Escola_Zona_Norte", "lat": -31.3150, "lon": -54.1100, "vagas": 55},
    {"id": "Escola_Menno_Fiege", "lat": -31.3190, "lon": -54.0950, "vagas": 55},
    {"id": "Escola_Passo_Pedras", "lat": -31.3380, "lon": -54.1220, "vagas": 55},
    {"id": "Escola_Morgado_Rosa", "lat": -31.3480, "lon": -54.0850, "vagas": 55},
    {"id": "Escola_Zona_Leste", "lat": -31.3250, "lon": -54.0820, "vagas": 55},
    {"id": "Escola_Industrial", "lat": -31.3420, "lon": -54.0990, "vagas": 55},
    {"id": "Escola_Castro_Alves", "lat": -31.3120, "lon": -54.1250, "vagas": 50},
    {"id": "Escola_Getulio_Vargas", "lat": -31.3350, "lon": -54.0900, "vagas": 50}
]

# Total de vagas = 550 (Para 500 alunos, deixando uma margem de 10% de folga)

# 2. GERAR ALUNOS ALEATÓRIOS (Espalhados pela cidade)
alunos_gerados = []
for i in range(1, NUM_ALUNOS + 1):
    alunos_gerados.append({
        "aluno_id": f"aluno_{i:03d}",  # <-- CORRIGIDO: mudou de "id" para "aluno_id"
        "lat": round(random.uniform(LAT_MIN, LAT_MAX), 6),
        "lon": round(random.uniform(LON_MIN, LON_MAX), 6)
    })

# 3. SALVAR ARQUIVOS CSV
with open("escolas_simuladas.csv", mode="w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["escola_id", "lat", "lon", "vagas"])
    writer.writeheader()
    for esc in escolas_base:
        writer.writerow({"escola_id": esc["id"], "lat": esc["lat"], "lon": esc["lon"], "vagas": esc["vagas"]})

with open("alunos_simulados.csv", mode="w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["aluno_id", "lat", "lon"])
    writer.writeheader()
    writer.writerows(alunos_gerados)

print(f"Cenário gerado com sucesso!")
print(f"-> 10 Escolas criadas (Total de vagas: {sum(e['vagas'] for e in escolas_base)})")
print(f"-> {NUM_ALUNOS} Alunos espalhados por Bagé.")