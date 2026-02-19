import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# --- CONFIGURAÇÕES GLOBAIS DE PADRONIZAÇÃO ---
CIDADES = ["Sumaré", "Hortolândia", "Campinas", "Paulínia", "Valinhos", "Americana"]
SERVICOS_PADRAO = ["Instalação Nova", "Reparo de Fibra", "Troca de Tecnologia", "Mudança de Endereço", "Suporte Wi-Fi"]
EMPRESAS = ["FiberTech", "Horizon Telecom", "Conecta+"]
TECNICOS = ["Kevyn Ferrezin", "João Silva", "Maria Oliveira", "Carlos Santos", "Ana Souza"]
PLANOS = ["Fibra 200MB", "Fibra 400MB", "Fibra 600MB", "Gamer Pro 1GB"]

def gerar_entrantes(n):
    data = []
    inicio = datetime(2026, 1, 1)
    hoje = datetime.now()
    
    for _ in range(n):
        cidade = random.choice(CIDADES)
        servico = random.choice(SERVICOS_PADRAO)
        criacao = inicio + timedelta(seconds=random.randint(0, int((hoje - inicio).total_seconds())))
        
        data.append({
            "empresa": random.choice(EMPRESAS),
            "descrição": servico,
            "cidade": cidade,
            "protocolo": f"2026{random.randint(1000000, 9999999)}",
            "created_at": criacao.strftime("%d/%m/%Y %H:%M:%S"),
            "Nome do Técnico": random.choice(TECNICOS),
            "status_os": random.choice(["Aberto", "Em deslocamento", "Pendente"]),
            "data_encerramento_prot": (criacao + timedelta(hours=random.randint(2, 48))).strftime("%d/%m/%Y %H:%M:%S"),
            "OLT": f"OLT-{random.choice(['ZTE', 'HUAWEI', 'NOKIA'])}-{random.randint(1, 10)}",
            "Regional": cidade, # Padronizado: Regional = Cidade
            "Motivo": servico
        })
    return pd.DataFrame(data)

def gerar_finalizados(n):
    data = []
    hoje = datetime.now()
    
    for _ in range(n):
        cidade = random.choice(CIDADES)
        servico = random.choice(SERVICOS_PADRAO)
        criacao = hoje - timedelta(days=random.randint(1, 45))
        conclusao = criacao + timedelta(hours=random.randint(1, 24))
        
        data.append({
            "empresa": random.choice(EMPRESAS),
            "descrição": servico,
            "cidade": cidade,
            "protocolo": f"2026{random.randint(1000000, 9999999)}",
            "created_at": criacao.strftime("%d/%m/%Y %H:%M:%S"),
            "Nome do Técnico": random.choice(TECNICOS),
            "status_os": "Finalizado",
            "data_encerramento_prot": conclusao.strftime("%d/%m/%Y %H:%M:%S"),
            "OLT": f"OLT-{random.choice(['ZTE', 'HUAWEI', 'NOKIA'])}-{random.randint(1, 10)}",
            "Regional": cidade,
            "Motivo": servico
        })
    return pd.DataFrame(data)

def gerar_cancelados(n):
    data = []
    inicio = datetime(2026, 1, 1)
    hoje = datetime.now()
    motivos_churn = ["Preço Elevado", "Mudança de Cidade", "Troca por Concorrente", "Problemas Técnicos"]
    setores = ["Retenção", "Financeiro", "Comercial", "Telemarketing"]
    
    for _ in range(n):
        cidade = random.choice(CIDADES)
        servico = random.choice(SERVICOS_PADRAO)
        # Sorteia o encerramento até o segundo atual
        encerramento = inicio + timedelta(seconds=random.randint(0, int((hoje - inicio).total_seconds())))
        
        # AJUSTE AQUI: Mudamos de (2, 10) para (0, 7). 
        # Assim, o chamado pode ter sido criado HOJE (0 dias de diferença).
        dias_aberto = random.randint(0, 7)
        created_at = encerramento - timedelta(days=dias_aberto, hours=random.randint(0, 12))

        data.append({
            "empresa": random.choice(EMPRESAS),
            "descrição": servico,
            "cidade": cidade,
            "protocolo": f"2026{random.randint(1000000, 9999999)}",
            "created_at": created_at.strftime("%d/%m/%Y %H:%M:%S"),
            "status_os": "Cancelado",
            "data_encerramento_prot": encerramento.strftime("%d/%m/%Y %H:%M:%S"),
            "OLT": f"OLT-{random.choice(['ZTE', 'HUAWEI', 'NOKIA'])}-{random.randint(1, 10)}",
            "Regional": cidade,
            "Motivo": servico,
            "Motivo do Cancelamento": random.choice(motivos_churn),
            "Setor que cancelou": random.choice(setores)
        })
    return pd.DataFrame(data)



