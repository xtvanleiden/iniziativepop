# iniziativepop.it — copia di comitatoiniziativepopolari.it

Copia completa del sito del **Comitato Iniziative Popolari**, preparata per il nuovo dominio
**iniziativepop.it**.

Data copia: 14 settembre 2026
Sorgente: `https://comitatoiniziativepopolari.it/`

---

## Cosa c'è in questa cartella

| Cartella | Contenuto |
|---|---|
| `site/` | **Mirror statico completo** del sito, pronto da pubblicare (359 file, 41 MB) |
| `export/` | **Contenuti sorgente** esportati via WordPress REST API (JSON) |
| `tools/` | Gli script usati, riutilizzabili per riaggiornare la copia |
| `_mirror_report.json` | Report tecnico della copia |

### `tools/`

| Script | Cosa fa |
|---|---|
| `mirror.py` | Scarica il sito e riscrive i link a percorsi relativi |
| `fetch_media.py` | Scarica tutta la media library, originali e dimensioni generate |
| `export_api.py` | Esporta i contenuti via REST API in `export/` |
| `rewrite_domain.py` | Sostituisce il vecchio dominio con quello nuovo |
| `wire_contact_form.py` | Collega il form Contattaci a un servizio esterno |
| `fix_404.py` | Sostituisce la ricerca nella pagina 404 con link alle sezioni |
| `make_sitemap.py` | Genera `sitemap.xml` e `robots.txt` per il nuovo dominio |
| `check_links.py` | Verifica che ogni riferimento locale punti a un file esistente |

Per riaggiornare la copia dopo modifiche al sito originale, **in quest'ordine**:

```bash
python tools/mirror.py site
python tools/fetch_media.py site export
python tools/rewrite_domain.py site      # rinomina anche le cartelle col vecchio dominio
python tools/wire_contact_form.py site   # aggiungi l'endpoint se configurato
python tools/fix_404.py site
python tools/make_sitemap.py site
python tools/check_links.py site         # deve dire: MANCANTI 0
```

L'ordine conta: `mirror.py` riscrive le pagine, quindi i passi successivi vanno rifatti dopo.

### `site/` — il sito statico

| | |
|---|---|
| Pagine HTML | 28 (9 pagine + 19 articoli) |
| PDF | 29 |
| Immagini | 175 (tutte le dimensioni generate da WordPress) |
| CSS / JS / Font | 19 / 62 / 40 |
| Documenti Word e testo | 5 |

Tutti i riferimenti interni sono stati riscritti a **percorsi relativi**, e ogni URL assoluto
residuo punta ora a `iniziativepop.it`. Verifica automatica: **2896 riferimenti locali
controllati, 0 mancanti**.

Gli asset che il sito originale caricava da CDN esterne (Jetpack `i0.wp.com` / `c0.wp.com`,
Google Fonts) sono stati **scaricati in locale** sotto `site/_ext/`, così il sito non dipende
più dal vecchio dominio.

### `export/` — i contenuti grezzi

`pages.json` (9), `posts.json` (19), `media.json` (44), `categories.json`, `users.json`,
`comments.json` (343), `wp-json-root.json`.

Servono se si vuole **ricostruire un WordPress vero** sul nuovo dominio: contengono titoli,
testo, HTML dei blocchi, date, slug e riferimenti ai media di ogni pagina e articolo.

---

## Come pubblicare il sito

Il progetto è già configurato per **Netlify** (`netlify.toml`) e **Vercel** (`vercel.json`).
Entrambi pubblicano la cartella `site/` senza nessuna build, con HTTPS automatico.

### Via GitHub (consigliato)

Ogni modifica al repository ripubblica il sito da sola.

```bash
git add -A
git commit -m "Sito iniziativepop.it"
gh repo create iniziativepop --private --source=. --push
```

