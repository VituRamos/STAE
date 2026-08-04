import csv
import folium

# CONFIGURAÇÕES
ARQUIVO_ALUNOS = "alunos_simulados.csv"
ARQUIVO_ESCOLAS = "escolas_simuladas.csv"
ARQUIVO_MATRIZ = "matriz_distancias_bage.csv"
LIMITE_INALCANSAVEL = 900000

print("Carregando dados da cidade...")

# 1. Carregar coordenadas das escolas
escolas = {}
with open(ARQUIVO_ESCOLAS, mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for linha in reader:
        escolas[linha['escola_id']] = (float(linha['lat']), float(linha['lon']))

# 2. Carregar coordenadas dos alunos
alunos = {}
with open(ARQUIVO_ALUNOS, mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for linha in reader:
        alunos[linha['aluno_id']] = (float(linha['lat']), float(linha['lon']))

# 3. Identificar os alunos isolados pela matriz de custo
# Um aluno é isolado se o tempo mínimo para chegar em QUALQUER escola for >= 900000
tempos_por_aluno = {aluno_id: [] for aluno_id in alunos.keys()}

with open(ARQUIVO_MATRIZ, mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for linha in reader:
        aluno = linha['aluno_id']
        tempo = int(linha['tempo_segundos'])
        tempos_por_aluno[aluno].append(tempo)

alunos_isolados = set()
for aluno, tempos in tempos_por_aluno.items():
    # Se o menor tempo entre todas as rotas possíveis ainda for um erro do OTP:
    if min(tempos) >= LIMITE_INALCANSAVEL:
        alunos_isolados.add(aluno)

print(f"Total de escolas processadas: {len(escolas)}")
print(f"Total de alunos isolados identificados: {len(alunos_isolados)}")

# 4. Criar o mapa centralizado em Bagé
# Usamos a média das coordenadas das escolas para centralizar a visão
lat_media = sum(coord[0] for coord in escolas.values()) / len(escolas)
lon_media = sum(coord[1] for coord in escolas.values()) / len(escolas)
mapa = folium.Map(location=[lat_media, lon_media], zoom_start=13, tiles="CartoDB positron")

# 5. Adicionar Escolas ao mapa (Marcadores Azuis com ícone de prédio)
for escola_id, coord in escolas.items():
    folium.Marker(
        location=coord,
        popup=f"<b>{escola_id.replace('_', ' ')}</b>",
        icon=folium.Icon(color="blue", icon="info-sign")
    ).add_to(mapa)

# 6. Adicionar Alunos Isolados ao mapa (Círculos Vermelhos)
for aluno_id in alunos_isolados:
    coord = alunos[aluno_id]
    folium.CircleMarker(
        location=coord,
        radius=6,
        popup=f"Aluno Isolado: {aluno_id}",
        color="red",
        fill=True,
        fill_color="red",
        fill_opacity=0.7
    ).add_to(mapa)

# Salvar o mapa
NOME_ARQUIVO_MAPA = "mapa_vazios_cobertura.html"
mapa.save(NOME_ARQUIVO_MAPA)
print(f"\nSucesso! Abra o arquivo '{NOME_ARQUIVO_MAPA}' no seu navegador para visualizar.")