def gerar_sobras(n):
    data = []
    inicio = datetime(2026, 1, 1)
    hoje = datetime.now()
    ontem = hoje - timedelta(days=1)
    
    motivos_pendencia = [
        "Falta de Tempo/Janela", "Cliente Ausente", 
        "Dificuldade Técnica (Poste/Tubulação)", 
        "Chuva Forte/Segurança", "Equipamento Defeituoso"
    ]
    
    for _ in range(n):
        cidade = random.choice(CIDADES)
        servico = random.choice(SERVICOS_PADRAO)
        
        # --- LÓGICA DE AGING (DISTRIBUIÇÃO DE PESOS) ---
        # 70% casos novos (0-2 dias), 20% casos em alerta (3-5 dias), 10% críticos (6-15 dias)
        peso = random.random()
        if peso > 0.3:
            dias_atras = random.randint(0, 2)
        elif peso > 0.1:
            dias_atras = random.randint(3, 5)
        else:
            dias_atras = random.randint(6, 15) # Casos "esquecidos" ou complexos

        # created_at é a data de nascimento do problema
        criacao = hoje - timedelta(days=dias_atras, hours=random.randint(0, 23), minutes=random.randint(0, 59))
        
        # data_sobra (quando foi tentado e sobrou) é entre a criação e hoje
        data_sobra = criacao + timedelta(hours=random.randint(2, 24))
        if data_sobra > hoje: data_sobra = hoje

        data.append({
            "empresa": random.choice(EMPRESAS),
            "descrição": servico,
            "cidade": cidade,
            "protocolo": f"2026{random.randint(1000000, 9999999)}",
            "created_at": criacao.strftime("%d/%m/%Y %H:%M:%S"),
            "status_os": "Pendente",
            "data_encerramento_prot": data_sobra.strftime("%d/%m/%Y %H:%M:%S"),
            "Nome do Técnico": random.choice(TECNICOS),
            "OLT": f"OLT-{random.choice(['ZTE', 'HUAWEI', 'NOKIA'])}-{random.randint(1, 10)}",
            "Regional": cidade,
            "Motivo": servico,
            "Motivo da Pendência": random.choice(motivos_pendencia),
            "Turno": random.choice(["Manhã", "Tarde"]),
            # --- NOVA COLUNA PARA O DASHBOARD ---
            "aging_dias": dias_atras # Facilita o cálculo do Cientista de Dados
        })
    return pd.DataFrame(data)

# --- EXECUÇÃO PRINCIPAL ---
if __name__ == "__main__":
    print("🚀 Iniciando geração das bases padronizadas...")
    
    # 1. Gerar DataFrames
    df_ent = gerar_entrantes(10000)
    df_fin = gerar_finalizados(10000)
    df_can = gerar_cancelados(10000)
    df_sobra = gerar_sobras(10000)
    
    # 2. Salvar Arquivos (exatamente com os nomes que o seu Dashboard busca)
    df_ent.to_csv("salesforce_entrantes_hoje_2026.csv", sep=";", index=False, encoding='utf-8-sig')
    df_fin.to_csv("salesforce_finalizados_2026.csv", sep=";", index=False, encoding='utf-8-sig')
    df_can.to_csv("salesforce_cancelados_hoje_2026.csv", sep=";", index=False, encoding='utf-8-sig')
    df_sobra.to_csv("salesforce_sobras_ontem_2026.csv", sep=";", index=False, encoding='utf-8-sig');
    
    print("✅ Sucesso! Os 3 arquivos foram gerados na pasta do projeto.")
    print(f"📊 Colunas de Descrição e Regional (Cidades) estão 100% sincronizadas.")