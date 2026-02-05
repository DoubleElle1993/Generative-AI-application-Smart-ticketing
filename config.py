# Lettura del file di prompt e mail
with open("Prompt_1403.txt", "r") as input_file:
    prompt_template = input_file.read()

# Creazione di un oggetto che contenga l'endpoint dell'API
api_url = "http://genai-sdlc-chat-v1-gtai0-svil.cloudapps-test.intesasanpaolo.com/api/stateless/chat/simple/tech"
app_mail = "U485984"

# Definizione del threshold per
threshold_Beneficiario: float = 0.5
threshold_Gruppi: float = 0.5
threshold_Descrizione: float = 0.7
# Definizione della funzione per definire la struttura del dizionario
def create_data_struct(email_template, prompt_template):
    """
    Questa funzione ha il fine di riprodurre la struttura dati che verranno
    passati al modello
    """

    return {
        "messages": [
            {
                "content": email_template,
                "role": "user"
            }
        ],
        "context": {
            "overrides": {
                "promptTemplate": prompt_template,
                "promptTemplateReplace": True,
                "temperature": 0,
                "gptModel": "gpt-4.1-mini"
            }
        },
        "stream": False,
        "chatType": "default"
    }



