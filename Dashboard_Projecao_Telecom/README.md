🛰️ Dashboard de Projeção Operacional Telecom (Sumaré Ops)
📝 Sobre o Projeto
Este projeto consiste em um Sistema de Suporte à Decisão (DSS) desenvolvido em Python e Streamlit, focado na gestão end-to-end de operações de campo no setor de Telecomunicações.

O sistema rompe com a visão tradicional de "relatórios estáticos" ao integrar modelos de projeção estatística com o balanço diário de carga operacional. Ele consolida dados de múltiplas fontes (Entrantes, Finalizados, Cancelados e Sobras) para oferecer uma visão em tempo real da "saúde" da operação e da força de trabalho.

🎯 Objetivo do Projeto
O objetivo central é antecipar a carga de trabalho e otimizar a vazão de atendimento da regional. Através da análise preditiva e do monitoramento de Aging (envelhecimento de fila), o projeto visa:

Prever a Rota Inicial (D+1): Calcular com precisão o volume de ordens de serviço para o dia seguinte, somando a demanda projetada ao passivo acumulado (sobras).

Garantir o SLA: Identificar gargalos de atendimento através da análise de Aging, priorizando chamados críticos para reduzir o Churn e aumentar a satisfação do cliente.

Maximizar a Produtividade: Monitorar a eficiência individual e coletiva dos técnicos de campo, permitindo o redimensionamento de equipes baseado em demanda real vs. capacidade instalada.

Visão Executiva: Oferecer um Overview consolidado para a diretoria, transformando dados brutos em decisões estratégicas em segundos.

🚀 Principais Funcionalidades
Projeção de Demanda: Algoritmo que calcula médias móveis e sazonalidade diária para prever entradas e saídas.

Balanço de Massa Operacional: Cálculo dinâmico de (Novos + Sobras) - (Vazão).

Monitoramento de Aging: Gráficos de envelhecimento de fila por buckets de tempo (0-24h, 24-48h, +72h).

Ranking de Eficiência: Painel de produtividade técnica com métricas de taxa de sucesso e ocupação.

🛠️ Tech Stack
Linguagem: Python 3.x

Framework Web: Streamlit

Manipulação de Dados: Pandas / Numpy

Visualização: Altair / Plotly

Versionamento: Git

OBS: Todos os dados apresentados não condizem com a realidade de nenhuma empresa e nem é contra as normas LGPD, os mesmos são gerados através de um código em Python.

Acesse o Dashboard Aqui: https://projetos-ciencia-de-dados-dashboard-projecao-telecom.streamlit.app/

