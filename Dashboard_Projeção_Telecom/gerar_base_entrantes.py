import pandas as pd
from datetime import datetime, timedelta
import random

def gerar_entrantes_telecom(n_linhas=10000):
    empresas = ["FiberTech", "Horizon Telecom", "Conecta+"]
    cidades = ["Sumaré", "Hortolândia", "Campinas", "Paulínia", "Valinhos", "Americana"]
    tecnicos = ["Kevyn Ferrezin", "João Silva", "Maria Oliveira", "Carlos Santos", "Ana Souza", "N/A"]
    planos = ["Fibra 200MB", "Fibra 400MB", "Fibra 600MB", "Gamer Pro 1GB"]
    
    # LISTA PADRONIZADA PARA FILTROS GLOBAIS
    servicos_padrao = ["Instalação Nova", "Reparo de Fibra", "Troca de Tecnologia", "Mudança de Endereço", "Suporte Wi-Fi"]
    
    data_inicio_jan = datetime(2026, 1, 1, 8, 0, 0)
    data_hoje = datetime.now()
    delta_total = data_hoje - data_inicio_jan
    data = []

    for i in range(n_linhas):
        segundos_aleatorios = random.randint(0, int(delta_total.total_seconds()))
        created_at = data_inicio_jan + timedelta(seconds=segundos_aleatorios)
        cidade_sorteada = random.choice(cidades)
        servico_sorteado = random.choice(servicos_padrao)

        row = {
            "empresa": random.choice(empresas),
            "descrição": servico_sorteado,
            "cidade": cidade_sorteada,
            "protocolo": f"2026{random.randint(1000000, 9999999)}",
            "created_at": created_at.strftime("%d/%m/%Y %H:%M:%S"),
            "so": f"SO-{random.randint(50000, 99999)}",
            "assinante": f"Assinante_{random.randint(10000, 99999)}",
            "Nome do Técnico": random.choice(tecnicos[:-1]),
            "status_os": random.choice(["Aberto", "Finalizado", "Pendente"]),
            "data_encerramento_prot": (created_at + timedelta(hours=random.randint(2, 48))).strftime("%d/%m/%Y %H:%M:%S"),
            "plano_cliente": random.choice(planos),
            "OLT": f"OLT-{random.choice(['ZTE', 'HUAWEI', 'NOKIA'])}-{random.randint(1, 10)}",
            "Regional": cidade_sorteada, # Regional agora é a Cidade
            "Motivo": servico_sorteado # Motivo igual à Descrição para evitar quebra de filtro
        }
        data.append(row)

    df = pd.DataFrame(data)
    df.to_csv("salesforce_entrantes_hoje_2026.csv", sep=";", index=False, encoding='utf-8-sig')
    print("✅ Base de Entrantes gerada!")

if __name__ == "__main__":
    gerar_entrantes_telecom(10000)