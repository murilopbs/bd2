"""
Pipeline de Transformação - Camada Bronze -> Camada Silver
Realiza limpeza, decodificação de encodings, remoção de padding,
padronização semântica, cálculo de permanência e tipagem de dados.
"""

import logging
import os
import re
import unicodedata
from pathlib import Path
from typing import Optional
import pandas as pd
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("transform_silver")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
BRONZE_DIR = BASE_DIR / "data" / "bronze"
SILVER_DIR = BASE_DIR / "data" / "silver"


def normalize_text(text: Optional[str]) -> str:
    """Normaliza texto: remove acentos, espaços extras e converte para maiúsculas."""
    if text is None or pd.isna(text):
        return ""
    text = str(text).strip()
    if text.upper() in ["NULL", "NONE", "NAN", "-", ""]:
        return ""
    # Normalização NFKD para decompor caracteres acentuados
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_text = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", ascii_text).upper()


def categorize_forma_saida(forma: str) -> str:
    """Classifica a forma de saída em categorias padronizadas de análise."""
    forma_norm = normalize_text(forma)
    if "FORMATURA" in forma_norm:
        return "FORMATURA"
    elif any(k in forma_norm for k in ["ABANDONO", "NAO CUMPRIU CONDICAO", "JUBILAMENTO", "REPR 3 VEZES", "DESLIGAMENTO"]):
        return "EVASAO_DESLIGAMENTO"
    elif any(k in forma_norm for k in ["NOVO VESTIBULAR", "TRANSFERENCIA", "MUDANCA DE CURSO", "DUPLA HABILITACAO"]):
        return "MUDANCA_INTERNA"
    else:
        return "OUTROS"


def process_sigra() -> pd.DataFrame:
    """Processa a base bruta do SIGRA e gera a versão Silver de discentes de graduação."""
    raw_path = BRONZE_DIR / "sigra_discentes.csv"
    logger.info(f"Processando {raw_path.name}...")
    
    df = pd.read_csv(raw_path, sep=";", encoding="utf-8", on_bad_lines="skip", dtype=str)
    
    # 1. Filtrar apenas discentes de graduação
    df["nivel_norm"] = df["nivel"].apply(normalize_text)
    df_grad = df[df["nivel_norm"] == "GRADUACAO"].copy()
    
    # 2. Limpeza de campos textuais
    df_grad["curso_raw"] = df_grad["curso"].astype(str).str.strip()
    df_grad["curso_norm"] = df_grad["curso"].apply(normalize_text)
    df_grad["departamento_norm"] = df_grad["departamento"].apply(normalize_text)
    df_grad["forma_saida_norm"] = df_grad["forma_saida"].apply(normalize_text)
    df_grad["tipo_saida_grupo"] = df_grad["forma_saida"].apply(categorize_forma_saida)
    
    # 3. Tratamento de datas e períodos
    df_grad["ano_ingresso"] = pd.to_numeric(df_grad["ano_ingresso"], errors="coerce")
    
    # Parse do periodo_saida (ex: '20141' -> ano 2014, semestre 1)
    def parse_periodo_saida(val):
        val_str = str(val).strip().replace(".0", "")
        if len(val_str) == 5 and val_str.isdigit():
            ano = int(val_str[:4])
            sem = int(val_str[4])
            return ano, sem
        elif len(val_str) == 4 and val_str.isdigit():
            # Apenas o ano
            return int(val_str), 1
        return np.nan, np.nan

    parsed_periodo = df_grad["periodo_saida"].apply(parse_periodo_saida)
    df_grad["ano_saida"] = [p[0] for p in parsed_periodo]
    df_grad["semestre_saida"] = [p[1] for p in parsed_periodo]
    
    # 4. Cálculo do tempo de permanência em semestres
    # Fórmula: 2 * (ano_saida - ano_ingresso) + semestre_saida
    # Documentação de incerteza: assume ingresso no semestre 1 como baseline
    df_grad["semestres_permanencia"] = (
        2 * (df_grad["ano_saida"] - df_grad["ano_ingresso"]) + df_grad["semestre_saida"]
    )
    
    # Filtro de sanidade (permanência entre 1 e 30 semestres)
    df_grad["semestres_permanencia_valida"] = df_grad["semestres_permanencia"].apply(
        lambda x: x if (pd.notna(x) and 1 <= x <= 30) else np.nan
    )
    
    out_path = SILVER_DIR / "sigra_graduacao_silver.csv"
    df_grad.to_csv(out_path, index=False, encoding="utf-8")
    logger.info(f"Salvo {out_path.name} com {len(df_grad):,} registros de graduação.")
    return df_grad


