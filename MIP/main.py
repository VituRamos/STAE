from fastapi import FastAPI, HTTPException
import subprocess
import os

app = FastAPI(
  title="STAE - Sistema de Transporte e Alocação Escolar",
  version="2.0",
  description="API de Otimização Exata baseada em MIP",
)


@app.post("/api/otimizar")
def rodar_otimizacao():
  """Dispara o motor MIP para recalcular a alocação ótima dos alunos."""
  script_otimizador = "otimizador_mip.py"

  if not os.path.exists(script_otimizador):
    raise HTTPException(
        status_code=404, detail="Script de otimizador não encontrado no servidor."
    )

  try:
    # Executa o script do solver em subprocesso e captura o retorno
    resultado = subprocess.run(
        ["python", script_otimizador],
        capture_output=True,
        text=True,
        check=True,
    )

    return {
        "status": "sucesso",
        "mensagem": "Otimização exata concluída com sucesso!",
        "logs_solver": resultado.stdout,
    }
  except subprocess.CalledProcessError as e:
    raise HTTPException(
        status_code=500,
        detail=f"Erro interno ao rodar o solver: {e.stderr}",
    )


@app.get("/health")
def health_check():
  return {"status": "online", "motor": "MIP/PuLP"}