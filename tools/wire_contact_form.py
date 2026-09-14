# -*- coding: utf-8 -*-
"""
Ricollega il form "Contattaci" a un servizio esterno (Formspree o compatibile),
mantenendo identico l'aspetto grafico del form Jetpack originale.

Uso:
    python tools/wire_contact_form.py site [ENDPOINT]

Se ENDPOINT non viene passato resta il placeholder e il form usa il fallback
mailto: (apre il client di posta con i campi gia' compilati).
"""
import sys, io, os, re, json
from bs4 import BeautifulSoup

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = sys.argv[1]
ENDPOINT = sys.argv[2] if len(sys.argv) > 2 else "FORMSPREE_ENDPOINT_DA_CONFIGURARE"
FALLBACK_EMAIL = "comitatoiniziativepopolari@gmail.com"
PAGE = os.path.join(ROOT, "mettiti-in-contatto-con-noi", "index.html")

FIELD_MAP = {
    "gblock-template-canvas-nome": "name",
    "gblock-template-canvas-email": "email",
    "gblock-template-canvas-messaggio": "message",
}
DROP_HIDDEN = {"jetpack_contact_form_jwt", "contact-form-id", "action", "contact-form-hash"}

with open(PAGE, encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "lxml")

form = soup.find("form", class_="contact-form")
if form is None:
    print("ERRORE: form non trovato")
    sys.exit(1)

container = form.find_parent(id=re.compile("^contact-form-")) or form.parent

# 1. rimuovi i campi nascosti di Jetpack (JWT, nonce, action)
removed = 0
for inp in form.find_all("input", {"type": "hidden"}):
    if inp.get("name") in DROP_HIDDEN:
        inp.decompose()
        removed += 1

# 2. rinomina i campi con nomi leggibili nelle email di notifica
renamed = 0
for el in form.find_all(["input", "textarea", "label"]):
    n = el.get("name")
    if n in FIELD_MAP:
        el["name"] = FIELD_MAP[n]
        renamed += 1
    fo = el.get("for")
    if fo in FIELD_MAP:
        el["for"] = FIELD_MAP[fo]
    i = el.get("id")
    if i in FIELD_MAP:
        el["id"] = FIELD_MAP[i]

# aggiorna anche gli aria-describedby che puntavano ai vecchi id
for el in form.find_all(attrs={"aria-describedby": True}):
    v = el["aria-describedby"]
    for old, new in FIELD_MAP.items():
        v = v.replace(old, new)
    el["aria-describedby"] = v

# 3. togli le direttive dell'Interactivity API (inerti nel sito statico)
stripped = 0
for el in container.find_all(True):
    for a in [a for a in el.attrs if a.startswith("data-wp-")]:
        del el[a]
        stripped += 1
for a in [a for a in container.attrs if a.startswith("data-wp-")]:
    del container[a]
    stripped += 1

# 4. configura il form
form["action"] = ENDPOINT
form["method"] = "post"
form["id"] = "cip-contact-form"
if form.has_attr("novalidate"):
    del form["novalidate"]

# honeypot antispam (Formspree lo riconosce come _gotcha)
hp = soup.new_tag("input", attrs={
    "type": "text", "name": "_gotcha", "tabindex": "-1",
    "autocomplete": "off", "aria-hidden": "true",
    "style": "position:absolute;left:-9999px;width:1px;height:1px;opacity:0",
})
form.insert(0, hp)

# 5. pannello esito (riusa i colori del sito)
status = soup.new_tag("div", attrs={
    "id": "cip-form-status", "role": "status", "aria-live": "polite", "hidden": "",
    "style": ("margin:16px 9vh;padding:14px 18px;border-radius:12px;"
              "border:2px solid #146894;color:#146894;font-size:1rem;line-height:1.5"),
})
form.insert_after(status)

# rimuovi il pannello di successo di Jetpack (dipendeva dal runtime WP)
old = container.find(class_="contact-form-submission")
if old:
    old.decompose()

# 6. comportamento: etichette "notched" + invio asincrono + fallback mailto
script = soup.new_tag("script")
script.string = """
(function () {
  var ENDPOINT = %s;
  var FALLBACK_EMAIL = %s;
  var form = document.getElementById('cip-contact-form');
  if (!form) return;
  var status = document.getElementById('cip-form-status');
  var configured = ENDPOINT.indexOf('http') === 0;

  // l'etichetta "notched" si alza quando il campo ha un valore
  function sync(el) { el.classList.toggle('has-value', !!el.value); }
  var fields = form.querySelectorAll('input.grunion-field, textarea.grunion-field');
  Array.prototype.forEach.call(fields, function (el) {
    sync(el);
    el.addEventListener('input', function () { sync(el); });
    el.addEventListener('blur', function () { sync(el); });
  });

  function show(msg, ok) {
    status.textContent = msg;
    status.style.borderColor = ok ? '#146894' : '#b32d2e';
    status.style.color = ok ? '#146894' : '#b32d2e';
    status.hidden = false;
    status.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    if (form.querySelector('[name="_gotcha"]').value) return;   // bot
    var data = new FormData(form);
    var nome = (data.get('name') || '').trim();
    var email = (data.get('email') || '').trim();
    var msg = (data.get('message') || '').trim();
    if (!nome || !email || !msg) { show('Compila tutti i campi obbligatori.', false); return; }

    // Nessun endpoint configurato: apri il client di posta
    if (!configured) {
      var body = 'Nome: ' + nome + '\\nEmail: ' + email + '\\n\\n' + msg;
      window.location.href = 'mailto:' + FALLBACK_EMAIL
        + '?subject=' + encodeURIComponent('Contatto dal sito - ' + nome)
        + '&body=' + encodeURIComponent(body);
      show('Si apre il tuo programma di posta per completare l\\'invio.', true);
      return;
    }

    var btn = form.querySelector('button[type="submit"], input[type="submit"]');
    if (btn) { btn.disabled = true; }
    fetch(ENDPOINT, { method: 'POST', body: data, headers: { Accept: 'application/json' } })
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        form.reset();
        Array.prototype.forEach.call(fields, sync);
        show('Grazie, il messaggio e\\' stato inviato. Ti risponderemo presto.', true);
      })
      .catch(function () {
        show('Invio non riuscito. Scrivici a ' + FALLBACK_EMAIL, false);
      })
      .finally(function () { if (btn) { btn.disabled = false; } });
  });
})();
""" % (json.dumps(ENDPOINT), json.dumps(FALLBACK_EMAIL))
form.insert_after(script)

with open(PAGE, "w", encoding="utf-8") as f:
    f.write(str(soup))

print("Form Contattaci ricollegato.")
print("  campi nascosti Jetpack rimossi : %d" % removed)
print("  campi rinominati               : %d" % renamed)
print("  direttive data-wp-* rimosse    : %d" % stripped)
print("  endpoint                       : %s" % ENDPOINT)
if not ENDPOINT.startswith("http"):
    print("  -> non configurato: il form usa il fallback mailto: verso %s" % FALLBACK_EMAIL)
