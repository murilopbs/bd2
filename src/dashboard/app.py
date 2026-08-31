"""
Dashboard Interativo de Apoio à Decisão - Retenção e Formatura na UnB
Desenvolvido para o Decanato de Ensino de Graduação (DEG/UnB)
Challenge de Dados Abertos da UnB - Metodologia CBL
"""

import json
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Painel de Retenção e Formatura UnB",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilização CSS customizada
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
    .metric-val {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1E40AF;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #64748B;
    }
    .badge-critica {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
GOLD_DIR = BASE_DIR / "data" / "gold"
DOCS_DIR = BASE_DIR / "docs"


@st.cache_data
def load_gold_data():
    csv_path = GOLD_DIR / "retencao_cursos_unb.csv"
    json_path = GOLD_DIR / "metricas_gerais_unb.json"
    join_path = GOLD_DIR / "relatorio_casamento_joins.json"
    
    if not csv_path.exists():
        st.error(f"Arquivo {csv_path} não encontrado. Execute o pipeline primeiro.")
        return None, None, None
        
    df = pd.read_csv(csv_path)
    with open(json_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    with open(join_path, "r", encoding="utf-8") as f:
        join_meta = json.load(f)
        
    return df, meta, join_meta


df_gold, global_meta, join_meta = load_gold_data()

# Barra Lateral (Sidebar)
st.sidebar.image("https://dados.unb.br/uploads/group/2019-11-01-175835.512234iconensino.png", width=180)
st.sidebar.title("🎓 Painel UnB")
st.sidebar.markdown("**Projeto**: Retenção e Formatura nos Cursos da UnB")
st.sidebar.markdown(f"**Taxa de Casamento**: `{join_meta.get('taxa_de_casamento_pct', 97.54)}%`")
st.sidebar.markdown("---")

tab_choice = st.sidebar.radio(
    "Navegação:",
    [
        "📊 Visão Executiva (DEG)",
        "🔍 Detalhe por Curso",
        "⚖️ Noturno vs. Diurno & Turnos",
        "🛠️ Auditoria & Qualidade de Dados",
        "⚠️ O Que Este Dado NÃO Responde",
    ],
)

if df_gold is not None:
    # Header Principal
    st.markdown('<div class="main-header">🎓 Observatório de Retenção e Formatura da UnB</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Mapeamento do tempo real de integralização curricular, retenção crítica e evasão baseado nos Dados Abertos da UnB.</div>', unsafe_allow_html=True)

    if tab_choice == "📊 Visão Executiva (DEG)":
        # KPIs Globais
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric(
                label="Total de Discentes Auditados",
                value=f"{global_meta['total_discentes_analisados']:,}",
                help="Discentes de graduação consolidados na camada Gold.",
            )
        with c2:
            st.metric(
                label="Tempo Médio Real de Formatura",
                value=f"{global_meta['tempo_medio_formatura_global_semestres']} sem.",
                help="Média em semestres entre o ingresso e a formatura na UnB.",
            )
        with c3:
            st.metric(
                label="Formatura no Prazo Ideal",
                value=f"{global_meta['taxa_conclusao_tempo_ideal_global_pct']}%",
                help="Percentual de egressos que integralizam o curso dentro do prazo da matriz.",
            )
        with c4:
            n_criticos = (df_gold["classificacao_retencao"] == "RETENÇÃO CRÍTICA").sum()
            st.metric(
                label="Cursos em Retenção Crítica",
                value=f"{n_criticos} cursos",
                delta=f"Top 25% mais retentores",
                delta_color="inverse",
            )

        st.markdown("---")

        # Gráfico Scatter: Atraso vs Evasão
        st.subheader("🎯 Matriz de Retenção Crítica: Atraso de Formatura vs. Taxa de Evasão")
        st.markdown(
            "Cursos no quadrante superior direito combinam **alto atraso na formatura** e **alta taxa de evasão**, exigindo intervenção pedagógica prioritária."
        )

        fig_scatter = px.scatter(
            df_gold,
            x="desvio_medio_semestres",
            y="taxa_evasao_pct",
            size="total_discentes_registrados",
            color="classificacao_retencao",
            hover_name="curso",
            hover_data={
                "tempo_medio_real_semestres": ":.1f",
                "semestre_ideal_previsto": ":.0f",
                "taxa_formatura_pct": ":.1f%",
                "campus": True,
            },
            labels={
                "desvio_medio_semestres": "Atraso Médio na Formatura (Semestres além do Ideal)",
                "taxa_evasao_pct": "Taxa de Evasão / Desligamento (%)",
                "classificacao_retencao": "Grau de Retenção",
            },
            color_discrete_map={
                "RETENÇÃO CRÍTICA": "#DC2626",
                "RETENÇÃO ALTA": "#F59E0B",
                "RETENÇÃO MÉDIA": "#3B82F6",
                "RETENÇÃO BAIXA": "#10B981",
            },
            height=500,
        )
        fig_scatter.add_vline(x=0, line_dash="dash", line_color="#9CA3AF")
        fig_scatter.add_hline(y=df_gold["taxa_evasao_pct"].median(), line_dash="dash", line_color="#9CA3AF")
        st.plotly_chart(fig_scatter, use_container_width=True)

        # Ranking dos Cursos
        col_left, col_right = st.columns(2)
        with col_left:
            st.subheader("🚨 Top 10 Cursos com Maior Retenção Crítica (IRC)")
            top_retencao = df_gold.head(10)[
                ["curso", "tempo_medio_real_semestres", "desvio_medio_semestres", "taxa_evasao_pct", "indice_retencao_critica"]
            ].rename(
                columns={
                    "curso": "Curso",
                    "tempo_medio_real_semestres": "Tempo Real (sem.)",
                    "desvio_medio_semestres": "Atraso (sem.)",
                    "taxa_evasao_pct": "Evasão (%)",
                    "indice_retencao_critica": "Score IRC",
                }
            )
            st.dataframe(top_retencao, use_container_width=True, hide_index=True)

        with col_right:
            st.subheader("⭐ Top 10 Cursos com Maior Formatura no Prazo Ideal")
            top_pontuais = df_gold.sort_values(by="formados_tempo_ideal_pct", ascending=False).head(10)[
                ["curso", "semestre_ideal_previsto", "formados_tempo_ideal_pct", "taxa_formatura_pct"]
            ].rename(
                columns={
                    "curso": "Curso",
                    "semestre_ideal_previsto": "Tempo Ideal (sem.)",
                    "formados_tempo_ideal_pct": "% No Prazo Ideal",
                    "taxa_formatura_pct": "Taxa Formatura (%)",
                }
            )
            st.dataframe(top_pontuais, use_container_width=True, hide_index=True)

    elif tab_choice == "🔍 Detalhe por Curso":
        st.subheader("🔍 Raio-X Acadêmico por Curso")
        
        course_list = sorted(df_gold["curso"].unique())
        selected_course = st.selectbox("Selecione o Curso para detalhamento:", course_list)
        
        row_course = df_gold[df_gold["curso"] == selected_course].iloc[0]
        
        # Metadados do curso
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Tempo Médio Real", f"{row_course['tempo_medio_real_semestres']:.1f} sem.")
        with m2:
            st.metric("Tempo Ideal da Matriz", f"{row_course['semestre_ideal_previsto']:.0f} sem.")
        with m3:
            st.metric("Desvio Médio", f"{row_course['desvio_medio_semestres']:+.1f} sem.")
        with m4:
            st.metric("Taxa de Formatura", f"{row_course['taxa_formatura_pct']:.1f}%")

        st.markdown("---")
        
        c_chart1, c_chart2 = st.columns(2)
        with c_chart1:
            st.markdown("##### ⏱️ Distribuição de Tempo dos Formados")
            df_dist = pd.DataFrame({
                "Faixa de Conclusão": ["Tempo Mínimo", "Tempo Ideal", "Acima do Ideal", "Limite Jubilamento"],
                "Percentual": [
                    row_course["formados_tempo_minimo_pct"],
                    row_course["formados_tempo_ideal_pct"],
                    row_course["formados_acima_ideal_pct"],
                    row_course["formados_limite_maximo_pct"],
                ],
            })
            fig_bar = px.bar(
                df_dist,
                x="Faixa de Conclusão",
                y="Percentual",
                color="Faixa de Conclusão",
                color_discrete_sequence=["#10B981", "#3B82F6", "#F59E0B", "#DC2626"],
                text_auto=".1f",
                height=350,
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with c_chart2:
            st.markdown("##### 🚪 Desfecho das Movimentações Acadêmicas")
            n_form = row_course["total_formados"]
            n_evad = row_course["total_evadidos_desligados"]
            n_outros = max(0, row_course["total_discentes_registrados"] - n_form - n_evad)
            
            df_pie = pd.DataFrame({
                "Desfecho": ["Formatura", "Evasão / Desligamento", "Outros / Mudança"],
                "Quantidade": [n_form, n_evad, n_outros],
            })
            fig_pie = px.pie(
                df_pie,
                names="Desfecho",
                values="Quantidade",
                color="Desfecho",
                color_discrete_map={
                    "Formatura": "#10B981",
                    "Evasão / Desligamento": "#DC2626",
                    "Outros / Mudança": "#6B7280",
                },
                height=350,
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    elif tab_choice == "⚖️ Noturno vs. Diurno & Turnos":
        st.subheader("⚖️ Comparativo de Formatura e Evasão por Turno (GQ 4)")
        
        st.markdown(
            "Análise do impacto do turno na permanência estudantil. *Nota: Cursos noturnos já têm prazos ideais maiores em suas matrizes.*"
        )
        
        df_turno = df_gold.groupby("turno").agg({
            "tempo_medio_real_semestres": "mean",
            "semestre_ideal_previsto": "mean",
            "desvio_medio_semestres": "mean",
            "taxa_evasao_pct": "mean",
            "taxa_formatura_pct": "mean",
            "total_discentes_registrados": "sum",
        }).reset_index()

        c1, c2 = st.columns(2)
        with c1:
            fig_turno_evas = px.bar(
                df_turno,
                x="turno",
                y="taxa_evasao_pct",
                title="Taxa Média de Evasão por Turno (%)",
                color="turno",
                text_auto=".1f",
                height=380,
            )
            st.plotly_chart(fig_turno_evas, use_container_width=True)
            
        with c2:
            fig_turno_tempo = px.bar(
                df_turno,
                x="turno",
                y=["semestre_ideal_previsto", "tempo_medio_real_semestres"],
                barmode="group",
                title="Tempo Ideal Previsto vs. Tempo Médio Real (Semestres)",
                labels={"value": "Semestres", "variable": "Métrica"},
                height=380,
            )
            st.plotly_chart(fig_turno_tempo, use_container_width=True)

    elif tab_choice == "🛠️ Auditoria & Qualidade de Dados":
        st.subheader("🛠️ Auditoria de Qualidade de Dados Abertos (Dia 4 - S1)")
        st.markdown("Verificação de integridade nas bases brutas do portal `dados.unb.br`.")
        
        relatorio_path = DOCS_DIR / "relatorio_qualidade.md"
        if relatorio_path.exists():
            with open(relatorio_path, "r", encoding="utf-8") as f:
                st.markdown(f.read())
        else:
            st.info("Relatório de qualidade não encontrado.")

    elif tab_choice == "⚠️ O Que Este Dado NÃO Responde":
        st.subheader("⚠️ Slide Obrigatório: O Que Este Dado NÃO Responde")
        st.markdown(
            """
            Para manter o rigor metodológico e científico na tomada de decisão do DEG:
            
            1. **Motivos Individuais de Evasão**: Os dados abertos não informam razões socioeconômicas, de saúde mental, incompatibilidade de horário de trabalho ou insatisfação com a carreira.
            2. **Semestre Exato de Ingresso no SIGRA**: O arquivo registra `ano_ingresso` com 4 dígitos (ex: `2010`) sem discriminar 1º ou 2º semestre, gerando uma incerteza metodológica de $\pm 1$ semestre.
            3. **Histórico de Migração Curricular Individual**: Discentes que ingressaram em matrizes antigas e migraram para matrizes novas não têm os créditos convalidados discriminados no dataset estático.
            4. **Efeito Causal Direto**: Uma alta taxa de retenção reflete uma combinação de complexidade de conteúdo, rigidez na cadeia de pré-requisitos, insuficiência de oferta de vagas e perfil de dedicação do estudante.
            """
        )
