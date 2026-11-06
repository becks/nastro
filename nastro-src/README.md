# Nastro – sorgenti

I file `.pd` in `../Nastro` sono generati da questi script. Si modificano gli script, non i `.pd`.

    python3 gen.py ../Nastro        # rigenera tutta la patch (main.pd + moduli)
    python3 gensim.py ../Nastro     # rigenera mac-sim.pd (simulatore per Mac)
    python3 makekit.py ../Nastro/drums.wav   # rigenera il kit di batteria

`gen.py` esegue gli altri `gen*.py` (tape, screen, mix, tempo, drum, tapemap, synth, seq).

Organelle di riferimento: Organelle 1, OS 4.0, Pd 0.49, 1 core ARM, Pd avviato con -audiobuf 6.
Regole emerse dai test: evitare picchi di lavoro di controllo > ~2 ms per blocco (spezzare i loop lunghi),
ridisegnare l'OLED solo quando cambia qualcosa.
