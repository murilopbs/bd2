"""
Cliente de Ingestão de Dados via API CKAN 2.11 - dados.unb.br
Responsável por consultar os metadados dos pacotes e baixar os recursos
brutos de forma automatizada e reproduzível para a camada Bronze.
"""

import json
import logging
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("ckan_ingestion")

BASE_URL = "https://dados.unb.br/api/3/action"
DEFAULT_BRONZE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "bronze"

# Mapeamento de pacotes e recursos prioritários para o projeto
DATASETS_CONFIG = {
    "sigra": {
        "package_id": "dados-referente-aos-alunos-de-graduacao-pos-graduacao-latu-sensu-mestrado-e-doutorado",
        "resource_name_pattern": "sigra.csv",
        "output_filename": "sigra_discentes.csv",
        "description": "Histórico acadêmico de discentes, ano de ingresso e forma/período de saída.",
    },
    "sigaa": {
        "package_id": "dados-referente-aos-alunos-de-graduacao-pos-graduacao-latu-sensu-mestrado-e-doutorado",
        "resource_name_pattern": "sigaa.csv",
        "output_filename": "sigaa_discentes.csv",
        "description": "Dados de discentes e status de diploma no SIGAA.",
    },
    "estrutura_curricular": {
        "package_id": "estrutura-curricular",
        "resource_name_pattern": "estrutura-curricular.csv",
        "output_filename": "estrutura_curricular.csv",
        "description": "Estruturas curriculares, semestres mínimo/ideal/máximo e carga horária por curso.",
    },
    "cursos_graduacao": {
        "package_id": "cursos-de-graduacao",
        "resource_name_pattern": "curso_graduacao.csv",
        "output_filename": "cursos_graduacao.csv",
        "description": "Catálogo de cursos de graduação, turnos, campus e unidades acadêmicas responsáveis.",
    },
}


def fetch_package_metadata(package_id: str) -> Dict:
    """Consulta a API do CKAN para obter metadados completos de um pacote."""
    url = f"{BASE_URL}/package_show?id={urllib.parse.quote(package_id)}"
    logger.info(f"Consultando metadados do pacote '{package_id}'...")
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "UnB-CBL-Challenge/1.0 (Data Science Agent)"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        if not data.get("success"):
            raise RuntimeError(f"Erro ao consultar pacote {package_id}: {data}")
        return data["result"]


def download_resource(url: str, dest_path: Path) -> Path:
    """Baixa um recurso do CKAN e salva no caminho de destino."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Baixando recurso de {url} -> {dest_path.name}...")
    
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "UnB-CBL-Challenge/1.0 (Data Science Agent)"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp, open(dest_path, "wb") as f:
        bytes_copied = 0
        while True:
            chunk = resp.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)
            bytes_copied += len(chunk)
            
    size_mb = bytes_copied / (1024 * 1024)
    logger.info(f"Download concluído: {dest_path.name} ({size_mb:.2f} MB)")
    return dest_path


def run_ingestion(output_dir: Optional[Path] = None) -> Dict[str, Path]:
    """
    Executa o processo completo de ingestão via API CKAN para a camada Bronze.
    Salva os metadados brutos em JSON e os arquivos CSV brutos.
    """
    out_dir = output_dir or DEFAULT_BRONZE_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    
    downloaded_files = {}
    metadata_summary = {}

    # Permite pular datasets via env (ex.: SKIP_DATASETS=sigaa) — usado no CI,
    # onde 'sigaa' não é consumido por nenhuma etapa do pipeline.
    skip = {s.strip() for s in os.environ.get("SKIP_DATASETS", "").split(",") if s.strip()}

    for key, config in DATASETS_CONFIG.items():
        if key in skip:
            logger.info(f"Pulando dataset '{key}' (SKIP_DATASETS).")
            continue
        pkg_id = config["package_id"]
        meta = fetch_package_metadata(pkg_id)
        metadata_summary[pkg_id] = meta
        
        # Salva o dump de metadados brutos da API
        meta_file = out_dir / f"metadata_{pkg_id}.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
            
        # Localiza o recurso desejado
        pattern = config["resource_name_pattern"].lower()
        target_resource = None
        for res in meta.get("resources", []):
            r_url = res.get("url", "").lower()
            r_name = res.get("name", "").lower()
            if pattern in r_url or pattern in r_name:
                target_resource = res
                break
                
        if not target_resource:
            # Se não encontrou pelo pattern exato, pega o primeiro CSV
            for res in meta.get("resources", []):
                if res.get("format", "").upper() == "CSV":
                    target_resource = res
                    break
                    
        if target_resource:
            res_url = target_resource["url"]
            dest_file = out_dir / config["output_filename"]
            download_resource(res_url, dest_file)
            downloaded_files[key] = dest_file
        else:
            logger.warning(f"Recurso compatível com '{pattern}' não encontrado em {pkg_id}")

    logger.info("=== Ingestão da Camada Bronze Concluída com Sucesso ===")
    return downloaded_files


if __name__ == "__main__":
    run_ingestion()
