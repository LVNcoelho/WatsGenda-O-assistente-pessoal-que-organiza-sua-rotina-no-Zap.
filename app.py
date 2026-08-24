import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request, BackgroundTasks
import google.generativeai as genai

load_dotenv()

app = FastAPI(title="WatsGenda API")

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

def processar_audio_e_agendar(audio_path: str, user_phone: str):
    try:
        audio_file = genai.upload_file(path=audio_path)
        prompt = (
            "Você é o assistente WatsGenda. Analise este áudio e extraia: "
            "1. Título do compromisso/tarefa "
            "2. Data e Horário "
            "3. Descrição breve. "
            "Responda em formato JSON limpo."
        )
        response = model.generate_content([audio_file, prompt])
        print(f"Compromisso processado para {user_phone}: {response.text}")
    except Exception as e:
        print(f"Erro ao processar áudio: {e}")

@app.get("/")
def home():
    return {"status": "WatsGenda rodando no Codespace!"}

@app.post("/webhook")
async def webhook_whatsapp(request: Request, background_tasks: BackgroundTasks):
    payload = await request.json()
    try:
        sender = payload.get("data", {}).get("key", {}).get("remoteJid")
        message_type = payload.get("data", {}).get("messageType")
        
        if message_type == "audioMessage":
            audio_path = "temp_audio.ogg" 
            background_tasks.add_task(processar_audio_e_agendar, audio_path, sender)
            return {"status": "Áudio em processamento"}
    except Exception as e:
        return {"error": str(e)}

    return {"status": "Evento recebido"}