Poi su [netlify.com](https://app.netlify.com) → *Add new site* → *Import an existing project*
→ scegli il repository. Netlify legge `netlify.toml` e pubblica `site/`.
Su Vercel il procedimento è identico e legge `vercel.json`.

> **Il repository deve restare privato.** `export/` contiene i 343 commenti e i profili
> autore esportati dal sito, con **indirizzi email di persone reali**. Se ti serve un
> repository pubblico, togli prima il commento alla riga `export/` in `.gitignore`.

### Senza GitHub (trascinamento)

Su [app.netlify.com/drop](https://app.netlify.com/drop) trascina la cartella `site/`:
il sito è online in pochi secondi. In questo caso `netlify.toml` non viene letto, quindi le
intestazioni di cache e sicurezza non vengono applicate — il sito funziona comunque.

### Collegare il dominio

Nel pannello Netlify (o Vercel) → *Domain settings* → aggiungi `iniziativepop.it`, poi
imposta dal registrar i record DNS che ti vengono indicati. Il certificato HTTPS viene
emesso automaticamente.

### Test in locale

```bash
cd site
python -m http.server 8000
# apri http://localhost:8000
```

---

## Parti dinamiche: stato

Il sito originale è **WordPress 6.8.8** (tema `extendable`). Analizzando pagina per pagina,
le parti che richiedevano PHP + database sono **molte meno del previsto**:

| Funzione | Stato nella copia |
|---|---|
| Testi, immagini, PDF, layout, grafica | ✅ identici all'originale |
| **Iscrizione al Comitato** | ✅ **funziona già** — è solo il PDF da scaricare, il bonifico su IBAN e l'invio via email. Nessun modulo online da ricollegare |
| **Contattaci** | ✅ **ricollegato** a servizio esterno (vedi sotto) |
| Donazioni **GiveWP** | ➖ il plugin è installato ma **nessun modulo di donazione è pubblicato** sul sito: niente da migrare |
| **WooCommerce** | ➖ nessun prodotto e nessun prezzo pubblicato: solo scaffolding del plugin, niente da migrare |
| Ricerca interna | ❌ non disponibile |
| Commenti (343 nel database) | ❌ non si può commentare |
| Pannello `/wp-admin` | ❌ assente per definizione |

### Il modulo "Contattaci"

Il form Jetpack originale è stato riscritto in `site/mettiti-in-contatto-con-noi/index.html`
mantenendo **identica la grafica** (stesse classi CSS, stesse etichette "notched" animate,
stesso colore `#146894`). Cosa è cambiato sotto:

- rimossi i 4 campi nascosti di Jetpack (JWT, nonce, action) che il sito statico non può validare;
- campi rinominati in `name` / `email` / `message`, leggibili nelle email di notifica;
- rimosse 89 direttive `data-wp-*` dell'Interactivity API, inerti senza WordPress;
- aggiunto un honeypot antispam (`_gotcha`);
- aggiunto invio asincrono con messaggio di esito e riabilitazione del pulsante.

**Adesso funziona in modalità fallback**: premendo Invia si apre il programma di posta
dell'utente con i campi già compilati, verso `comitatoiniziativepopolari@gmail.com`.
Funziona subito, senza registrarsi da nessuna parte.

**Per ricevere i messaggi direttamente via email** (senza che si apra il client di posta):

1. Registra un account gratuito su [formspree.io](https://formspree.io) (50 invii/mese
   nel piano gratuito) e crea un form: ti darà un endpoint tipo
   `https://formspree.io/f/xxxxxxxx`.
2. Lancia:

   ```bash
   python tools/wire_contact_form.py site https://formspree.io/f/xxxxxxxx
   ```

Lo script è idempotente: si può rilanciare per cambiare endpoint.
Alternative equivalenti a Formspree: **Web3Forms**, **FormSubmit**, **Basin**.

---

## Se invece serve un WordPress identico e funzionante

La copia statica **non** è una migrazione. Per avere su `iniziativepop.it` un sito
completamente identico e amministrabile serve la migrazione vera, cioè:

1. **File** — l'intera cartella `public_html/` dal vecchio hosting (include `wp-content`:
   tema, plugin, upload).
2. **Database MySQL** — export `.sql` completo.
3. Ripristino sul nuovo dominio e aggiornamento degli URL nel database
   (`siteurl`, `home` e tutte le occorrenze serializzate).

Richiede l'accesso al pannello Hostinger (hPanel) del sito attuale: da lì con
**Strumenti → Migrazione sito** oppure con un plugin (All-in-One WP Migration, Duplicator)
si sposta tutto in modo pulito.

---

## Cose da controllare prima di andare online

- **Email**: nel sito originale il footer riporta `info@comitatoiniziativepopolari.it`.
  Nella copia è stato riscritto in **`info@iniziativepop.it`** — va creata questa casella,
  altrimenti il contatto non riceve nulla. L'indirizzo Gmail
  `comitatoiniziativepopolari@gmail.com` è stato lasciato invariato.
- **Redirect 301** dal vecchio dominio al nuovo, per non perdere il posizionamento.
- **Iubenda** (cookie/privacy, siteId `4167037`): la configurazione è legata al vecchio
  dominio, va aggiunto il nuovo.
- **Google Site Kit / Analytics**: da riconfigurare sul nuovo dominio.
- **Link social** (Facebook, Instagram, X, WhatsApp) e gli embed YouTube restano invariati.
