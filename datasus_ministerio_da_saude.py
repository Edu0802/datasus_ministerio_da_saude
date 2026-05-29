import os
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output

# ==============================================================================
# DICIONÁRIOS E MAPEAMENTOS ESTRUTURAIS (DADOS DO SUS)
# ==============================================================================
DE_PAR_UFS = {
    'AC': 'Acre', 'AL': 'Alagoas', 'AP': 'Amapá', 'AM': 'Amazonas', 'BA': 'Bahia',
    'CE': 'Ceará', 'DF': 'Distrito Federal', 'ES': 'Espírito Santo', 'GO': 'Goiás',
    'MA': 'Maranhão', 'MT': 'Mato Grosso', 'MS': 'Mato Grosso do Sul', 'MG': 'Minas Gerais',
    'PA': 'Pará', 'PB': 'Paraíba', 'PR': 'Paraná', 'PE': 'Pernambuco', 'PI': 'Piauí',
    'RJ': 'Rio de Janeiro', 'RN': 'Rio Grande do Norte', 'RS': 'Rio Grande do Sul',
    'RO': 'Rondônia', 'RR': 'Roraima', 'SC': 'Santa Catarina', 'SP': 'São Paulo',
    'SE': 'Sergipe', 'TO': 'Tocantins'
}

SUBGRUPOS_POR_GRUPO = {
    'vl_02': {'vl_0201': 'Exames Lab', 'vl_0202': 'Imagem'},
    'vl_03': {'vl_0304': 'Partos'},
    'vl_04': {'vl_0409': 'Ortopedia', 'vl_0415': 'Trauma'}
}

NOMES_GRUPOS = {
    'vl_02': 'Diagnóstico', 'vl_03': 'Clínico', 'vl_04': 'Cirúrgico', 
    'vl_05': 'Transplantes', 'vl_07': 'OPME'
}

PAI_DO_SUBGRUPO = {
    'vl_0201': 'vl_02', 'vl_0202': 'vl_02',
    'vl_0304': 'vl_03',
    'vl_0409': 'vl_04', 'vl_0415': 'vl_04'
}

# ==============================================================================
# ESTILIZAÇÃO CUSTOMIZADA (CSS)
# ==============================================================================
if not os.path.exists('assets'):
    os.makedirs('assets')

with open('assets/style.css', 'w') as f:
    f.write('''
* { box-sizing: border-box; }
body { margin: 0; padding: 0; background-color: #000000; color: #FFFFFF; font-family: "DM Sans", sans-serif; }
#react-entry-point, .dash-spreadsheet, .dash-table-container { background-color: #000000; }
h1 { color: #39FF14; margin: 0; font-size: 26px; letter-spacing: 1px; font-weight: bold; text-shadow: 0 0 10px rgba(57, 255, 20, 0.2); }
.subtitulo { color: #888888 !important; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; margin-top: 5px; }
.secao { background-color: #050505; border: 1px solid #111111; border-radius: 8px; padding: 20px; margin: 15px; box-shadow: 0 0 15px rgba(0,0,0,0.9); }
.dash-dropdown { background-color: #8c8c8c !important; border: 1px solid #222222 !important; border-radius: 4px; }
.dash-dropdown-value, .dash-dropdown-value-item, .dash-dropdown-value-item span, .dash-dropdown-placeholder, .dash-dropdown * { color: #000000 !important; font-weight: 700 !important; }
.dash-dropdown svg, .dash-dropdown-trigger-icon, .dash-dropdown-clear svg path { fill: #000000 !important; color: #000000 !important; }
[data-radix-popper-content-wrapper] *, [role="listbox"] *, .dash-dropdown-wrapper [style*="position"] { background-color: #8c8c8c !important; color: #000000 !important; }
.grid-kpis { display: flex; justify-content: space-between; margin: 0 15px 15px 15px; gap: 15px; }
.kpi-card { background-color: #050505; border-radius: 8px; padding: 15px; text-align: center; border: 1px solid #111111; flex: 1; box-shadow: 0 0 10px rgba(0,0,0,0.5); white-space: nowrap; }
.card-azul    { border-top: 3px solid #00ffff !important; }
.card-verde   { border-top: 3px solid #39FF14 !important; }
.card-laranja { border-top: 3px solid #FF5C00 !important; }
.card-roxo    { border-top: 3px solid #FFFF00 !important; }
.card-rosa    { border-top: 3px solid #FF007F !important; }
.kpi-label { font-size: 11px; color: #666666; text-transform: uppercase; margin-bottom: 5px; letter-spacing: 0.5px; }
.kpi-value { font-size: 18px; font-weight: bold; }
.js-plotly-plot, .dash-graph { background-color: #050505 !important; border-radius: 8px; }
''')

