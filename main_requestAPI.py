import gc
import urllib.request
import json
import pandas as pd
import time
import os
import config
import openpyxl
from openpyxl import utils
from MetricheTest import metriche



def build_email_text(row):
    return (
        f"Da: {row['From']}\n"
        f"A: {row['To']}\n"
        f"Cc: {row['Cc']}\n"
        f"Oggetto: {row['Subject']}\n"
        f"Body \n{row['Body']}"
    )

def send_request(prompt_template: str, email_template: str):
    """
    Function that allows sending a request to the API and
    returns the response along with the time taken
    """

    try:
        # Conversione, serializzazione del dizionario in un JSON e codifica del JSON in bytes
        data_struc = config.create_data_struct(email_template, prompt_template)
        data = json.dumps(data_struc).encode("utf-8")
        # Creazione e configurazione di un oggetto per la richiesta POST all'endpoint dell'API
        # usando come body della richiesta i bytes del json
        req = urllib.request.Request(config.api_url, data=data, method='POST')
        # Creazione di un dizionario per gli header della richiesta
        headers = {
            'Accept': 'application/json',
            'app-userid': config.app_mail,
            'Content-Type': 'application/json',
            'app-acronym': 'GTAI0',
            'app-conversation-id': '32ef3e3c-0380-494e-ba82-d84c1844a653',
            'app-lang': 'it',
            'app-page-name': 'HelpDeskFin',
            'app-use-case-key': '73232de2-0c94-47ec-9fba-f5806e9e325e'
        }
        for key, value in headers.items():
            req.add_header(key, value)
        # Tempo inizio chiamata
        start_time = time.time()
        # Invio della richiesta HTTP POST all'endpoint API, ricezione della risposta e restituzione del messaggio generato dal modello
        with urllib.request.urlopen(req) as f:
            response = f.read().decode("utf-8")
            json_response = json.loads(response)
        # Tempo fine chiamata
        end_time = time.time()
        elapsed_time = end_time - start_time
        # Contenuto del file Json contenente il risultato del modello come testo stringa
        content = json_response['choices'][0]['message']['content']
        return content, elapsed_time
    except Exception as e:
        return f"Errore: {e}", None


def main():

    # Definzione degli oggetti utilizzati nella funzione
    input_xlsx = "Dataset_SDF_20250418.xlsx"
    input_sheet = "dataset_mail"
    output_xlsx = "model_results.xlsx"
    output_sheet = "model_dataset"
    columns = ['Id','Apertura','Beneficiario','Descrizione','Gruppo','Categoria','Tempo_impiegato']

    try:
        # Caricamento dati
        mail_df = pd.read_excel(input_xlsx, sheet_name=input_sheet, engine="openpyxl")
        # Trasformazione del campo body
        mail_df['Body'] = mail_df['Body'].astype(str)
        mail_df['Body'] = mail_df['Body'].apply(openpyxl.utils.escape.unescape)
        mail_df['Body'] = mail_df.apply(build_email_text, axis=1)
        mail_df['Body'] = mail_df['Body'].str.replace(r'\s+|\\n', ' ', regex=True)
        print(mail_df['Body'].head())
    except Exception as e:
        print(f"Errore di caricamento del file: {e}")
        return

    if not os.path.exists(output_xlsx):
        pd.DataFrame(columns=columns).to_excel(output_xlsx, index=False, sheet_name=output_sheet)
    else:
        os.remove(output_xlsx)
        pd.DataFrame(columns=columns).to_excel(output_xlsx, index=False, sheet_name=output_sheet)
    # Apertura del file excel di output per poi fare l'append del risultato all'interno
    with pd.ExcelWriter(output_xlsx, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
        for index, row in mail_df.iterrows():
            result_answer, elapsed_time = send_request(config.prompt_template, row['Body'])
            print("RAW result_answer:", repr(result_answer))

            print(f"Per la riga di indice: {row['Indice']}\n")
            print(f"Il modello restituisce il risultato\n: {result_answer}")
            try:
                dictionary_result = json.loads(result_answer)
                if len(dictionary_result.keys()) > 1:
                    json_result = [{'Id': row['Indice'], 'Apertura': dictionary_result['AperturaTicket'],
                                      'Beneficiario': dictionary_result['Beneficiario'],
                                      'Descrizione': dictionary_result['Descrizione'],
                                      'Gruppo': dictionary_result['Gruppo'], 'Categoria': dictionary_result['Categoria'],
                                      'Tempo_impiegato': elapsed_time
                                    }]
                else:
                    json_result = [{'Id': row['Indice'], 'Apertura': None,
                                    'Beneficiario': None,
                                    'Descrizione': None,
                                    'Gruppo': None, 'Categoria': None,
                                    'Tempo_impiegato': None
                                    }]

                print(f"Il tempo impiegato per l'esecuzione della riga di indice {row['Indice']} é: {elapsed_time}\n")
                # Salvataggio dei risultati in un file excel
                result_df = pd.DataFrame(json_result)
                result_df.to_excel(writer, sheet_name=output_sheet, startrow=writer.sheets[output_sheet].max_row,
                                       index=False, header=None)
                gc.collect()

            except Exception as e:
                print(f"Errore {e} per la riga di indice {row['Indice']}")
                json_result = [{'Id': row['Indice'], 'Apertura': None,
                                'Beneficiario': None,
                                'Descrizione': None,
                                'Gruppo': None, 'Categoria': None,
                                'Tempo_impiegato': None
                                }]
                # Salvataggio dei risultati in un file excel
                result_df = pd.DataFrame(json_result)
                result_df.to_excel(writer, sheet_name=output_sheet, startrow=writer.sheets[output_sheet].max_row,
                                       index=False, header=None)
                gc.collect()


if __name__ == "__main__":
    main()
