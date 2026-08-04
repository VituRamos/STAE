import requests
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# CONFIGURAÇÕES
OTP_URL = "http://localhost:8080/otp/routers/default/index/graphql"
ARQUIVO_ALUNOS = "alunos_simulados.csv"
ARQUIVO_ESCOLAS = "escolas_simuladas.csv"
ARQUIVO_SAIDA = "matriz_distancias_bage.csv"

# Número de requisições simultâneas. 
# 20 é um bom equilíbrio para não travar o servidor OTP local.
MAX_WORKERS = 20 

def carregar_csv(caminho_arquivo):
    with open(caminho_arquivo, mode='r', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def consultar_otp(tarefa):
    """
    Função executada por cada Thread. 
    Recebe um par (aluno, escola) e consulta o OTP.
    """
    aluno, escola = tarefa
    
    query = """
    query ObterRota($fromLat: Float!, $fromLon: Float!, $toLat: Float!, $toLon: Float!) {
      plan(
        from: { lat: $fromLat, lon: $fromLon }
        to: { lat: $toLat, lon: $toLon }
        date: "2017-03-15"
        time: "07:30:00"
        numItineraries: 1
      ) {
        itineraries {
          duration
        }
      }
    }
    """
    
    variables = {
        "fromLat": float(aluno['lat']),
        "fromLon": float(aluno['lon']),
        "toLat": float(escola['lat']),
        "toLon": float(escola['lon'])
    }
    
    try:
        # Timeout curto para evitar travamentos caso o OTP engasgue
        response = requests.post(OTP_URL, json={'query': query, 'variables': variables}, timeout=3)
        if response.status_code == 200:
            data = response.json()
            itineraries = data.get('data', {}).get('plan', {}).get('itineraries', [])
            if itineraries:
                return {
                    "aluno_id": aluno['aluno_id'],
                    "escola_id": escola['escola_id'],
                    "tempo_segundos": itineraries[0]['duration']
                }
    except Exception:
        pass # Erros de timeout ou conexão caem na penalidade abaixo
        
    # Se der erro ou não houver rota, retorna com a penalidade alta
    return {
        "aluno_id": aluno['aluno_id'],
        "escola_id": escola['escola_id'],
        "tempo_segundos": 999999
    }

if __name__ == "__main__":
    print("Carregando arquivos de cenário...")
    alunos = carregar_csv(ARQUIVO_ALUNOS)
    escolas = carregar_csv(ARQUIVO_ESCOLAS)
    
    # Cria o produto cartesiano (todas as combinações possíveis)
    lista_tarefas = [(aluno, escola) for aluno in alunos for escola in escolas]
    total_requisicoes = len(lista_tarefas)
    
    print(f"-> {len(alunos)} alunos e {len(escolas)} escolas carregados.")
    print(f"-> Total de rotas a calcular: {total_requisicoes}")
    print(f"-> Iniciando extração paralela com {MAX_WORKERS} workers. Aguarde...")
    
    tempo_inicio = time.time()
    matriz_resultados = []
    
    # Gerenciador de concorrência por Threads
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Dispara todas as tarefas de uma vez
        futuros = {executor.submit(consultar_otp, tarefa): tarefa for tarefa in lista_tarefas}
        
        contador = 0
        for futuro in as_completed(futuros):
            resultado = futuro.result()
            matriz_resultados.append(resultado)
            
            # Print de progresso a cada 250 requisições conclúidas
            contador += 1
            if contador % 250 == 0 or contador == total_requisicoes:
                print(f"Progresso: {contador}/{total_requisicoes} rotas calculadas ({(contador/total_requisicoes)*100:.1f}%)")

    # Salva o resultado final estruturado em CSV
    print(f"\nSalvando resultados em '{ARQUIVO_SAIDA}'...")
    with open(ARQUIVO_SAIDA, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["aluno_id", "escola_id", "tempo_segundos"])
        writer.writeheader()
        writer.writerows(matriz_resultados)
        
    tempo_total = time.time() - tempo_inicio
    print(f"Sucesso! Matriz gerada em {tempo_total:.1f} segundos.")