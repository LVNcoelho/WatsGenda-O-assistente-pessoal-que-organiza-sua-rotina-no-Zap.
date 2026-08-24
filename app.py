import os
import json
from dotenv import load_dotenv
from fastapi import FastAPI, Request, BackgroundTasks
import google.generativeai as genai
from supabase import create_client, Client

load_dotenv()

app = FastAPI(title="WatsGenda API")

# Inicialização da API do Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

# Inicialização do Cliente Supabase
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)


def processar_audio_e_agendar(audio_path: str, user_phone: str):
    """
    Sobe o áudio para o Gemini, extrai os dados estruturados em JSON
    e insere os dados diretamente na tabela do Supabase.
    """
    try:
        # Upload do arquivo de áudio para a API do Gemini
        audio_file = genai.upload_file(path=audio_path)
        
        prompt = (
            "Você é o assistente WatsGenda. Analise este áudio e extraia as informações de compromisso ou tarefa. "
            "Responda EXCLUSIVAMENTE em formato JSON válido, sem marcação de código markdown como ```json, contendo as chaves: "
            '"titulo", "data_horario" e "descricao".'
        )
        
        response = model.generate_content([audio_file, prompt])
        
        # Converte a resposta em dicionário Python
        dados = json.loads(response.text.strip())
        
        # Prepara a estrutura para salvar no Supabase
        novo_agendamento = {
            "user_phone": user_phone,
            "titulo": dados.get("titulo", "Sem título"),
            "data_horario": dados.get("data_horario", ""),
            "descricao": dados.get("descricao", ""),
            "status": "confirmado"
        }
        
        # Insere na tabela 'agendamentos'
        res = supabase.table("agendamentos").insert(novo_agendamento).execute()
        print(f"✅ Agendamento salvo no Supabase com sucesso para {user_phone}: {res.data}")
        
    except json.JSONDecodeError as e:
        print(f"❌ Erro ao converter resposta do Gemini para JSON: {e}")
    except Exception as e:
        print(f"❌ Erro ao processar áudio ou salvar no Supabase: {e}")


@app.get("/")
def home():
    return {"status": "WatsGenda + Supabase rodando perfeitamente!"}


@app.post("/webhook")
async def webhook_whatsapp(request: Request, background_tasks: BackgroundTasks):
    """
    Endpoint de entrada do webhook do WhatsApp.
    """
    payload = await request.json()
    
    try:
        sender = payload.get("data", {}).get("key", {}).get("remoteJid")
        message_type = payload.get("data", {}).get("messageType")
        
        if message_type == "audioMessage":
            audio_path = "temp_audio.ogg"
            
            # Processa o áudio e a gravação no banco em segundo plano
            background_tasks.add_task(processar_audio_e_agendar, audio_path, sender)
            
            return {"status": "Áudio recebido, em processamento e salvando no Supabase..."}
            
    except Exception as e:
        return {"error": str(e)}

    return {"status": "Evento recebido"}
