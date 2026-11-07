# Nastro – sorgenti

I file `.pd` in `../Nastro` sono generati da questi script. Si modificano gli script, non i `.pd`.

    python3 gen.py ../Nastro        # rigenera tutta la patch (main.pd + moduli)
    python3 gensim.py ../Nastro     # rigenera mac-sim.pd (simulatore per Mac)
    python3 makekit.py ../Nastro/drums.wav   # rigenera il kit di batteria

`gen.py` esegue gli altri `gen*.py` (tape, screen, mix, tempo, drum, tapemap, synth, seq, smpl, proj, tapeedit).

Test headless sul Mac (Pd 0.54 `-batch`): `test_edit.py`, `test_loopclick.py`, `test_limiter.py`, `test_autorec.py`, `test_tomb.py`, `test_reverb.py` (editing del nastro, confronto campione per campione),
`test_nav.py`, `test_smpl.py`, `test_click.py`, `test_pan.py`, `test_proj.py`, `test_drumrec.py`, `test_monitor.py`.

## Loop senza clic
Al giro del loop (e a ogni salto della testina) una seconda testina per traccia continua oltre il punto di salto e
sfuma in 5 ms mentre la principale entra in dissolvenza (`apply_xfade.py`, test: `test_loopclick.py`).
Solo l'uscita è in crossfade; l'overdub legge la testina principale.

## Motori ambient ARIA e VETRO (`apply_ambient.py`, voci in `gensynth.py`)
5 ARIA: rumore in 2 passa-banda (nota + ottava, vcf~), Q da soffio (2) a fischio (60) con guadagno sqrt(Q),
LFO lento casuale per voce su intonazione e livello. Manopole ATK REL Q MOTO (contesto 18).
6 VETRO: 4 parziali (armoniche 1 2 3 4 <-> campana 1 2.76 5.4 8.93), decadimento più corto per le parziali alte,
2 gemelle stonate per i battimenti, 6 voci, suona fino in fondo anche dopo il note-off. Manopole DECAY BRITE INARM
BATT (contesto 19, `pkval` 80). Test: `test_ambient.py`.

## ENDLESS (`genendl.py` → `endl.pd`, collegamenti in `apply_endl.py`)
Quarta pagina di SEQ (AUX+E: TEMPO → STEP → TOMBOLA → ENDLESS). Fermo: ogni tasto aggiunge una nota (max 64),
AUX+A# una pausa, AUX+B cancella; AUX+C5 avvia/ferma. Gira col tempo del nastro (tick16) all'infinito; un tasto
mentre suona traspone rispetto alla prima nota. Manopole (contesto 17, `pkval` 72): RATE 1/4–1/32, GATE,
DIREZIONE (>> << <> ??), PROB. Salvato con il progetto (`p<N>-endn.txt`, `p<N>-endp.txt`). Schermo: ridisegno
completo solo quando cambia qualcosa, il cursore si sposta invertendo 2 colonne. Test: `test_endl.py`.

## Lucine dell'uscita (`genmeter.py` → `meter.pd`, ganci in `apply_meter.py`)
Riga del titolo della pagina MIX (livelli): L e R, 12 segmenti da -30 a 0 dBFS (env~ dopo limiter e mute),
discesa di un segmento per fotogramma, lucina LIM quando il limiter lavora. 10 fps, si disegnano solo i
segmenti che cambiano; `mt-reset` quando la pagina cancella lo schermo.

**Attenzione (Pd 0.49 sull'Organelle):** `expr` non ha `mtof()` (usare l'oggetto `[mtof]` prima). Funzioni disponibili: vedi `ex_*` nel binario.

**Attenzione (Pd):** `expr` con più uscite calcola ogni uscita solo quando la manda (da destra a sinistra). Se
un'uscita scrive in una tabella che le altre leggono, raccogliere prima tutto in `[pack]` e scrivere dopo.