# ==============================================================================
# LEITURA OTIMIZADA DO ARQUIVO CSV LOCAL
# ==============================================================================
df = pd.read_csv("dados_sus.csv")

# Tratamento e limpeza rápida dos dados carregados
df['uf_sigla'] = df['uf_sigla'].str.strip().str.upper()
df['nome_municipio'] = df['nome_municipio'].str.strip()
df['regiao_nome'] = df['regiao_nome'].str.strip()
colunas_valores = [c for c in df.columns if c.startswith('vl_') or c.startswith('qtd_')]
df[colunas_valores] = df[colunas_valores].fillna(0)
df['numero_habitantes'] = df['numero_habitantes'].fillna(0).astype(int)
df['ano_aih'] = df['ano_aih'].astype(int)
df['uf_extenso'] = df['uf_sigla'].map(DE_PAR_UFS).fillna(df['uf_sigla'])

anos_disponiveis = sorted(df['ano_aih'].unique())
ufs_disponiveis = sorted(df['uf_sigla'].unique())
opcoes_anos = [{"label": str(a), "value": a} for a in anos_disponiveis]

# ==============================================================================
# CONFIGURAÇÃO DO DASHBOARD
# ==============================================================================
app = dash.Dash(__name__)
server = app.server  # Crucial para o funcionamento do Gunicorn na nuvem da Render

