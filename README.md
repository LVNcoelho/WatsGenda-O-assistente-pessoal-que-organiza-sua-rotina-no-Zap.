#  WatsGenda <img src="https://upload.wikimedia.org/wikipedia/commons/6/6b/WhatsApp.svg" width="30" height="30" alt="WhatsApp"> — O Assistente Pessoal de Rotina via WhatsApp


> **Transforme áudios soltos no WhatsApp e mensagens em compromissos organizados (Planner) no seu banco de dados em segundos.**

O **WatsGenda** foi criado para resolver um problema crítico de produtividade: o desperdício de tempo e a perda de informações que ocorrem no fluxo contínuo de conversas e áudios do dia a dia. Ao integrar inteligência artificial multimodal com um backend assíncrono de altíssima performance, o sistema escuta, entende e estrutura compromissos automaticamente.

---

## 📑 Índice

* [💡 Estratégia & Valor de Negócio](#-estratégia--valor-de-negócio)
* [🛠️ Tech Stack & Escolhas Arquiteturais](#-tech-stack--escolhas-arquiteturais)
* [🔄 Fluxo de Funcionamento](#-fluxo-de-funcionamento)
* [🚀 Como Executar o Projeto](#-como-executar-o-projeto)

---

## 💡 Estratégia & Valor de Negócio

* **Fator Zero Fricção:** O usuário não precisa abrir um app de agenda complexo ou digitar textos longos. Enviar um áudio no WhatsApp como faria para qualquer pessoa é o único requisito.
* **Redução de Erros Operacionais:** Transforma mensagens informais em registros estruturados em JSON, padronizando a captura de datas, horários e descrições.
* **Arquitetura Custo-Eficiente:** Combina o consumo sob demanda de APIs com serviços em nuvem gerenciados, garantindo escala contínua com custos operacionais baixíssimos.

---

## 🛠️ Tech Stack & Escolhas Arquiteturais

A arquitetura foi desenhada priorizando velocidade de resposta, flexibilidade de dados e robustez no processamento:

| Tecnologia | Função no Ecossistema | Motivo da Escolha Estratégica |
| :--- | :--- | :--- |
| **FastAPI** | Backend & Webhooks | Desempenho nativo assíncrono e suporte a *Background Tasks*, garantindo respostas instantâneas às APIs de mensagens sem estourar o tempo limite (*timeout*). |
| **Gemini 1.5 Flash** | Processamento Multimodal | Modelo de linguagem otimizado para áudio e texto com excelente custo-benefício, capaz de extrair contextos e retornar dados estritamente estruturados em JSON. |
| **Supabase** | Persistência Relacional | Infraestrutura de banco de dados PostgreSQL serverless com APIs REST geradas automaticamente, oferecendo consultas rápidas e segurança de dados. |
| **Python** | Linguagem Principal | Ecossistema maduro para manipulação de payloads, integração com modelos de IA e facilidade de manutenção. |

---

## 🔄 Fluxo de Funcionamento

```text
[ Usuário ] ──( Áudio no WhatsApp )──► [ Webhook FastAPI ]
                                             │
                                   (Background Task)
                                             │
                                             ▼
[ Supabase DB ] ◄──(
