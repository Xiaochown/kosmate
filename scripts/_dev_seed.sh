#!/data/data/com.termux/files/usr/bin/bash
cd /root/kosmate || exit 1
{
  echo "LLM_BASE_URL=https://api.teamorouter.com/v1"
  echo "LLM_API_KEY=${HERMES_CUSTOM_API_TEAMOROUTER_COM_API_KEY}"
  echo "LLM_MODEL=deepseek-v4-flash-free"
  echo "LLM_MODEL_FALLBACK=gemini-3.5-flash-lite"
  echo "TTS_PROVIDER=auto"
  echo "TTS_VOICE=id-ID-GadisNeural"
  echo "STT_PROVIDER=auto"
  echo "ASSISTANT_NAME=Kai"
  echo "USER_NAME=Faa"
  echo "PERSONA_MODE=temen"
  echo "HOST=127.0.0.1"
  echo "PORT=8095"
} > .env
wc -l .env
.venv/bin/python -m server.memory
echo "--- LLM test ---"
timeout 120 .venv/bin/python -m server.llm
