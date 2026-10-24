# Officina Snella – versione statica

Mirror statico di <https://www.officinasnella.com> (WordPress), pubblicato con GitHub Pages dalla cartella `docs/`.

## Rigenerare il sito

```bash
tools/build.sh
```

Il dominio ora punta a GitHub Pages: per riscaricare il WordPress originale serve aggiungere temporaneamente a `/etc/hosts` la riga `3.123.199.162 www.officinasnella.com` (lo script si ferma con un avviso se il WordPress non è raggiungibile).

Lo script:
1. raccoglie tutte le pagine, articoli, categorie e tag dalle API REST di WordPress;
2. scarica il sito con `wget` (pagine + CSS/JS/immagini/font) in `docs/`;
3. esegue `tools/postprocess.py`, che ripulisce i nomi dei file (`?ver=…`), rimuove i riferimenti al backend WordPress (feed, oEmbed, xmlrpc, emoji) e il banner cookie (plugin GDPR Cookie Compliance), e sostituisce Google Fonts con la copia locale in `static/fonts/`, converte i link `?p=NN` nei percorsi reali e rende relativi i link rimasti assoluti.

Per un dominio personalizzato, creare un file `CNAME` nella root del repo: `build.sh` lo copia in `docs/`.

I file in `static/` (font, immagini mancanti) vengono copiati in `docs/` a ogni build.

## Limiti

Le funzioni dinamiche (form di contatto/registrazione eventi, prenotazioni, ricerca) non funzionano sulla versione statica.
