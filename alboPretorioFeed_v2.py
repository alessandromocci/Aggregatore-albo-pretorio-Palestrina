import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from datetime import datetime

# Funzione per convertire le date in formato RFC-822
def convert_to_rfc822(date_str):
    try:
        # Prova a interpretare la data come "giorno/mese/anno"
        date_obj = datetime.strptime(date_str.strip(), '%d/%m/%Y')
        return date_obj.strftime('%a, %d %b %Y %H:%M:%S %z')
    except ValueError:
        # Se fallisce, ritorna la stringa originale
        return date_str

# Funzione per estrarre dati da una singola pagina e aggiungerli all'RSS feed
def extract_data_from_page(soup, channel):
    rows = soup.find_all("tr", class_="master-detail-list-line")
    for row in rows:
        numero_registrazione = row.find("td", class_="annonumeroregistrazione number").text.strip()
        categoria = row.find("td", class_="categoria text").text.strip()
        oggetto = row.find("td", class_="oggetto text").text.strip()
        periodo_pubblicazione = row.find("td", class_="periodo-pubblicazione date").text.strip()
        periodo_pubblicazione = convert_to_rfc822(periodo_pubblicazione.split()[0])

        # Estrazione del primo link
        link = row.find("a", class_="master-detail-list-link-a")['href']

        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = numero_registrazione
        ET.SubElement(item, "category").text = categoria
        ET.SubElement(item, "description").text = oggetto
        ET.SubElement(item, "pubDate").text = periodo_pubblicazione+"+0000"
        ET.SubElement(item, "link").text = link
        #ET.SubElement(item, "guid").text = link
        ET.SubElement(item, "guid", isPermaLink="true").text = link
        ET.SubElement(item, "atom:link", href=link, rel="via", type="text/html", title="Fonte Originale")

# Funzione per ottenere il contenuto HTML di una pagina specifica
def get_page_content(url, data=None):
    response = requests.post(url, data=data)
    response.raise_for_status()  # Controlla se la richiesta è andata a buon fine
    return BeautifulSoup(response.content, "html.parser")

# URL base del sito web originale
base_url = "https://palestrina.trasparenza-valutazione-merito.it/web/trasparenza/papca-ap?p_auth=6pinQXV5&p_p_id=jcitygovalbopubblicazioni_WAR_jcitygovalbiportlet&p_p_lifecycle=1&p_p_state=normal&p_p_mode=view&p_p_col_id=column-1&p_p_col_count=1&_jcitygovalbopubblicazioni_WAR_jcitygovalbiportlet_action=eseguiPaginazione"
sitoFeed_url = "http://www.miosito.com/feed.xml"
# Ottieni il numero totale di pagine
initial_soup = get_page_content(base_url)
div_pagination = initial_soup.find("div", class_="pagination pagination-centered")
if div_pagination:
    ul_pagination = div_pagination.find("ul", id="master-detail-pagination-ul")
    if ul_pagination:
        li_active = ul_pagination.find("li", class_="active")
        if li_active:
            pagination_text = li_active.find("span").text.strip()
            total_pages = int(pagination_text.split("di")[1].split("(")[0].strip())
            print(f"Totale pagine da scansionare: {total_pages}")

            # Creazione del file RSS feed
            rss = ET.Element("rss", version="2.0", attrib={"xmlns:atom": "http://www.w3.org/2005/Atom"})
            channel = ET.SubElement(rss, "channel")
            ET.SubElement(channel, "title").text = "Feed degli atti amministrativi"
            ET.SubElement(channel, "link").text = sitoFeed_url
            ET.SubElement(channel, "description").text = "Feed RSS degli atti amministrativi del comune di Palestrina"
            ET.SubElement(channel, "atom:link", href=sitoFeed_url, rel="self", type="application/rss+xml")

            # Inizializza variabili per la paginazione
            for current_page in range(1, total_pages + 1):
                print(f"Scraping pagina {current_page}")
                # Dati per la richiesta POST
                data = {
                    "hidden_page_size": "10",  # Puoi adattare questa dimensione alla tua necessità
                    "hidden_page_to": current_page
                }
                soup = get_page_content(base_url, data)
                extract_data_from_page(soup, channel)

            # Scrive il contenuto RSS su un file
            tree = ET.ElementTree(rss)
            tree.write("feed.xml", encoding="utf-8", xml_declaration=True)
            print("Scraping completato e feed RSS creato.")
        else:
            print("Elemento 'li' con classe 'active' non trovato.")
    else:
        print("Ul con id 'master-detail-pagination-ul' non trovato.")
else:
    print("Div con classe 'pagination pagination-centered' non trovato.")
