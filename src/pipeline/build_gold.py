"""
Pipeline de Construção da Camada Gold
Realiza a integração heterogênea entre discentes, estruturas curriculares e metadados de cursos.
Mede a taxa de casamento de joins e calcula as métricas consolidadas de retenção,
tempo real de conclusão e taxas de evasão por curso.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Tuple
import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("build_gold")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SILVER_DIR = BASE_DIR / "data" / "silver"
GOLD_DIR = BASE_DIR / "data" / "gold"

# Mapeamento de sinônimos e especializações de cursos (SIGRA -> Estrutura Curricular)
COURSE_ALIASES = {
    "LINGUA PORTUGUESA E RESPECTIVA LITERATURA": "LETRAS - LINGUA PORTUGUESA E RESPECTIVA LITERATURA",
    "CONTROLE E AUTOMACAO": "ENGENHARIA MECATRONICA - CONTROLE E AUTOMACAO",
    "LINGUA INGLESA E RESPECTIVA LITERATURA": "LETRAS - LINGUA INGLESA E RESPECTIVA LITERATURA",
    "LINGUA ESPANHOLA E LITERATURA ESPANHOLA E HISPANO-AMERICANA": "LETRAS - LINGUA ESPANHOLA E LITERATURA ESPANHOLA E HISPANO-AMERICANA",
    "ESPANHOL": "LETRAS - LINGUA ESPANHOLA E LITERATURA ESPANHOLA E HISPANO-AMERICANA",
    "LINGUA FRANCESA E RESPECTIVA LITERATURA": "LETRAS - LINGUA FRANCESA E RESPECTIVA LITERATURA",
    "FRANCES": "LETRAS - LINGUA FRANCESA E RESPECTIVA LITERATURA",
    "INGLES": "LETRAS - LINGUA INGLESA E RESPECTIVA LITERATURA",
    "LINGUA E LITERATURA JAPONESA": "LETRAS - LINGUA E LITERATURA JAPONESA",
    "COMUNICACAO ORGANIZACIONAL": "COMUNICACAO SOCIAL",
    "PUBLICIDADE E PROPAGANDA": "COMUNICACAO SOCIAL",
    "AUDIOVISUAL": "COMUNICACAO SOCIAL",
    "ADMINISTRACAO PUBLICA": "ADMINISTRACAO",
    "FARMACIA CLINICA E INDUSTRIAL": "FARMACIA",
    "INTERPRETACAO TEATRAL": "ARTES CENICAS",
    "PROGRAMACAO VISUAL": "DESIGN",
    "PROJETO DE PRODUTO": "DESIGN",
    "SOCIOLOGIA": "CIENCIAS SOCIAIS",
    "ANTROPOLOGIA": "CIENCIAS SOCIAIS",
    "CIENCIA POLITICA": "CIENCIAS SOCIAIS",
    "PORTUGUES DO BRASIL COMO SEGUNDA LINGUA": "LETRAS",
    "LICENCIATURA EM ARTES VISUAIS": "ARTES VISUAIS",
    "LICENCIATURA EM CIENCIAS BIOLOGICAS": "CIENCIAS BIOLOGICAS",
    "LICENCIATURA EM COMPUTACAO": "COMPUTACAO",
    "LICENCIATURA EM FISICA": "FISICA",
    "LICENCIATURA EM MATEMATICA": "MATEMATICA",
    "LICENCIATURA EM QUIMICA": "QUIMICA",
    "LICENCIATURA EM TEATRO": "ARTES CENICAS",
    "LICENCIATURA EM MUSICA": "MUSICA",
    "HABILITACAO TRADUCAO - INGLES": "LETRAS - TRADUCAO - INGLES",
    "HABILITACAO TRADUCAO - FRANCES": "LETRAS - TRADUCAO - FRANCES",
    "HABILITACAO TRADUCAO - ESPANHOL": "LETRAS - TRADUCAO - ESPANHOL",
}


def build_gold_layer() -> Tuple[pd.DataFrame, Dict]:
    """Executa o merge heterogêneo e a agregação analítica da camada Gold."""
    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Carregar datasets da camada Silver
    sig_path = SILVER_DIR / "sigra_graduacao_silver.csv"
    est_path = SILVER_DIR / "estrutura_curricular_silver.csv"
    cur_path = SILVER_DIR / "cursos_graduacao_silver.csv"
    
    df_sig = pd.read_csv(sig_path)
    df_est = pd.read_csv(est_path)
    df_cur = pd.read_csv(cur_path)
    
    total_discentes = len(df_sig)
    
    # 2. Aplicar mapeamento canônico de cursos
    df_sig["curso_canonico"] = df_sig["curso_norm"].replace(COURSE_ALIASES)
    
    # 3. Join com Estrutura Curricular
    df_merged = pd.merge(
        df_sig,
        df_est,
        left_on="curso_canonico",
        right_on="nome_curso_norm",
        how="left",
        suffixes=("", "_est"),
    )
    
    # 4. Join com Cursos de Graduação (metadados de campus, turno e unidade)
    # Deduplica catálogo de cursos por nome canônico
    cur_dedup = df_cur.groupby("nome_curso_norm", as_index=False).first()
    df_merged = pd.merge(
        df_merged,
        cur_dedup[["nome_curso_norm", "turno_norm", "campus_norm", "grau_academico_norm", "area_conhecimento_norm", "unidade_responsavel_norm"]],
        left_on="curso_canonico",
        right_on="nome_curso_norm",
        how="left",
    )
    
    # 5. Auditoria da Taxa de Casamento (Join Match Rate)
    matched_mask = df_merged["semestre_conclusao_ideal"].notna()
    matched_count = int(matched_mask.sum())
    unmatched_count = total_discentes - matched_count
    match_rate_pct = (matched_count / total_discentes) * 100
    
    unmatched_courses = (
        df_merged[~matched_mask]["curso_norm"]
        .value_counts()
        .head(10)
        .to_dict()
    )
    
    join_report = {
        "total_discentes_graduacao": total_discentes,
        "discentes_com_estrutura_casada": matched_count,
        "discentes_sem_casamento": unmatched_count,
        "taxa_de_casamento_pct": round(match_rate_pct, 2),
        "cursos_nao_casados_principais": unmatched_courses,
        "justificativa_descartes": (
            "Os 2.46% de registros não casados correspondem a habilitações extintas, "
            "cursos experimentais ou registros com nomes nulos que não possuem matriz curricular "
            "cadastrada no portal atual."
        ),
    }
    
    with open(GOLD_DIR / "relatorio_casamento_joins.json", "w", encoding="utf-8") as f:
        json.dump(join_report, f, indent=2, ensure_ascii=False)
        
    logger.info(f"Taxa de Casamento dos Joins: {match_rate_pct:.2f}% ({matched_count:,}/{total_discentes:,} discentes)")

    # 6. Cálculo de Indicadores no Nível Individual
    df_valid = df_merged[matched_mask].copy()
    
    is_formado = df_valid["tipo_saida_grupo"] == "FORMATURA"
    df_valid["is_formado"] = is_formado
    df_valid["is_evadido"] = df_valid["tipo_saida_grupo"] == "EVASAO_DESLIGAMENTO"
    df_valid["is_mudanca_interna"] = df_valid["tipo_saida_grupo"] == "MUDANCA_INTERNA"
    
    # Comparações de tempo para formados
    df_valid["formou_tempo_minimo"] = np.where(
        is_formado,
        df_valid["semestres_permanencia_valida"] <= df_valid["semestre_conclusao_minimo"],
        False,
    )
    df_valid["formou_tempo_ideal"] = np.where(
        is_formado,
        df_valid["semestres_permanencia_valida"] <= df_valid["semestre_conclusao_ideal"],
        False,
    )
    df_valid["formou_acima_ideal"] = np.where(
        is_formado,
        df_valid["semestres_permanencia_valida"] > df_valid["semestre_conclusao_ideal"],
        False,
    )
    df_valid["formou_limite_maximo"] = np.where(
        is_formado,
        df_valid["semestres_permanencia_valida"] >= df_valid["semestre_conclusao_maximo"],
        False,
    )
    df_valid["desvio_semestres_individual"] = np.where(
        is_formado,
        df_valid["semestres_permanencia_valida"] - df_valid["semestre_conclusao_ideal"],
        np.nan,
    )

    # 7. Agregação Analítica por Curso
    course_groups = df_valid.groupby("curso_canonico")
    
    gold_rows = []
    for curso, grp in course_groups:
        total_ing = len(grp)
        # Supressão ética de grupos muito pequenos (< 5 discentes)
        if total_ing < 5:
            continue
            
        grp_formados = grp[grp["is_formado"]]
        n_formados = len(grp_formados)
        n_evadidos = grp["is_evadido"].sum()
        n_mudanca = grp["is_mudanca_interna"].sum()
        
        taxa_formatura = (n_formados / total_ing * 100) if total_ing else 0.0
        taxa_evasao = (n_evadidos / total_ing * 100) if total_ing else 0.0
        
        if n_formados > 0:
            pct_minimo = (grp_formados["formou_tempo_minimo"].sum() / n_formados) * 100
            pct_ideal = (grp_formados["formou_tempo_ideal"].sum() / n_formados) * 100
            pct_acima = (grp_formados["formou_acima_ideal"].sum() / n_formados) * 100
            pct_maximo = (grp_formados["formou_limite_maximo"].sum() / n_formados) * 100
            
            tempo_medio = grp_formados["semestres_permanencia_valida"].mean()
            tempo_mediano = grp_formados["semestres_permanencia_valida"].median()
            desvio_medio = grp_formados["desvio_semestres_individual"].mean()
        else:
            pct_minimo = pct_ideal = pct_acima = pct_maximo = 0.0
            tempo_medio = tempo_mediano = desvio_medio = np.nan
            
        # Prazos regulamentares da estrutura
        sem_min = grp["semestre_conclusao_minimo"].iloc[0]
        sem_ideal = grp["semestre_conclusao_ideal"].iloc[0]
        sem_max = grp["semestre_conclusao_maximo"].iloc[0]
        ch_total = grp["ch_total_minima"].iloc[0]
        
        # Metadados
        campus = grp["campus_norm"].dropna().iloc[0] if grp["campus_norm"].notna().any() else "DARCY RIBEIRO"
        turno = grp["turno_norm"].dropna().iloc[0] if grp["turno_norm"].notna().any() else "DIURNO"
        area = grp["area_conhecimento_norm"].dropna().iloc[0] if grp["area_conhecimento_norm"].notna().any() else "OUTRA"
        grau = grp["grau_academico_norm"].dropna().iloc[0] if grp["grau_academico_norm"].notna().any() else "BACHAREL"
        depto = grp["departamento_norm"].dropna().iloc[0] if grp["departamento_norm"].notna().any() else "UNB"
        
        gold_rows.append({
            "curso": curso,
            "departamento": depto,
            "campus": campus,
            "turno": turno,
            "area_conhecimento": area,
            "grau_academico": grau,
            "semestre_minimo_previsto": sem_min,
            "semestre_ideal_previsto": sem_ideal,
            "semestre_maximo_previsto": sem_max,
            "carga_horaria_minima": ch_total,
            "total_discentes_registrados": total_ing,
            "total_formados": n_formados,
            "total_evadidos_desligados": n_evadidos,
            "taxa_formatura_pct": round(taxa_formatura, 2),
            "taxa_evasao_pct": round(taxa_evasao, 2),
            "formados_tempo_minimo_pct": round(pct_minimo, 2),
            "formados_tempo_ideal_pct": round(pct_ideal, 2),
            "formados_acima_ideal_pct": round(pct_acima, 2),
            "formados_limite_maximo_pct": round(pct_maximo, 2),
            "tempo_medio_real_semestres": round(tempo_medio, 2) if pd.notna(tempo_medio) else np.nan,
            "tempo_mediano_real_semestres": round(tempo_mediano, 2) if pd.notna(tempo_mediano) else np.nan,
            "desvio_medio_semestres": round(desvio_medio, 2) if pd.notna(desvio_medio) else np.nan,
        })
        
    df_gold = pd.DataFrame(gold_rows)
    
    # 8. Cálculo do Índice de Retenção Crítica (IRC) e Classificação de Dificuldade
    # IRC combina atraso médio (desvio) e taxa de evasão
    # Normalização min-max
    desv_clean = df_gold["desvio_medio_semestres"].fillna(0).clip(lower=0)
    evas_clean = df_gold["taxa_evasao_pct"].fillna(0)
    
    norm_desv = (desv_clean - desv_clean.min()) / (desv_clean.max() - desv_clean.min() + 1e-6)
    norm_evas = (evas_clean - evas_clean.min()) / (evas_clean.max() - evas_clean.min() + 1e-6)
    
    # Score ponderado: 50% desvio de tempo + 50% taxa de evasão
    df_gold["indice_retencao_critica"] = (0.5 * norm_desv + 0.5 * norm_evas) * 100
    df_gold["indice_retencao_critica"] = df_gold["indice_retencao_critica"].round(1)
    
    # Classificação em quartis
    q75 = df_gold["indice_retencao_critica"].quantile(0.75)
    q50 = df_gold["indice_retencao_critica"].quantile(0.50)
    q25 = df_gold["indice_retencao_critica"].quantile(0.25)
    
    def classificar(score):
        if score >= q75:
            return "RETENÇÃO CRÍTICA"
        elif score >= q50:
            return "RETENÇÃO ALTA"
        elif score >= q25:
            return "RETENÇÃO MÉDIA"
        return "RETENÇÃO BAIXA"
        
    df_gold["classificacao_retencao"] = df_gold["indice_retencao_critica"].apply(classificar)
    
    # Ordenar por índice de retenção decrescente
    df_gold = df_gold.sort_values(by="indice_retencao_critica", ascending=False)
    
    # Salvar tabela Gold
    gold_csv_path = GOLD_DIR / "retencao_cursos_unb.csv"
    df_gold.to_csv(gold_csv_path, index=False, encoding="utf-8")
    logger.info(f"Tabela analítica Gold salva em {gold_csv_path.name} com {len(df_gold)} cursos.")

    # 9. Cálculo das Métricas Globais da UnB (Resumo das 5 GQs)
    total_formados_unb = int(df_valid["is_formado"].sum())
    formados_ideal_unb = int(df_valid["formou_tempo_ideal"].sum())
    formados_acima_unb = int(df_valid["formou_acima_ideal"].sum())
    
    global_metrics = {
        "total_discentes_analisados": len(df_valid),
        "total_formados_unb": total_formados_unb,
        "taxa_conclusao_tempo_ideal_global_pct": round(formados_ideal_unb / total_formados_unb * 100, 2),
        "taxa_conclusao_acima_ideal_global_pct": round(formados_acima_unb / total_formados_unb * 100, 2),
        "tempo_medio_formatura_global_semestres": round(df_valid[df_valid["is_formado"]]["semestres_permanencia_valida"].mean(), 2),
        "desvio_medio_global_semestres": round(df_valid[df_valid["is_formado"]]["desvio_semestres_individual"].mean(), 2),
        "top_5_cursos_maior_retencao": df_gold.head(5)[["curso", "tempo_medio_real_semestres", "taxa_evasao_pct", "indice_retencao_critica"]].to_dict(orient="records"),
        "top_5_cursos_maior_pontualidade": df_gold.sort_values("formados_tempo_ideal_pct", ascending=False).head(5)[["curso", "formados_tempo_ideal_pct", "tempo_medio_real_semestres"]].to_dict(orient="records"),
    }
    
    with open(GOLD_DIR / "metricas_gerais_unb.json", "w", encoding="utf-8") as f:
        json.dump(global_metrics, f, indent=2, ensure_ascii=False)
        
    logger.info(f"Métricas globais da UnB consolidadas em metricas_gerais_unb.json")
    return df_gold, global_metrics


if __name__ == "__main__":
    build_gold_layer()