app.layout = html.Div([
    html.Div([
        html.Div([
            html.H1("DATASUS – Ministério da Saúde"),
            html.Div("Painel de Monitoramento Orçamentário", className="subtitulo")
        ], style={"flex": "1"}),
        html.Div([
            html.Div([html.Label("Ano", style={"font-size": "11px", "color": "#888888"}), dcc.Dropdown(id="filtro-ano", options=opcoes_anos, value=None, placeholder="Todos", clearable=True)], style={"width": "120px", "margin-right": "10px"}),
            html.Div([html.Label("UF", style={"font-size": "11px", "color": "#888888"}), dcc.Dropdown(id="filtro-uf", options=[{"label": u, "value": u} for u in ufs_disponiveis], value=None, placeholder="Todos")], style={"width": "110px", "margin-right": "10px"}),
            html.Div([html.Label("Município", style={"font-size": "11px", "color": "#888888"}), dcc.Dropdown(id="filtro-municipio", placeholder="Todos")], style={"width": "180px", "margin-right": "10px"}),
            html.Div([html.Label("Grupo SUS", style={"font-size": "11px", "color": "#888888"}), dcc.Dropdown(id="filtro-grupo", options=[{"label": f"{v.replace('vl_','')} - {k}", "value": v} for v, k in NOMES_GRUPOS.items()], placeholder="Todos", clearable=True)], style={"width": "160px", "margin-right": "10px"}),
            html.Div([html.Label("Subgrupo Crítico", style={"font-size": "11px", "color": "#888888"}), dcc.Dropdown(id="filtro-subgrupo", options=[
                {"label": "0201 - Exames Lab", "value": "vl_0201"}, {"label": "0202 - Imagem", "value": "vl_0202"},
                {"label": "0304 - Partos", "value": "vl_0304"},
                {"label": "0409 - Ortopedia", "value": "vl_0409"}, {"label": "0415 - Trauma", "value": "vl_0415"}
            ], placeholder="Todos", clearable=True)], style={"width": "160px"})
        ], style={"display": "flex", "alignItems": "center"})
    ], className="secao", style={"display": "flex", "alignItems": "center", "justifyContent": "space-between", "borderBottom": "2px solid #39FF14"}),

    html.Div([
        html.Div([html.Div("Total de Internações", className="kpi-label"), html.Div(id="kpi-internacoes", className="kpi-value", style={"color": "#00ffff"})], className="kpi-card card-azul"),
        html.Div([html.Div("Total Gasto (SUS)", className="kpi-label"), html.Div(id="kpi-gastos", className="kpi-value", style={"color": "#39FF14"})], className="kpi-card card-verde"),
        html.Div([html.Div("Média por Município", className="kpi-label"), html.Div(id="kpi-custo-medio", className="kpi-value", style={"color": "#FF5C00"})], className="kpi-card card-laranja"),
        html.Div([html.Div("Maior Gasto por UF", className="kpi-label"), html.Div(id="kpi-maior-uf", className="kpi-value", style={"color": "#FFFF00"})], className="kpi-card card-roxo"),
        html.Div([html.Div("Maior Gasto Município", className="kpi-label"), html.Div(id="kpi-maior-mun", className="kpi-value", style={"color": "#FF007F"})], className="kpi-card card-rosa")
    ], className="grid-kpis"),

    html.Div([
        html.Div([dcc.Graph(id="grafico-gastos-uf")], style={"flex": "1", "margin-right": "10px"}),
        html.Div([dcc.Graph(id="grafico-gastos-municipio")], style={"flex": "1", "margin-left": "10px"})
    ], style={"display": "flex", "margin": "0 15px 15px 15px"}),

    html.Div([
        html.Div([dcc.Graph(id="grafico-evolucao-anual")], style={"flex": "1", "margin-right": "10px"}),
        html.Div([dcc.Graph(id="grafico-distribuicao-grupo")], style={"flex": "1", "margin-left": "10px"})
    ], style={"display": "flex", "margin": "0 15px 15px 15px"}),

    html.Div([dcc.Graph(id="grafico-top-municipios")], className="secao"),

    html.Div([
        html.H3("📋 DETALHAMENTO ANALÍTICO DA REDE", style={"font-size": "13px", "color": "#39FF14", "margin": "0 0 15px 0"}),
        dash_table.DataTable(
            id="tabela-detalhada",
            columns=[
                {"name": "Município", "id": "nome_municipio", "sort_as_id": "nome_municipio"},
                {"name": "UF", "id": "uf_sigla", "sort_as_id": "uf_sigla"},
                {"name": "Ano", "id": "ano_aih", "sort_as_id": "ano_aih"},
                {"name": "Qtd Total Internações", "id": "qtd_total_formatada", "sort_as_id": "qtd_total"},
                {"name": "Valor Destinado (R$)", "id": "vl_total_formatado", "sort_as_id": "vl_total"}
            ],
            page_size=12, sort_action="native", page_action="native",
            style_header={'backgroundColor': '#0d0d0d', 'color': '#39FF14', 'fontWeight': 'bold', 'border': '1px solid #1a1a1a', 'padding': '12px', 'fontSize': '12px', 'textTransform': 'uppercase'},
            style_cell={'padding': '12px', 'fontSize': '13px', 'border': '1px solid #111111'},
            style_cell_conditional=[
                {'if': {'column_id': 'nome_municipio'}, 'textAlign': 'left'},
                {'if': {'column_id': 'uf_sigla'}, 'textAlign': 'center', 'width': '80px'},
                {'if': {'column_id': 'ano_aih'}, 'textAlign': 'center', 'width': '90px'},
                {'if': {'column_id': 'qtd_total_formatada'}, 'textAlign': 'right'},
                {'if': {'column_id': 'vl_total_formatado'}, 'textAlign': 'right', 'color': '#39FF14', 'fontWeight': 'bold'}
            ],
            style_data_conditional=[
                {'if': {'row_index': 'odd'}, 'backgroundColor': '#070707'},
                {'if': {'row_index': 'even'}, 'backgroundColor': '#000000'},
                {'if': {'state': 'selected'}, 'backgroundColor': '#112211', 'border': '1px solid #39FF14'}
            ],
            style_data={'color': '#FFFFFF'}
        )
    ], className="secao")
])