## Velocità del nastro
Manopola 1 in TAPE: 7 scatti in ottave (-2 -1 -0.5 0 0.5 1 2) distribuiti sulla corsa; con AUX tenuto continua
(-2..2, calamite su 1 / 0 / -1). Globale per tutte le tracce. In rec resta forzata a 1x.

## Progetti: partenza vuota (`apply_projnew.py`)
All'avvio Nastro parte vuoto (progetto 0: nessun file, quindi tutti i valori iniziali). "+ NUOVO" carica il progetto 0
(azzera tutto, anche le palline della TOMBOLA). Si carica un progetto solo scegliendolo dalla lista. Salvare il
progetto 0 (AUX+A o SALVA NUOVO) gli assegna il primo numero libero. `current.txt` non serve più per l'avvio.
La TOMBOLA distribuisce il lavoro: una pallina ogni 3,75 ms, disegno in due tempi (`apply_tombspread.py`).
Test: `test_startempty.py`.

## Riverbero (`genrev.py` → `reverb.pd`, collegamenti in `apply_reverb.py`)
Pre-delay (vd~) → 4 allpass in serie → FDN a 8 linee (31.7–73.7 ms, Hadamard a farfalle), lop~ e guadagno di
decadimento per linea (10^(-3L/T60)/√8), 2 linee modulate (vd~). Pari a sinistra, dispari a destra. AUX + manopole
sulla pagina FX: DEC (T60 0.4–12 s), TONO (1.5–12 kHz), PRE (0–120 ms), MOD. Contesto pickup 16 (`pkval` 68).
`switch~`: acceso quando REV > 0, spento T60+0.5 s dopo che REV va a 0. Livello pari al vecchio riverbero.
Test: `test_reverb.py`. Nota: `[r nome]` non ha ingresso, per unire due receive collegarli entrambi alla destinazione.

## TOMBOLA (`gentomb.py` → `tomb.pd`, collegamenti in `apply_tomb.py`)
Terza pagina di SEQ (AUX+E: TEMPO → STEP → TOMBOLA). Poligono rotante (3–8 lati) con fino a 8 palline; ogni tasto
lancia una pallina con la sua nota, l'urto con una parete suona la nota (velocity dall'urto) sullo strumento attivo
via `seq-notes`. Manopole (contesto pickup 15, `pkval` a 64): giro, gravità, rimbalzo, lati. AUX+A# toglie l'ultima,
AUX+B tutte, AUX+C5 pausa. Suona solo mentre la sua pagina è visibile (uscendo si ferma, le palline restano). Fisica a 33 tick/s solo con palline presenti; per pallina: movimento, settore, scelta tra
3 pareti (angoli), rimbalzo con spinta della parete. Schermo ~11 fps, testo solo quando cambia. Test: `test_tomb.py`.

## Revisione (strumenti in `review.py`, `review_order.py`, `errscan.py`)
- `python3 review.py ../Nastro`: send/receive senza controparte, collegamenti verso `[r]`, `[delay]` con float,
  funzioni `expr` non in Pd 0.49, oggetti orfani, conteggio oggetti audio per patch.
- `python3 review_order.py ../Nastro`: uscite collegate a un inlet freddo e a un percorso caldo che lo raggiunge.
- `python3 errscan.py test_X.py`: esegue un test e riporta ogni errore di Pd inatteso.
- Ogni voce (synth e batteria) ha il suo `switch~` (`apply_voiceswitch.py`): accesa alla nota, spenta a suono
  finito (PLUK `switch~ 16`). Da fermo -42% di calcolo.

## SMPL: vista dal vivo leggera (`apply_smplive.py`)
Durante la registrazione si disegna solo la barretta appena misurata (3 messaggi ogni 100 ms, scala fissa) invece
di ridisegnare tutta la pagina SYNTH (~60 messaggi): da 610 a 30 messaggi OLED al secondo. Ridisegno completo alla fine.

