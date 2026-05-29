import os
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output

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
# CONEXÃO COM O BANCO DE DADOS
# ==============================================================================
HOST = "bigdata.dataiesb.com"
BANCO = "iesb"
USUARIO = "data_iesb"
SENHA = "iesb"
PORTA = "5432"

engine = create_engine(f"postgresql://{USUARIO}:{SENHA}@{HOST}:{PORTA}/{BANCO}")

query = """
SELECT
    ano_aih, uf_sigla, nome_municipio, regiao_nome,
    AVG(numero_habitantes) as numero_habitantes,
    SUM(qtd_total) as qtd_total, SUM(vl_total) as vl_total,
    SUM(vl_02) as vl_02, SUM(vl_03) as vl_03, SUM(vl_04) as vl_04, SUM(vl_05) as vl_05, SUM(vl_07) as vl_07,
    SUM(vl_0409) as vl_0409, SUM(vl_0415) as vl_0415, SUM(vl_0304) as vl_0304, SUM(vl_0201) as vl_0201, SUM(vl_0202) as vl_0202
FROM sus_aih
GROUP BY ano_aih, uf_sigla, nome_municipio, regiao_nome;
"""

df = pd.read_sql(query, con=engine)
df['uf_sigla'] = df['uf_sigla'].str.strip().str.upper()
df['nome_municipio'] = df['nome_municipio'].str.strip()
df['regiao_nome'] = df['regiao_nome'].str.strip()
colunas_valores = [c for c in df.columns if c.startswith('vl_') or c.startswith('qtd_')]
df[colunas_valores] = df[colunas_valores].fillna(0)
df['numero_habitantes'] = df['numero_habitantes'].fillna(0).astype(int)
df['ano_aih'] = df['ano_aih'].astype(int)

anos_disponiveis = sorted(df['ano_aih'].unique())
ufs_disponiveis = sorted(df['uf_sigla'].unique())
opcoes_anos = [{"label": str(a), "value": a} for a in anos_disponiveis]