# ==============================================================================
# CALLBACK DE DINÂMICA GEOGRÁFICA
# ==============================================================================
@app.callback(Output("filtro-municipio", "options"), Input("filtro-uf", "value"))
def atualizar_dropdown_municipios(uf_selecionada):
    if not uf_selecionada:
        return [{"label": m, "value": m} for m in sorted(df["nome_municipio"].unique())]
    return [{"label": m, "value": m} for m in sorted(df[df["uf_sigla"] == uf_selecionada]["nome_municipio"].unique())]

# ==============================================================================
# CALLBACK MESTRE PIPELINE (INDEPENDÊNCIA DE GRUPO/SUBGRUPO + LINHA DO TEMPO FIX)
# ==============================================================================
@app.callback(
    Output("kpi-internacoes", "children"), Output("kpi-gastos", "children"), Output("kpi-custo-medio", "children"),
    Output("kpi-maior-uf", "children"), Output("kpi-maior-mun", "children"), Output("grafico-gastos-uf", "figure"),
    Output("grafico-gastos-municipio", "figure"), Output("grafico-evolucao-anual", "figure"),
    Output("grafico-distribuicao-grupo", "figure"), Output("grafico-top-municipios", "figure"), Output("tabela-detalhada", "data"),
    Input("filtro-ano", "value"), Input("filtro-uf", "value"), Input("filtro-municipio", "value"),
    Input("filtro-grupo", "value"), Input("filtro-subgrupo", "value")
)
def pipeline_dashboard(ano, uf, municipio, grupo, subgrupo):
    df_f = df.copy()

    if uf: df_f = df_f[df_f["uf_sigla"] == uf]
    if municipio: df_f = df_f[df_f["nome_municipio"] == municipio]

    df_temporal = df_f.copy()
    if ano: df_f = df_f[df_f["ano_aih"] == int(ano)]

    coluna_alvo = "vl_total"
    filtrado_por_procedimento = False

    # Lógica inteligente e combinada de filtragem estrutural
    if subgrupo:
        df_f = df_f[df_f[subgrupo] > 0]
        df_temporal = df_temporal[df_temporal[subgrupo] > 0]
        coluna_alvo = subgrupo
        filtrado_por_procedimento = True
        df_f["vl_total"] = df_f[subgrupo]
    elif grupo:
        df_f = df_f[df_f[grupo] > 0]
        df_temporal = df_temporal[df_temporal[grupo] > 0]
        coluna_alvo = grupo
        filtrado_por_procedimento = True
        df_f["vl_total"] = df_f[grupo]

    if df_f.empty:
        return "0", "R$ 0,00", "R$ 0,00", "N/A", "N/A", go.Figure(), go.Figure(), go.Figure(), go.Figure(), go.Figure(), []

    if filtrado_por_procedimento:
        total_int = len(df_f)
    else:
        total_int = df_f["qtd_total"].sum()

    total_gasto = df_f[coluna_alvo].sum()
    df_media_mun = df_f.groupby("nome_municipio")[coluna_alvo].sum()
    media_municipio = df_media_mun.mean() if not df_media_mun.empty else 0

    # Formatadores PT-BR
    def formatar_valor_ptbr(valor):
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def formatar_valor_kpi(valor):
        if valor >= 1_000_000_000: return f"R$ {valor / 1_000_000_000:,.2f} Bi".replace(".", ",").replace(",", ".", 1)
        elif valor >= 1_000_000: return f"R$ {valor / 1_000_000:,.2f} Mi".replace(".", ",").replace(",", ".", 1)
        else: return formatar_valor_ptbr(valor)

    df_uf_max = df_f.groupby("uf_sigla")["vl_total"].sum()
    maior_uf = f"{DE_PAR_UFS.get(df_uf_max.idxmax(), df_uf_max.idxmax())} - {formatar_valor_kpi(df_uf_max.max())}" if not df_uf_max.empty and df_uf_max.max() > 0 else "N/A"
    
    df_mun_max = df_f.groupby("nome_municipio")["vl_total"].sum()
    if not df_mun_max.empty and df_mun_max.max() > 0:
        mun_id = df_mun_max.idxmax()
        uf_pertencente = df_f[df_f['nome_municipio'] == mun_id]['uf_sigla'].values[0]
        maior_mun = f"{mun_id} ({uf_pertencente})"
    else:
        maior_mun = "N/A"

    str_int = f"{int(total_int):,}".replace(",", ".")
    str_gas = formatar_valor_kpi(total_gasto)
    str_med = formatar_valor_kpi(media_municipio)

    label_hover_config = dict(bgcolor="#2323FF", bordercolor="#39FF14", font_size=13, font_color="#FFFFFF", font_family="DM Sans")

    # GRÁFICO 1: Gastos por UF
    df_g_uf = df_f.groupby(["uf_sigla", "uf_extenso"])["vl_total"].sum().reset_index().sort_values(by="vl_total", ascending=False).head(14)
    df_g_uf["vl_ptbr"] = df_g_uf["vl_total"].apply(formatar_valor_ptbr)
    fig_uf = px.bar(df_g_uf, x="uf_sigla", y="vl_total", custom_data=["uf_extenso", "vl_ptbr"], title="Gastos Hospitalares por UF", color_discrete_sequence=["#00ffff"])
    fig_uf.update_traces(hovertemplate="<b>%{customdata[0]}</b><br>Valor Destinado: %{customdata[1]}<extra></extra>", hoverlabel=label_hover_config)
    fig_uf.update_layout(template="plotly_dark", paper_bgcolor="#050505", plot_bgcolor="#050505", margin=dict(l=20, r=20, t=40, b=20), xaxis_title="UF", yaxis_title="Montante (R$)")

    # GRÁFICO 2: Gastos por Município
    df_g_mun = df_f.groupby("nome_municipio")["vl_total"].sum().reset_index().sort_values(by="vl_total", ascending=False).head(14)
    df_g_mun["vl_ptbr"] = df_g_mun["vl_total"].apply(formatar_valor_ptbr)
    fig_mun = px.bar(df_g_mun, x="nome_municipio", y="vl_total", custom_data=["vl_ptbr"], title="Gastos Hospitalares por Município", color_discrete_sequence=["#FF5C00"])
    fig_mun.update_traces(hovertemplate="<b>%{x}</b><br>Valor Destinado: %{customdata[0]}<extra></extra>", hoverlabel=label_hover_config)
    fig_mun.update_layout(template="plotly_dark", paper_bgcolor="#050505", plot_bgcolor="#050505", margin=dict(l=20, r=20, t=40, b=20), xaxis_title="Município", yaxis_title="Montante (R$)")

    # GRÁFICO 3: Linha do Tempo Corrigida (Calcula estritamente o macro/micro selecionado)
    df_g_time = df_temporal.groupby("ano_aih")[coluna_alvo].sum().reset_index().sort_values(by="ano_aih")
    df_g_time["vl_ptbr"] = df_g_time[coluna_alvo].apply(formatar_valor_ptbr)
    fig_time = px.line(df_g_time, x="ano_aih", y=coluna_alvo, markers=True, custom_data=["vl_ptbr"], title="Evolução Anual Histórica do Orçamento")
    fig_time.update_traces(line_color="#39FF14", marker=dict(color="#FFFF00", size=8), hovertemplate="<b>Ano: %{x}</b><br>Orçamento SUS: %{customdata[0]}<extra></extra>", hoverlabel=label_hover_config)
    fig_time.update_layout(template="plotly_dark", paper_bgcolor="#050505", plot_bgcolor="#050505", margin=dict(l=20, r=20, t=40, b=20), xaxis=dict(type='category', title="Ano"), yaxis_title="Gasto Acumulado (R$)")

    # GRÁFICO 4: Pizza Inteligente (Bug corrigido de group -> grupo)
    if subgrupo:
        pai = PAI_DO_SUBGRUPO[subgrupo]
        mapeamento_filhos = SUBGRUPOS_POR_GRUPO[pai]
        grupos_labels = list(mapeamento_filhos.values())
        grupos_valores = [df_f[col].sum() for col in mapeamento_filhos.keys()]
        titulo_pizza = f"Contexto Interno: Subgrupos de {NOMES_GRUPOS[pai]}"
    elif grupo and grupo in SUBGRUPOS_POR_GRUPO:
        mapeamento_filhos = SUBGRUPOS_POR_GRUPO[grupo]
        grupos_labels = list(mapeamento_filhos.values())
        grupos_valores = [df_f[col].sum() for col in mapeamento_filhos.keys()]
        titulo_pizza = f"Abertura de Subgrupos: {NOMES_GRUPOS[grupo]}"
    elif grupo:
        nome_atual = NOMES_GRUPOS.get(grupo, "Selecionado")
        total_geral_painel = df_f["vl_total"].sum()
        grupos_labels = [nome_atual, 'Demais Custos da Rede']
        grupos_valores = [df_f[grupo].sum(), max(0, total_geral_painel - df_f[grupo].sum())]
        titulo_pizza = f"Participação do Grupo: {nome_atual}"
    else:
        grupos_labels = ['Diagnóstico', 'Clínico', 'Cirúrgico', 'Transplantes', 'OPME']
        grupos_valores = [df_f['vl_02'].sum(), df_f['vl_03'].sum(), df_f['vl_04'].sum(), df_f['vl_05'].sum(), df_f['vl_07'].sum()]
        titulo_pizza = "Distribuição de Recursos por Grupo SUS"

    valores_fatias_ptbr = [formatar_valor_ptbr(v) for v in grupos_valores]

    fig_pie = go.Figure(data=[go.Pie(
        labels=grupos_labels, values=grupos_valores, hole=.4,
        customdata=valores_fatias_ptbr,
        marker=dict(colors=["#00ffff", "#39FF14", "#FF5C00", "#FFFF00", "#FF007F"]),
        hovertemplate="<b>Grupo: %{label}</b><br>Representação: %{percent}<br>Valor: %{customdata}<extra></extra>",
        hoverlabel=label_hover_config,
        textfont=dict(size=15, weight='bold')
    )])
    fig_pie.update_layout(template="plotly_dark", paper_bgcolor="#050505", plot_bgcolor="#050505", title=titulo_pizza, margin=dict(l=20, r=20, t=40, b=20))

    # GRÁFICO 5: Top 10 Municípios Críticos
    df_top10 = df_f.groupby("nome_municipio")["vl_total"].sum().reset_index().sort_values(by="vl_total", ascending=False).head(10)
    df_top10["vl_ptbr"] = df_top10["vl_total"].apply(formatar_valor_ptbr)
    fig_top = px.bar(df_top10, x="vl_total", y="nome_municipio", orientation="h", custom_data=["vl_ptbr"], title="Top 10 Municípios com Maior Pressão Orçamentária", color="vl_total", color_continuous_scale=["#002200", "#39FF14", "#FFFF00", "#FF5C00"])
    fig_top.update_traces(hovertemplate="<b>%{y}</b><br>Valor Destinado: %{customdata[0]}<extra></extra>", hoverlabel=label_hover_config)
    fig_top.update_layout(template="plotly_dark", paper_bgcolor="#050505", plot_bgcolor="#050505", margin=dict(l=40, r=20, t=40, b=20), xaxis_title="Custo Repassado (R$)", yaxis_title="")

    # TABELA DE DETALHAMENTO ANALÍTICO
    df_tab = df_f.sort_values(by="vl_total", ascending=False).head(150).copy()
    df_tab["qtd_total_formatada"] = df_tab["qtd_total"].apply(lambda x: f"{int(x):,}".replace(",", "."))
    df_tab["vl_total_formatado"] = df_tab["vl_total"].apply(formatar_valor_ptbr)

    return str_int, str_gas, str_med, maior_uf, maior_mun, fig_uf, fig_mun, fig_time, fig_pie, fig_top, df_tab.to_dict("records")

# ==============================================================================
# DISPARO DO SERVIDOR DE PRODUÇÃO
# ==============================================================================
if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=False)
