import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Request

import google.generativeai as genai
from supabase import create_client, Client


# ============================================================
# CONFIGURAÇÕES
# ============================================================

load_dotenv()

app = FastAPI(title="WatsGenda API")


# ------------------------------------------------------------
# Gemini
# ------------------------------------------------------------

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-1.5-flash")


# ------------------------------------------------------------
# Supabase
# ------------------------------------------------------------

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# ------------------------------------------------------------
# WhatsApp / Evolution API
# ------------------------------------------------------------

EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY")
EVOLUTION_INSTANCE = os.getenv("EVOLUTION_INSTANCE")


# ------------------------------------------------------------
# Timezone
# ------------------------------------------------------------

TIMEZONE = ZoneInfo("America/Sao_Paulo")


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def obter_data_atual():
    """
    Retorna data e hora atual no fuso de São Paulo.
    """

    agora = datetime.now(TIMEZONE)

    return agora.strftime("%Y-%m-%d %H:%M:%S")


def limpar_numero_whatsapp(remote_jid: str) -> str:
    """
    Converte algo como:

        5511999999999@s.whatsapp.net

    para:

        5511999999999

    """

    if not remote_jid:
        return ""

    return remote_jid.split("@")[0]


# ============================================================
# GEMINI
# ============================================================

def interpretar_mensagem(mensagem: str):
    """
    Envia a mensagem para o Gemini e transforma a linguagem
    natural em uma ação estruturada.
    """

    data_atual = obter_data_atual()

    prompt = f"""
Você é o cérebro do WatsGenda, um assistente pessoal que
organiza a rotina do usuário.

DATA E HORA ATUAL:
{data_atual}

FUSO HORÁRIO:
America/Sao_Paulo

MENSAGEM DO USUÁRIO:
"{mensagem}"

Sua tarefa é identificar se o usuário deseja criar um lembrete.

Retorne EXCLUSIVAMENTE um JSON válido.

Se for um pedido para criar um lembrete, use:

{{
    "intencao": "criar_lembrete",
    "titulo": "título curto do lembrete",
    "data_horario": "YYYY-MM-DD HH:MM:SS",
    "descricao": "descrição curta"
}}

Se NÃO for um pedido para criar lembrete, use:

{{
    "intencao": "conversa",
    "resposta": "resposta curta e amigável para o usuário"
}}

IMPORTANTE:

- Entenda expressões como "amanhã", "hoje", "sexta-feira", etc.
- Considere a data atual informada acima.
- Se o usuário disser apenas "às 9", interprete como 09:00.
- Não invente informações que não estejam na mensagem.
- Retorne somente JSON.
"""

    try:

        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.1,
                "response_mime_type": "application/json"
            }
        )

        texto = response.text.strip()

        dados = json.loads(texto)

        return dados

    except json.JSONDecodeError as e:

        print("❌ Gemini retornou algo que não é JSON:")
        print(response.text)

        raise e

    except Exception as e:

        print(f"❌ Erro ao interpretar mensagem com Gemini: {e}")

        raise e


# ============================================================
# SUPABASE
# ============================================================

def salvar_lembrete(
    user_phone: str,
    titulo: str,
    data_horario: str,
    descricao: str
):
    """
    Salva o lembrete no Supabase.
    """

    novo_lembrete = {
        "user_phone": user_phone,
        "titulo": titulo,
        "data_horario": data_horario,
        "descricao": descricao,
        "status": "confirmado"
    }

    resultado = (
        supabase
        .table("agendamentos")
        .insert(novo_lembrete)
        .execute()
    )

    print("✅ Lembrete salvo no Supabase:")
    print(resultado.data)

    return resultado.data


# ============================================================
# WHATSAPP
# ============================================================

def enviar_mensagem_whatsapp(
    numero: str,
    mensagem: str
):
    """
    Envia uma mensagem de texto de volta para o WhatsApp
    usando a Evolution API.
    """

    url = (
        f"{EVOLUTION_API_URL}/message/sendText/"
        f"{EVOLUTION_INSTANCE}"
    )

    headers = {
        "Content-Type": "application/json",
        "apikey": EVOLUTION_API_KEY
    }

    payload = {
        "number": numero,
        "text": mensagem
    }

    try:

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=15
        )

        print("📤 Resposta WhatsApp:")
        print(response.status_code)
        print(response.text)

        response.raise_for_status()

        return True

    except Exception as e:

        print(f"❌ Erro ao enviar mensagem para WhatsApp: {e}")

        return False


# ============================================================
# FORMATAÇÃO DA RESPOSTA
# ============================================================

def formatar_data_hora(data_horario: str) -> str:
    """
    Converte:

    2026-08-25 09:00:00

    para:

    25/08/2026 às 09:00
    """

    try:

        data = datetime.strptime(
            data_horario,
            "%Y-%m-%d %H:%M:%S"
        )

        return data.strftime(
            "%d/%m/%Y às %H:%M"
        )

    except Exception:

        return data_horario


