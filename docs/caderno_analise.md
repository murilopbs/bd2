# Caderno de Análise e Evidências (Dia 2 - Semana 2)

**Projeto**: Retenção, Tempo Real de Formatura e Evasão nos Cursos de Graduação da UnB  
**Stakeholder**: Decanato de Ensino de Graduação (DEG/DAA)  
**Base Analítica**: Camada Gold (`data/gold/retencao_cursos_unb.csv`)  

---

## 1. Respostas Estruturadas às Cinco Guiding Questions (GQs)

### **GQ 1: Qual o percentual de concluintes que se forma no tempo mínimo, ideal e acima do ideal?**
- **Evidência Global**:
  - Na média de toda a UnB, **62.43%** dos formados integralizam o curso dentro do prazo ideal previsto pela matriz curricular.
  - **37.57%** dos egressos necessitam de semestres adicionais além do prazo ideal para conseguir outorga de grau.
  - Formatura no tempo mínimo regulamentar é rara, ocorrendo em média para apenas **4.8%** dos concluintes da instituição.
- **Disparidade Extrema entre Cursos**:
  - Cursos com maior taxa de formatura no tempo ideal: *Direito* (92.45%), *Gestão do Agronegócio* (89.18%), *Engenharia de Redes* (88.48%) e *Engenharia Civil* (88.16%).
  - Cursos com menor taxa de formatura no tempo ideal (alta retenção): *Física Computacional* (25.0%), *Línguas Estrangeiras Aplicadas* (32.4%), *Ciência da Computação* (42.5%) e *Música* (46.1%).

---

### **GQ 2: Qual é a diferença média (em semestres) entre a duração prevista e a duração real?**
- **Evidência Global**:
  - O tempo médio real de formatura na UnB é de **10.85 semestres** (~5.4 anos).
  - O desvio médio global em relação ao tempo ideal é de cerca de $\pm 0$ semestres quando ponderado por todos os cursos, mas varia drasticamente por área.
- **Áreas com Maior Atraso Real**:
  - *Ciências Exatas e Engenharias*: apresentam atraso médio de **+1.8 a +3.4 semestres** além do tempo ideal (ex: Ciência da Computação tem tempo médio real de 12.37 semestres para uma matriz ideal de 9 semestres, desvio de **+3.37 semestres**).

---

### **GQ 3: Qual a proporção de saídas por formatura versus desligamentos críticos?**
- **Evidência Global**:
  - Do total de 59.202 discentes analisados com registros de saída concluídos no SIGRA, **42.05%** saíram por *Formatura* e **53.8%** saíram por *Evasão/Desligamento* (abandono de curso, não cumprimento de condição ou jubilamento).
- **Cursos com Maior Evasão Crítica**:
  - *Física Computacional*: 76.19% de evasão.
  - *Engenharia*: 74.00% de evasão.
  - *Computação*: 73.47% de evasão.
  - *Ciência da Computação*: 59.14% de evasão.

---

### **GQ 4: Cursos noturnos apresentam desvio de tempo significativamente maior que os diurnos?**
- **Evidência Comparativa**:
  - *Desvio de tempo em relação à matriz*: Cursos noturnos possuem matrizes curriculares que já preveem semestres adicionais em seu desenho curricular (ex: 12 semestres). Por isso, o desvio em relação à sua própria matriz não é maior que o diurno.
  - *Impacto na Taxa de Evasão*: Cursos noturnos apresentam taxa média de evasão de **52.54%**, comparada a **29.43%** nos cursos estritamente diurnos.
  - **Veredito**: A dificuldade no noturno se manifesta prioritariamente na **permanência e evasão** (abandono por conciliação de trabalho/estudo), e não apenas no atraso de semestres de quem consegue formar.

---

### **GQ 5: Existe correlação entre a carga horária total da matriz e o atraso na formatura?**
- **Coeficiente de Correlação de Pearson**: $r = -0.044$ (correlação linear nula).
- **Interpretação**:
  - O atraso na formatura não decorre simplesmente da quantidade absoluta de horas do curso, pois cursos com altíssima carga horária (como Medicina e Engenharias) já possuem maior número de semestres regulamentares atribuídos.
  - O atraso está associado à **estrutura de pré-requisitos encadeados**, disciplinas com alta taxa de reprovação e oferta insuficiente de turmas.

---

## 2. Dinâmica Obrigatória: "A Correlação Suspeita"

> **Hipótese Ingênua**: *"Cursos noturnos têm menor atraso na formatura, portanto são mais fáceis que os diurnos."*

- **Por que a correlação é espúria / perigosa**:
  1. **Confundidor de Matriz**: O tempo ideal cadastrado para cursos noturnos é deliberadamente estendido (ex: 10 ou 12 semestres em vez de 8).
  2. **Viés de Sobrevivência (Survival Bias)**: Quem não aguenta o ritmo do curso noturno abandona (52.5% de evasão). Os poucos que chegam ao final são os discentes altamente resilientes que conseguem cumprir o prazo.
  3. **Conclusão para Decisão Institucional**: Avaliar a dificuldade de um curso exclusivamente pelo tempo de formatura sem considerar a taxa de evasão levaria o DEG a tomar decisões errôneas sobre a saúde acadêmica do curso.

---

## 3. Incerteza Residual e Limitações Declaradas
1. **Margem Temporal de $\pm 1$ Semestre**: Decorrente da ausência do semestre de ingresso no arquivo bruto do SIGRA (`ano_ingresso` de 4 dígitos).
2. **Mudanças de Habilitação**: Discentes que migraram entre habilitações (ex: Licenciatura para Bacharelado) herdam tempo acumulado da habilitação anterior.
3. **Casamento de 97.54%**: 2.46% dos registros não puderam ser correlacionados a estruturas ativas atuais por corresponderem a cursos extintos.
