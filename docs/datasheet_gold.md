# Datasheet for Dataset: Tabela Gold de Retenção e Formatura da UnB

*Baseado no padrão de documentação científica de Gebru et al. (2021) "Datasheets for Datasets".*

---

## 1. Motivação (Motivation)
- **Para qual propósito este dataset foi criado?**
  Criado para diagnosticar quantitativamente as discrepâncias entre a duração prevista pelas matrizes curriculares e o tempo real de integralização dos discentes de graduação da UnB, bem como mensurar as taxas de evasão associadas.
- **Quem criou o dataset e sob qual mandato?**
  Construído pela equipe do Challenge de Dados Abertos da UnB (Metodologia CBL - Disciplina de BD2), tendo como stakeholder o Decanato de Ensino de Graduação (DEG).

---

## 2. Composição (Composition)
- **O que cada instância representa?**
  Cada linha representa um curso canônico de graduação da Universidade de Brasília com métricas agregadas de retenção, tempo médio real de formatura, percentuais de pontualidade e taxas de desligamento.
- **Quantas instâncias existem no dataset?**
  76 cursos de graduação consolidados (com supressão ética de cursos com menos de 5 registros para proteção de privacidade).
- **O dataset contém dados confidenciais ou LGPD?**
  Não. Todas as variáveis sensíveis (data de nascimento, raça, sexo e cota) foram descartadas e o dataset expõe exclusivamente agregados estatísticos por curso.

---

## 3. Processo de Coleta e Proveniência (Collection Process)
- **Como os dados foram obtidos?**
  Extraídos programaticamente via API CKAN 2.11 do portal [dados.unb.br](https://dados.unb.br) a partir de três pacotes abertos:
  1. *dados-referente-aos-alunos-de-graduacao-pos-graduacao-latu-sensu-mestrado-e-doutorado* (`sigra.csv`);
  2. *estrutura-curricular* (`estrutura-curricular.csv`);
  3. *cursos-de-graduacao* (`curso_graduacao.csv`).
- **Qual foi o período temporal de cobertura?**
  Cobre históricos de discentes que ingressaram e concluíram seus ciclos acadêmicos entre 2010 e os semestres mais recentes consolidados no SIGRA.

---

## 4. Pré-processamento e Limpeza (Preprocessing & Cleaning)
- **Quais transformações foram aplicadas?**
  1. *Decodificação*: Correção de encoding `ISO-8859-1` / `Latin-1` na estrutura curricular.
  2. *Normalização Textual*: Remoção de acentuação (NFKD), conversão para caixa alta e strip de espaços contínuos e padding de final de linha.
  3. *Mapeamento Canônico*: Aplicação de dicionário de sinônimos para especializações e habilitações de cursos, elevando a taxa de casamento dos joins para 97.54%.
  4. *Incerteza Temporal*: O cálculo do tempo de permanência assume o semestre 1 como baseline na ausência do semestre de ingresso, com incerteza metodológica de $\pm 1$ semestre explicitada.

---

## 5. Usos Recomendados e Não Recomendados (Uses)
- **Usos Apropriados**:
  - Avaliação institucional da carga de retenção por departamentos e áreas;
  - Identificação de cursos com necessidade urgente de flexibilização de fluxos e pré-requisitos;
  - Planejamento de ampliação de vagas em disciplinas gargalo.
- **Usos Desaconselhados**:
  - Rotular um curso como "pior" ou "melhor" de forma descontextualizada da sua complexidade técnica;
  - Tentar reidentificar trajetórias de discentes individuais;
  - Utilizar os dados como justificativa punitiva para cortes orçamentários departamentais.