def process_estrutura_curricular() -> pd.DataFrame:
    """Processa a base bruta de estrutura curricular (resolvendo encoding latin-1)."""
    raw_path = BRONZE_DIR / "estrutura_curricular.csv"
    logger.info(f"Processando {raw_path.name}...")
    
    df = pd.read_csv(raw_path, sep=";", encoding="latin-1", on_bad_lines="skip", dtype=str)
    
    # Normalização de nomes de cursos
    df["nome_curso_norm"] = df["nome_curso"].apply(normalize_text)
    df["nome_matriz_norm"] = df["nome_matriz"].apply(normalize_text)
    
    # Conversão de colunas numéricas de semestres e horas
    num_cols = [
        "semestre_conclusao_minimo",
        "semestre_conclusao_ideal",
        "semestre_conclusao_maximo",
        "ch_total_minima",
        "cr_total_minimo",
        "ano_entrada_vigor",
    ]
    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        
    # Agregação por curso canônico para obter os prazos de referência consolidados
    # (seleciona o currículo com maior ch_total_minima ou mais recente)
    df_clean = df[df["nome_curso_norm"] != ""].copy()
    
    # Agrupamento para consolidar matriz de referência
    agg_dict = {
        "semestre_conclusao_minimo": "median",
        "semestre_conclusao_ideal": "median",
        "semestre_conclusao_maximo": "median",
        "ch_total_minima": "max",
        "cr_total_minimo": "max",
        "id_curso": "first",
    }
    df_consolidado = df_clean.groupby("nome_curso_norm", as_index=False).agg(agg_dict)
    
    out_path = SILVER_DIR / "estrutura_curricular_silver.csv"
    df_consolidado.to_csv(out_path, index=False, encoding="utf-8")
    logger.info(f"Salvo {out_path.name} com {len(df_consolidado):,} estruturas curriculares consolidadas.")
    return df_consolidado


def process_cursos_graduacao() -> pd.DataFrame:
    """Processa a base de cursos de graduação (resolvendo 'NULL' literais e metadados)."""
    raw_path = BRONZE_DIR / "cursos_graduacao.csv"
    logger.info(f"Processando {raw_path.name}...")
    
    df = pd.read_csv(raw_path, sep=",", encoding="utf-8", on_bad_lines="skip", dtype=str)
    
    df["nome_curso_norm"] = df["nome"].apply(normalize_text)
    df["turno_norm"] = df["turno"].apply(normalize_text)
    df["campus_norm"] = df["campus"].apply(normalize_text)
    df["grau_academico_norm"] = df["grau_academico"].apply(normalize_text)
    df["area_conhecimento_norm"] = df["area_conhecimento"].apply(normalize_text)
    df["unidade_responsavel_norm"] = df["unidade_responsavel"].apply(normalize_text)
    
    # Substituir literais NULL por NaN
    df = df.replace(["NULL", "NONE", "NAN", ""], np.nan)
    
    out_path = SILVER_DIR / "cursos_graduacao_silver.csv"
    df.to_csv(out_path, index=False, encoding="utf-8")
    logger.info(f"Salvo {out_path.name} com {len(df):,} cursos cadastrados.")
    return df


def run_silver_pipeline():
    """Executa o pipeline completo Bronze -> Silver."""
    SILVER_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("=== Iniciando Pipeline de Transformação (Camada Silver) ===")
    df_sigra = process_sigra()
    df_est = process_estrutura_curricular()
    df_cursos = process_cursos_graduacao()
    logger.info("=== Camada Silver Gerada com Sucesso ===")
    return df_sigra, df_est, df_cursos


if __name__ == "__main__":
    run_silver_pipeline()