## Mirror dello schermo (`genmirror.py` → `mirror.pd`, voce di menu in `apply_mirrormenu.py`)
Spento all'avvio. Menu PROGETTI → "SCHERMO SU MAC: OFF/ON". L'IP del computer sta in `mirror.txt` accanto alla
patch (es. `192.168.1.114;`); se manca: MANCA-MIRROR.TXT. Ogni comando OLED (e il LED) va via UDP sulla porta 9123.
Sul computer: `OLED_BIND=0.0.0.0 python3 oled-sim.py`, aprire http://localhost:8123 e registrare la finestra.

## Editing su tutte le tracce (`apply_editall.py`, `apply_editall_menu.py`)
Voce del menu EDIT "MODO: 1 TRACCIA / TUTTE" (op 8). Con TUTTE ogni operazione 1..6 viene eseguita per le tracce
1..4 in sequenza (stato in tabella `teseq`), riusando il codice a traccia singola: appunti e annulla hanno 4
scomparti (offset (k-1)*lunghezza), la regione si calcola solo alla prima traccia, DUPLICA sposta il loop solo
all'ultima. ANNULLA dopo un'operazione su tutte annulla tutte e 4. Test: `test_editall.py`.

## ANNULLA, limiter, partenza automatica
- ANNULLA (menu EDIT): prima di ogni modifica la regione toccata va in `te-undo`; ANNULLA la scambia col nastro
  (premuto di nuovo = ripristina). Registrare o caricare un progetto cancella l'annullamento (`apply_undo.py`).
- Limiter sul master (`apply_limiter.py`): picco per blocco (`tabsend~` + `array max`), soglia 0.89, attacco
  immediato, rilascio ~150 ms, `clip~` finale. Nessuna latenza aggiunta. Fuori dal limiter: metronomo e ingresso del nastro.
- Partenza automatica (`apply_autorec.py`): AUX+E5 (ingresso) arma la registrazione (badge ATT), che parte quando
  il segnale supera 0.03; pre-roll di 15 ms con `delwrite~`/`delread~`. Ripremere mentre è in attesa = annulla.
  AUX+F5 (uscita di Nastro) parte subito come prima. `threshold~` in Pd non ha un messaggio per azzerare lo stato.

## Editing del nastro (`gentapeedit.py` → `tapeedit.pd`)
Encoder premuto in TAPE → menu `EDIT-T n`: TAGLIA, COPIA, INCOLLA, INVERTI, CANCELLA, DUPLICA sulla traccia
selezionata, sulla regione del loop (se attivo) o sulla battuta corrente. Copie spezzate a 4096 campioni per tick
(`array get/set`, nome tabella nell'inlet destro: in Pd 0.49 non esiste il messaggio `set`). L'inversione passa in
tempo reale con contatore `rpole~` + `tabwrite~` (allineati al blocco; `vline~` sfasava di ~80 campioni).

Organelle di riferimento: Organelle 1, OS 4.0, Pd 0.49, 1 core ARM, Pd avviato con -audiobuf 6.
Regole emerse dai test: evitare picchi di lavoro di controllo > ~2 ms per blocco (spezzare i loop lunghi),
ridisegnare l'OLED solo quando cambia qualcosa.

## Idee future (decise con l'utente, da fare più avanti)
- **Registrazione del nastro a velocità diversa da 1x** (come l'OP-1: registri a metà velocità, in play a 1x suona un'ottava sopra).
  Oggi rec forza 1x perché `tabwrite~` scrive solo in sequenza. Piano: registrare in un buffer temporaneo a 1x e, allo
  stop (o a ogni giro di loop), ricampionarlo alla velocità del nastro e sommarlo sulla traccia (overdub), con la
  conversione spezzata su più blocchi per non far glitchare l'Organelle. Possibile anche al contrario.
- Annulla dell'ultima registrazione in un tasto DRUM / ripristino del suono di base del tasto.
- Regolazione fine di START/END (es. AUX + knob = passi 20x più piccoli).
- Altro montaggio del nastro (selezione libera oltre loop/battuta, annullare una registrazione), MIDI in/clock, nomi dei progetti.

Attenzione: non lanciare un secondo Pd `-batch` sull'Organelle mentre la patch gira (l'ha bloccata/riavviata).
