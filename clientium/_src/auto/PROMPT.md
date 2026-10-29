Scrivi 3 frasi per una pagina di Clientium rivolta al titolare di un'azienda B2B italiana (il LEAD). Clientium porta appuntamenti B2B qualificati e il cliente paga solo quelli che si presentano. Ricevi pochi fatti dal sito del lead e il suo MARKET (i decisori che contatteremmo per lui). Restituisci SOLO un oggetto JSON.

REGOLE
- Ogni numero deve comparire nei fatti esattamente così. Mai inventare, arrotondare o calcolare numeri.
- Niente trattini, niente punti esclamativi, niente grassetto. Italiano corretto con gli accenti. Dai del tu.
- Niente prezzi, costi di attivazione, durate. Non nominare software. Non dire che il sito non ha qualcosa.
- Nome azienda breve, mai tutto maiuscolo, mai la forma societaria.
- Descrivi cosa vende il lead solo con parole prese dai suoi fatti.

FRASI
"cover_sub": 14 a 24 parole, cos'è questa pagina e perché è per lui, senza numeri.
"market_line": 18 a 28 parole, inizia con il nome dell'azienda e cosa vende, poi perché i decisori del MARKET sono quelli giusti.
"offer_tail": 12 a 22 parole, come si applica a lui il modello paghi solo i risultati.

ESEMPIO
FATTI:
LEAD: Marco Bianchi, Termoprogetti, https://termoprogetti.it
SITE OFFERS: sopralluogo gratuito
MARKET (our data): 8.410 responsabili di stabilimento di aziende logistiche e alimentari
HOMEPAGE: Impianti termici per industria e logistica dal 1999...
OUTPUT:
{"cover_sub": "Una pagina breve su chi contatteremmo per te e su cosa funziona oggi nel tuo mercato.", "market_line": "Termoprogetti progetta impianti termici per industria e logistica, quindi parleremmo con chi gestisce lo stabilimento e vive il problema ogni giorno.", "offer_tail": "Per Termoprogetti vuol dire pagare solo i sopralluoghi fissati con responsabili in target che si presentano."}
