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


def send_request(prompt_template, email_template):
    """
    Funzione che consente l'invio di una richiesta all'API e
    restituisce la risposta e il tempo impiegato
    """

    try:

        data_struct = config.create_data_struct(email_template, prompt_template)
        # Conversione e serializzazione del dizionario in un JSON e codifica del JSON in bytes
        data = json.dumps(data_struct).encode('utf-8')
        # Creazione e configurazione di un oggetto per la richiesta POST all'endpoint dell'API
        req = urllib.request.Request(config.api_url, data=data, method='POST')
        # Aggiunta delle intestazioni alla richiesta
        req.add_header('Accept', 'application/json')
        req.add_header('app-userid', config.app_mail)
        req.add_header('Content-Type', 'application/json')
        req.add_header('app-acronym', 'GTAI0')
        req.add_header('app-conversation-id', '32ef3e3c-0380-494e-ba82-d84c1844a653')
        req.add_header('app-lang', 'it')
        req.add_header('app-page-name', 'HelpDeskFin')
        req.add_header('app-use-case-key', '73232de2-0c94-47ec-9fba-f5806e9e325e')
        # Misurazione tempo di inizio
        start_time = time.time()
        # Invio della richiesta HTTP POST all'endpoint API,
        # ricezione della risposta e restituzione del messaggio generato dal modello
        with urllib.request.urlopen(req) as f:
            response = f.read().decode('utf-8')
            json_response = json.loads(response)

        # Misurazione tempo di fine
        end_time = time.time()
        elapsed_time = end_time - start_time

        return json_response['choices'][0]['message']['content'], elapsed_time
    except Exception as e:
        return f"Errore: {e}", None


def main():
    """
    Funzione main per processare le mail, mandare le richieste
    all'API e salvare i risultati in un file excel.
    """

    # Caricamento dataset mail
    try:
        mail_df = pd.read_excel("Dataset_SDF_20250418.xlsx", sheet_name='dataset_mail', engine='openpyxl')
        mail_df['Body'] = mail_df['Body'].astype(str).apply(openpyxl.utils.escape.unescape)
        pd.set_option('display.max_colwidth', None)
        mail_df['Body'] = mail_df.apply(
            lambda row: "Da: {0}\nA: {1}\nCc: {2}\nOggetto: {3}\n Body:\n{4}".format(row['From'], row['To'], row['Cc'],
                                                                               row['Subject'], row['Body']), axis=1)
        mail_df['Body'] = mail_df['Body'].str.replace(r'\s+|\\n', ' ', regex=True)
        print(mail_df['Body'].head(10))
    except Exception as e:
        print(f"Errore durante il caricamento del file Excel: {e}")
        return

    sheet_name = 'model_dataset'
    col = ['Id', 'Apertura', 'Beneficiario', 'Descrizione', 'Gruppo', 'Categoria', 'Tempo_impiegato']
    if not os.path.exists("model_results.xlsx"):
        pd.DataFrame(columns=col).to_excel("model_results.xlsx", index=False, sheet_name=sheet_name)
    else:
        os.remove("model_results.xlsx")
        pd.DataFrame(columns=col).to_excel("model_results.xlsx", index=False, sheet_name=sheet_name)
    with pd.ExcelWriter('model_results.xlsx', engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
        # Iterazione sulle mail del dataset
        for index, row in mail_df.iterrows():
            # Identificatore della mail
            result_answer, elapsed_time = send_request(config.prompt_template, row['Body'])
            print(f"Per la mail di indice: {row['Indice']}")
            print(f"Il risultato del modello è il seguente:\n {result_answer}")
            try:
                result = json.loads(result_answer)
                if len(result.keys()) > 1:
                    result_json = [{"Id": row["Indice"], "Apertura": result['AperturaTicket'], "Beneficiario": result["Beneficiario"], "Descrizione": result["Descrizione"],
                                    "Gruppo": result["Gruppo"], "Categoria": result["Categoria"], "Tempo_impiegato": elapsed_time}]
                else:
                    result_json = [
                        {"Id": row["Indice"], "Apertura": result['AperturaTicket'], "Beneficiario": None,
                         "Descrizione": None, "Gruppo": None, "Categoria": None, "Tempo_impiegato": elapsed_time}]

                print(f"Tempo impiegato: {elapsed_time}")
                print("-" * 50)

                # Salvataggio dei risultati in un excel
                model_results = pd.DataFrame(result_json)
                model_results.to_excel(writer, sheet_name=sheet_name, startrow=writer.sheets[sheet_name].max_row,
                                       index=False, header=None)
                gc.collect()

            except Exception as e:
                print(f"Errore generico per indice {row['Indice']}: {e}")
                result_json = [
                    {"Id": row["Indice"], "Apertura": None, "Beneficiario": None,
                     "Descrizione": None, "Gruppo": None, "Categoria": None, "Tempo_impiegato": None}]
                model_results = pd.DataFrame(result_json)
                model_results.to_excel(writer, sheet_name=sheet_name, startrow=writer.sheets[sheet_name].max_row,
                                       index=False, header=None)
                gc.collect()
                continue

    out = metriche("model_results.xlsx")
    if out is None:
        print(f"Attenzione: la funzione metriche restituisce valore None")
    if out:
        print("Indici che non sono stati gestiti dal modello:  ")
        print(" ".join(out))

if __name__ == "__main__":
    main()