# ============================================================
# PROCESSAMENTO PRINCIPAL
# ============================================================

def processar_mensagem(
    mensagem: str,
    user_phone: str
):
    """
    Fluxo principal do WatsGenda:

    WhatsApp
        ↓
    Gemini
        ↓
    Supabase
        ↓
    WhatsApp
    """

    print("\n==============================")
    print("📩 NOVA MENSAGEM")
    print("==============================")

    print(f"Usuário: {user_phone}")
    print(f"Mensagem: {mensagem}")

    # --------------------------------------------------------
    # 1. Gemini entende a mensagem
    # --------------------------------------------------------

    dados = interpretar_mensagem(mensagem)

    print("🧠 Gemini interpretou:")
    print(dados)

    intencao = dados.get("intencao")

    # --------------------------------------------------------
    # 2. Se for lembrete
    # --------------------------------------------------------

    if intencao == "criar_lembrete":

        titulo = dados.get(
            "titulo",
            "Sem título"
        )

        data_horario = dados.get(
            "data_horario",
            ""
        )

        descricao = dados.get(
            "descricao",
            ""
        )

        # ----------------------------------------------------
        # 3. Salva no Supabase
        # ----------------------------------------------------

        salvar_lembrete(
            user_phone=user_phone,
            titulo=titulo,
            data_horario=data_horario,
            descricao=descricao
        )

        # ----------------------------------------------------
        # 4. Prepara resposta
        # ----------------------------------------------------

        data_formatada = formatar_data_hora(
            data_horario
        )

        resposta = (
            f"✅ Feito!\n\n"
            f"Vou te lembrar de:\n"
            f"📌 {titulo}\n"
            f"🗓️ {data_formatada}"
        )

    # --------------------------------------------------------
    # 5. Se não for lembrete
    # --------------------------------------------------------

    else:

        resposta = dados.get(
            "resposta",
            "Entendi! 😊"
        )

    # --------------------------------------------------------
    # 6. Responde no WhatsApp
    # --------------------------------------------------------

    enviar_mensagem_whatsapp(
        numero=user_phone,
        mensagem=resposta
    )


# ============================================================
# ROTAS FASTAPI
# ============================================================

@app.get("/")
def home():

    return {
        "status": "WatsGenda API funcionando 🚀"
    }


@app.post("/webhook")
async def webhook_whatsapp(request: Request):

    """
    Recebe eventos enviados pelo WhatsApp/Evolution API.
    """

    payload = await request.json()

    print("\n==============================")
    print("📡 WEBHOOK RECEBIDO")
    print("==============================")

    print(json.dumps(
        payload,
        indent=2,
        ensure_ascii=False
    ))

    try:

        data = payload.get(
            "data",
            {}
        )

        key = data.get(
            "key",
            {}
        )

        message = data.get(
            "message",
            {}
        )

        # ----------------------------------------------------
        # Quem enviou?
        # ----------------------------------------------------

        remote_jid = key.get(
            "remoteJid"
        )

        if not remote_jid:

            print("⚠️ Não consegui identificar o remetente.")

            return {
                "status": "sem remetente"
            }

        user_phone = limpar_numero_whatsapp(
            remote_jid
        )

        # ----------------------------------------------------
        # Ignora mensagens enviadas pelo próprio bot
        # ----------------------------------------------------

        from_me = key.get(
            "fromMe",
            False
        )

        if from_me:

            print("↩️ Mensagem enviada pelo próprio bot. Ignorando.")

            return {
                "status": "mensagem própria ignorada"
            }

        # ----------------------------------------------------
        # Identifica mensagem de texto
        # ----------------------------------------------------

        mensagem = None

        # Mensagem de texto simples
        if "conversation" in message:

            mensagem = message.get(
                "conversation"
            )

        # Texto enviado como mensagem estendida
        elif "extendedTextMessage" in message:

            mensagem = (
                message
                .get("extendedTextMessage", {})
                .get("text")
            )

        # ----------------------------------------------------
        # Se não for texto
        # ----------------------------------------------------

        if not mensagem:

            print("ℹ️ Evento recebido, mas não é texto.")

            return {
                "status": "evento recebido"
            }

        mensagem = mensagem.strip()

        print(f"👤 Usuário: {user_phone}")
        print(f"💬 Mensagem: {mensagem}")

        # ----------------------------------------------------
        # Processa a mensagem
        # ----------------------------------------------------

        processar_mensagem(
            mensagem=mensagem,
            user_phone=user_phone
        )

        return {
            "status": "processado"
        }

    except Exception as e:

        print("\n❌ ERRO NO WEBHOOK")
        print(str(e))

        return {
            "status": "erro",
            "error": str(e)
        }
