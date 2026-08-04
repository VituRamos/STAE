# STAE
Sistema de Transporte e Alocação Escolar via Algoritmo Genético

🚌 Otimização de Alocação Escolar via Algoritmo Genético e OpenTripPlanner (OTP)Este projeto resolve o Problema de Localização e Alocação com Capacidade (Capacitated Facility Location Problem) aplicado ao sistema de transporte público urbano. O objetivo é distribuir estudantes em escolas de forma otimizada, minimizando o tempo total de viagem via ônibus sem exceder o limite de vagas das instituições.O pipeline utiliza o OpenTripPlanner (OTP) para roteamento multimodal com dados reais de transporte (GTFS + OpenStreetMap) e um Algoritmo Genético (AG) baseado em permutação para otimização combinatória.📌 Fluxo da ArquiteturaServidor OTP (Local): Processa a malha viária e tabelas de ônibus.População Sintética: Mapeia alunos e capacidades de vagas das escolas.Extração Multithread: Calcula matrizes de tempo $N \times M$ em paralelo via REST API.Algoritmo Genético: Otimiza a distribuição de vagas por permutação e Swap Mutation.Diagnóstico Geográfico: Identifica vazios de cobertura de transporte público (Transit Deserts) e gera mapas interativos.🛠️ Pré-requisitosCertifique-se de ter os seguintes componentes instalados em sua máquina:Java Development Kit (JDK): Versão 17 ou 21 (necessário para rodar o OTP 2.x).Bashjava -version
Python: Versão 3.10 ou superior.Bashpython --version
Dependências Python:Bashpip install requests folium
📂 Estrutura do RepositórioPara que o servidor OTP e os scripts Python se comuniquem corretamente, estruture a pasta do projeto conforme o esquema abaixo:Plaintext📂 projeto_transporte/
 ├── 📄 gerador_cenario.py          # Gerador de coordenadas sintéticas
 ├── 📄 extrator_matriz_paralelo.py # Extrator multithread de tempos de rota via OTP
 ├── 📄 otimizador_escola_real.py  # Motor do Algoritmo Genético (Permutação/Swap)
 ├── 📄 gerar_mapa_isolados.py     # Gerador do mapa interativo de vazios urbanos
 └── 📂 otp_servidor/
      ├── ☕ otp-2.4.0-shaded.jar   # Executável do OpenTripPlanner
      └── 📂 bage_dados/
           ├── 🗺️ sul-latest.osm.pbf # Malha viária (OpenStreetMap)
           └── 🚌 gtfs_bage.zip     # Tabela de ônibus e horários (GTFS)
🚀 Passo a Passo de Execução1️⃣ Configurar e Iniciar o Servidor OpenTripPlanner (OTP)Navegue até a pasta do servidor OTP no terminal:Bashcd otp_servidor
A. Construir o Grafo de Roteamento (Executar apenas na primeira vez)Combina o mapa viário com as linhas de ônibus para criar o grafo de transporte:Bashjava -Xmx4G -jar otp-2.4.0-shaded.jar --build --save bage_dados
B. Iniciar o ServidorCarrega o grafo compilado na memória e abre a API local:Bashjava -Xmx4G -jar otp-2.4.0-shaded.jar --load bage_dados
⚠️ Atenção: Mantenha este terminal aberto. O servidor estará pronto quando exibir a mensagem Grizzly server running. Você pode testar a interface acessando http://localhost:8080 no navegador.2️⃣ Gerar a População Sintética e EscolasEm um novo terminal, navegue até a raiz do projeto (projeto_transporte) e execute:Bashpython gerador_cenario.py
Saída: Cria os arquivos alunos_simulados.csv e escolas_simuladas.csv com as posições geográficas e capacidades físicas de cada escola.3️⃣ Extrair a Matriz de Tempos de Viagem (Multithreading)Com o servidor OTP online na porta 8080, execute a consulta paralela:Bashpython extrator_matriz_paralelo.py
O que faz: Dispara requisições simultâneas (20 threads) para a API do OTP, calculando os tempos exatos de viagem porta a porta. Caso o transporte público não atenda ao trajeto, atribui a penalidade de rota inalcançável.Saída: Gera o arquivo matriz_distancias_bage.csv.4️⃣ Executar a Otimização com Algoritmo GenéticoExecute a etapa de computação evolutiva para encontrar a alocação ótima:Bashpython otimizador_escola_real.py
O que faz: Processa as gerações de evolução respeitando estritamente o limite de vagas de cada escola por meio de mutações por troca (Swap Mutation).Saída: Exibe no terminal a convergência de custo por geração, a taxa de ocupação das escolas e o tempo médio global de deslocamento.5️⃣ Gerar o Mapa de Diagnóstico UrbanoPara visualizar espacialmente os alunos geograficamente isolados da rede de transporte público:Bashpython gerar_mapa_isolados.py
Saída: Cria o arquivo mapa_vazios_cobertura.html. Dê dois cliques no arquivo gerado para visualizá-lo interativamente em qualquer navegador.📊 Saídas do SistemaArquivoDescriçãomatriz_distancias_bage.csvTabela $N \times M$ com todos os tempos de viagem calculados pelo OTP.mapa_vazios_cobertura.htmlMapa georreferenciado contendo marcadores das escolas e dos alunos em vazios de cobertura.Relatório no TerminalMétrica de convergência do AG, tempo médio por aluno e validação do limite de vagas.
