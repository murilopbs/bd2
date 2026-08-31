"""
Suíte de Testes Automatizados - Pipeline de Retenção e Formatura UnB
Valida integridade de esquema, contratos de dados, taxa de casamento de joins
e conformidade com as regras metodológicas do Challenge.
"""

import json
from pathlib import Path
import unittest
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
BRONZE_DIR = BASE_DIR / "data" / "bronze"
SILVER_DIR = BASE_DIR / "data" / "silver"
GOLD_DIR = BASE_DIR / "data" / "gold"


class TestDataPipeline(unittest.TestCase):
    
    def test_01_bronze_datasets_exist(self):
        """Verifica se os datasets brutos foram baixados corretamente via API."""
        required_files = [
            "sigra_discentes.csv",
            "estrutura_curricular.csv",
            "cursos_graduacao.csv",
        ]
        for fname in required_files:
            fpath = BRONZE_DIR / fname
            self.assertTrue(fpath.exists(), f"Arquivo Bronze ausente: {fname}")
            self.assertGreater(fpath.stat().st_size, 1000, f"Arquivo Bronze vazio ou corrompido: {fname}")

    def test_02_silver_transformation_integrity(self):
        """Verifica a limpeza, tipagem e decodificação na camada Silver."""
        sig_path = SILVER_DIR / "sigra_graduacao_silver.csv"
        est_path = SILVER_DIR / "estrutura_curricular_silver.csv"
        cur_path = SILVER_DIR / "cursos_graduacao_silver.csv"
        
        self.assertTrue(sig_path.exists(), "sigra_graduacao_silver.csv ausente")
        self.assertTrue(est_path.exists(), "estrutura_curricular_silver.csv ausente")
        self.assertTrue(cur_path.exists(), "cursos_graduacao_silver.csv ausente")
        
        df_sig = pd.read_csv(sig_path)
        self.assertIn("semestres_permanencia_valida", df_sig.columns)
        self.assertIn("tipo_saida_grupo", df_sig.columns)
        self.assertTrue((df_sig["nivel_norm"] == "GRADUACAO").all(), "Registros de pós-graduação presentes indevidamente")
        
        df_est = pd.read_csv(est_path)
        self.assertIn("semestre_conclusao_ideal", df_est.columns)
        self.assertTrue(df_est["semestre_conclusao_ideal"].notna().any(), "Prazos ideais nulos na estrutura")

    def test_03_gold_layer_and_join_match_rate(self):
        """Verifica se a camada Gold atinge taxa de casamento superior a 90% e métricas consistentes."""
        gold_path = GOLD_DIR / "retencao_cursos_unb.csv"
        join_meta_path = GOLD_DIR / "relatorio_casamento_joins.json"
        
        self.assertTrue(gold_path.exists(), "retencao_cursos_unb.csv ausente")
        self.assertTrue(join_meta_path.exists(), "relatorio_casamento_joins.json ausente")
        
        with open(join_meta_path, "r", encoding="utf-8") as f:
            join_meta = json.load(f)
            
        taxa = join_meta.get("taxa_de_casamento_pct", 0)
        self.assertGreaterEqual(taxa, 90.0, f"Taxa de casamento abaixo da meta de 90%: {taxa}%")
        
        df_gold = pd.read_csv(gold_path)
        self.assertGreater(len(df_gold), 50, "Quantidade de cursos na Gold muito reduzida")
        
        # Validar consistência matemática das métricas percentuais (0 <= pct <= 100)
        pct_cols = [
            "taxa_formatura_pct",
            "taxa_evasao_pct",
            "formados_tempo_ideal_pct",
            "formados_tempo_minimo_pct",
            "formados_acima_ideal_pct",
        ]
        for col in pct_cols:
            self.assertTrue((df_gold[col] >= 0).all(), f"Valor negativo encontrado na coluna {col}")
            self.assertTrue((df_gold[col] <= 100).all(), f"Valor superior a 100% encontrado na coluna {col}")
            
        # Validar semestres reais positivos
        valid_sem = df_gold["tempo_medio_real_semestres"].dropna()
        self.assertTrue((valid_sem >= 1).all(), "Tempo de formatura menor que 1 semestre encontrado")

    def test_04_privacy_safeguards(self):
        """Garante que a tabela Gold não expõe quase-identificadores sensíveis de discentes."""
        gold_path = GOLD_DIR / "retencao_cursos_unb.csv"
        df_gold = pd.read_csv(gold_path)
        
        forbidden_cols = ["nome", "cpf", "data_nascimento", "sexo", "raca_cor", "cota_ingresso", "aluno"]
        for fcol in forbidden_cols:
            self.assertNotIn(fcol, df_gold.columns, f"Dado pessoal '{fcol}' exposto indevidamente na camada Gold")
            
        # Supressão de cursos com menos de 5 discentes
        self.assertTrue((df_gold["total_discentes_registrados"] >= 5).all(), "Grupo com k < 5 discentes não foi suprimido")


if __name__ == "__main__":
    unittest.main()
