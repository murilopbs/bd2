# Dicionário de Dados da Tabela Gold: `retencao_cursos_unb.csv`

Este documento descreve a semântica, os tipos de dados e os métodos de cálculo de todas as colunas da tabela analítica da camada Gold (`data/gold/retencao_cursos_unb.csv`), gerada para suportar a tomada de decisão do Decanato de Ensino de Graduação (DEG).

---

## 1. Metadados do Artefato
- **Arquivo**: `data/gold/retencao_cursos_unb.csv`
- **Granularidade**: 1 linha por curso canônico de graduação da UnB.
- **Total de Cursos Consolidados**: 76 cursos.
- **Fontes Primárias**: `sigra_discentes.csv` (24.5 MB) + `estrutura_curricular.csv` (76 KB) + `cursos_graduacao.csv` (45 KB).
- **Taxa de Casamento dos Joins**: 97.54%.

---

## 2. Dicionário de Campos

| Nome da Coluna | Tipo de Dado | Exemplo | Descrição e Regra de Cálculo |
| :--- | :--- | :--- | :--- |
| `curso` | String | `CIENCIA DA COMPUTACAO` | Nome canônico e normalizado do curso de graduação da UnB (sem acentos, uppercase). |
| `departamento` | String | `DEPTO CIENCIA DA COMPUTACAO` | Departamento acadêmico de vinculação principal da matriz. |
| `campus` | String | `DARCY RIBEIRO` | Campus de oferta (Darcy Ribeiro, FGA - Gama, FCE - Ceilândia, FUP - Planaltina). |
| `turno` | String | `DIURNO` | Turno de oferta cadastrado no catálogo de graduação (Diurno, Noturno, Integral). |
| `area_conhecimento` | String | `CIENCIAS EXATAS E DA TERRA` | Grande área de conhecimento do CNPq/MEC. |
| `grau_academico` | String | `BACHAREL` | Titulação conferida ao egresso (Bacharel, Licenciado, Engenheiro). |
| `semestre_minimo_previsto` | Float | `8.0` | Quantidade mínima regulamentar de semestres para conclusão cadastrada na estrutura curricular. |
| `semestre_ideal_previsto` | Float | `9.0` | Duração padrão/ideal em semestres para integralização da matriz curricular. |
| `semestre_maximo_previsto` | Float | `16.0` | Prazo máximo de permanência antes da abertura de processo de jubilamento. |
| `carga_horaria_minima` | Float | `3600.0` | Carga horária total mínima (horas-aula) exigida para conclusão. |
| `total_discentes_registrados` | Inteiro | `1450` | Volume total de discentes com registro de movimentação acadêmica no curso. |
| `total_formados` | Inteiro | `580` | Quantidade total de discentes cuja forma de saída foi `Formatura`. |
| `total_evadidos_desligados` | Inteiro | `850` | Total de discentes desligados (abandono, jubilamento, reprovação 3x na mesma disciplina). |
| `taxa_formatura_pct` | Float (%) | `40.00` | Percentual de discentes que concluíram o curso: $\frac{\text{total\_formados}}{\text{total\_discentes}} \times 100$. |
| `taxa_evasao_pct` | Float (%) | `58.62` | Percentual de discentes evadidos/desligados: $\frac{\text{total\_evadidos}}{\text{total\_discentes}} \times 100$. |
| `formados_tempo_minimo_pct` | Float (%) | `5.17` | Proporção de egressos que integralizaram o curso em prazo $\le \text{semestre\_minimo\_previsto}$. |
| `formados_tempo_ideal_pct` | Float (%) | `42.50` | Proporção de egressos que integralizaram o curso em prazo $\le \text{semestre\_ideal\_previsto}$. |
| `formados_acima_ideal_pct` | Float (%) | `57.50` | Proporção de egressos que ultrapassaram o tempo ideal ($100 - \text{formados\_tempo\_ideal\_pct}$). |
| `formados_limite_maximo_pct` | Float (%) | `8.20` | Proporção de egressos que se formaram no limite do jubilamento ($\ge \text{semestre\_maximo\_previsto}$). |
| `tempo_medio_real_semestres` | Float | `12.37` | Duração média observada em semestres entre o ingresso e a outorga de grau. |
| `tempo_mediano_real_semestres` | Float | `12.00` | Mediana do tempo de integralização em semestres (robusta a outliers). |
| `desvio_medio_semestres` | Float | `3.37` | Diferença média em semestres: $\text{tempo\_medio\_real} - \text{semestre\_ideal\_previsto}$. |
| `indice_retencao_critica` | Float (0-100) | `59.7` | Índice composto normalizado: $0.5 \times \text{norm}(desvio) + 0.5 \times \text{norm}(evasao)$. |
| `classificacao_retencao` | String | `RETENÇÃO CRÍTICA` | Nível de urgência institucional: `RETENÇÃO CRÍTICA` (Top 25%), `ALTA`, `MÉDIA`, `BAIXA`. |