# ==============================================================================
# CONFIGURAÇÃO DO DASHBOARD
# ==============================================================================
app = dash.Dash(__name__)
server = app.server  # Crucial para o Gunicorn funcionar na nuvem

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
            html.Div([html.Label("Grupo SUS", style={"font-size": "11px", "color": "#888888"}), dcc.Dropdown(id="filtro-grupo", options=[
                {"label": "02 - Diagnóstico", "value": "vl_02"}, {"label": "03 - Clínico", "value": "vl_03"}, {"label": "04 - Cirúrgico", "value": "vl_04"}, {"label": "05 - Transplantes", "value": "vl_05"}, {"label": "07 - OPME", "value": "vl_07"}
            ], placeholder="Todos", clearable=True)], style={"width": "160px", "margin-right": "10px"}),
            html.Div([html.Label("Subgrupo Crítico", style={"font-size": "11px", "color": "#888888"}), dcc.Dropdown(id="filtro-subgrupo", options=[
                {"label": "0409 - Ortopedia", "value": "vl_0409"}, {"label": "0415 - Trauma", "value": "vl_0415"}, {"label": "0304 - Partos", "value": "vl_0304"}, {"label": "0201 - Exames Lab", "value": "vl_0201"}, {"label": "0202 - Imagem", "value": "vl_0202"}
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

@app.callback(Output("filtro-municipio", "options"), Input("filtro-uf", "value"))
def atualizar_dropdown_municipios(uf_selecionada):
    if not uf_selecionada:
        return [{"label": m, "value": m} for m in sorted(df["nome_municipio"].unique())]
    return [{"label": m, "value": m} for m in sorted(df[df["uf_sigla"] == uf_selecionada]["nome_municipio"].unique())]

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
    if ano: df_f = df_f[df_f["ano_aih"] == int(ano)]
    if uf: df_f = df_f[df_f["uf_sigla"] == uf]
    if municipio: df_f = df_f[df_f["nome_municipio"] == municipio]
    if subgrupo:
        df_f = df_f[df_f[subgrupo] > 0]
        df_f["vl_total"] = df_f[subgrupo]
    elif grupo:
        df_f = df_f[df_f[grupo] > 0]
        df_f["vl_total"] = df_f[grupo]

    if df_f.empty:
        return "0", "R$ 0,00", "R$ 0,00", "N/A", "N/A", go.Figure(), go.Figure(), go.Figure(), go.Figure(), go.Figure(), []

    total_int = df_f["qtd_total"].sum()
    total_gasto = df_f["vl_total"].sum()
    media_municipio = df_f.groupby("nome_municipio")["vl_total"].sum().mean()

    def fmt_kpi(v):
        if v >= 1e9: return f"R$ {v/1e9:,.2f} Bi".replace(".", ",").replace(",", ".", 1)
        if v >= 1e6: return f"R$ {v/1e6:,.2f} Mi".replace(".", ",").replace(",", ".", 1)
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    df_uf_max = df_f.groupby("uf_sigla")["vl_total"].sum()
    maior_uf = f"{df_uf_max.idxmax()} - {fmt_kpi(df_uf_max.max())}" if not df_uf_max.empty else "N/A"
    df_mun_max = df_f.groupby("nome_municipio")["vl_total"].sum()
    maior_mun = f"{df_mun_max.idxmax()} ({df_f[df_f['nome_municipio'] == df_mun_max.idxmax()]['uf_sigla'].values[0]})" if not df_mun_max.empty else "N/A"

    str_int = f"{int(total_int):,}".replace(",", ".")
    str_gas = fmt_kpi(total_gasto)
    str_med = fmt_kpi(media_municipio)

    fig_uf = px.bar(df_f.groupby("uf_sigla")["vl_total"].sum().reset_index().sort_values(by="vl_total", ascending=False).head(14), x="uf_sigla", y="vl_total", title="Gastos Hospitalares por UF", color_discrete_sequence=["#00ffff"])
    fig_uf.update_layout(template="plotly_dark", paper_bgcolor="#050505", plot_bgcolor="#050505", margin=dict(l=20, r=20, t=40, b=20))

    fig_mun = px.bar(df_f.groupby("nome_municipio")["vl_total"].sum().reset_index().sort_values(by="vl_total", ascending=False).head(14), x="nome_municipio", y="vl_total", title="Gastos Hospitalares por Município", color_discrete_sequence=["#FF5C00"])
    fig_mun.update_layout(template="plotly_dark", paper_bgcolor="#050505", plot_bgcolor="#050505", margin=dict(l=20, r=20, t=40, b=20))

    df_temp = df.copy()
    if uf: df_temp = df_temp[df_temp["uf_sigla"] == uf]
    if municipio: df_temp = df_temp[df_temp["nome_municipio"] == municipio]
    if subgrupo: df_temp["vl_total"] = df_temp[subgrupo]
    elif grupo: df_temp["vl_total"] = df_temp[grupo]
    fig_time = px.line(df_temp.groupby("ano_aih")["vl_total"].sum().reset_index().sort_values(by="ano_aih"), x="ano_aih", y="vl_total", markers=True, title="Evolução Anual Histórica do Orçamento")
    fig_time.update_traces(line_color="#39FF14", marker=dict(color="#FFFF00", size=8))
    fig_time.update_layout(template="plotly_dark", paper_bgcolor="#050505", plot_bgcolor="#050505", margin=dict(l=20, r=20, t=40, b=20), xaxis=dict(type='category'))

    fig_pie = go.Figure(data=[go.Pie(labels=['Diagnóstico', 'Clínico', 'Cirúrgico', 'Transplantes', 'OPME'], values=[df_f['vl_02'].sum(), df_f['vl_03'].sum(), df_f['vl_04'].sum(), df_f['vl_05'].sum(), df_f['vl_07'].sum()], hole=.4, marker=dict(colors=["#00ffff", "#39FF14", "#FF5C00", "#FFFF00", "#FF007F"]))])
    fig_pie.update_layout(template="plotly_dark", paper_bgcolor="#050505", plot_bgcolor="#050505", title="Distribuição de Recursos por Grupo SUS", margin=dict(l=20, r=20, t=40, b=20))

    fig_top = px.bar(df_f.groupby(["nome_municipio", "uf_sigla"])["vl_total"].sum().reset_index().sort_values(by="vl_total", ascending=False).head(10), x="vl_total", y="nome_municipio", orientation="h", title="Top 10 Municípios com Maior Pressão Orçamentária", color="vl_total", color_continuous_scale=["#002200", "#39FF14", "#FFFF00", "#FF5C00"])
    fig_top.update_layout(template="plotly_dark", paper_bgcolor="#050505", plot_bgcolor="#050505", margin=dict(l=40, r=20, t=40, b=20))

    df_tab = df_f.sort_values(by="vl_total", ascending=False).head(150).copy()
    df_tab["qtd_total_formatada"] = df_tab["qtd_total"].apply(lambda x: f"{int(x):,}".replace(",", "."))
    df_tab["vl_total_formatado"] = df_tab["vl_total"].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    return str_int, str_gas, str_med, maior_uf, maior_mun, fig_uf, fig_mun, fig_time, fig_pie, fig_top, df_tab.to_dict("records")

if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=False)
