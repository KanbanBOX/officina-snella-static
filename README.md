# Officina Snella – versione statica

Mirror statico di <https://www.officinasnella.com> (WordPress), pubblicato con GitHub Pages dalla cartella `docs/`.

## Rigenerare il sito

```bash
tools/build.sh
```

Lo script:
1. raccoglie tutte le pagine, articoli, categorie e tag dalle API REST di WordPress;
2. scarica il sito con `wget` (pagine + CSS/JS/immagini/font) in `docs/`;
3. esegue `tools/postprocess.py`, che ripulisce i nomi dei file (`?ver=…`), rimuove i riferimenti al backend WordPress (feed, oEmbed, xmlrpc, emoji), converte i link `?p=NN` nei percorsi reali e rende relativi i link rimasti assoluti.

Per un dominio personalizzato, creare un file `CNAME` nella root del repo: `build.sh` lo copia in `docs/`.

## Limiti

Le funzioni dinamiche (form di contatto/registrazione eventi, prenotazioni, ricerca) non funzionano sulla versione statica.
