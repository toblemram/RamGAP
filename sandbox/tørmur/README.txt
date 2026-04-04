# Streamlit-app for tørrmurberegning

Filer:
- `app.py` – Streamlit-appen
- `Dimensjonering av tørrmurer iht V220_rev 1.xltm` – original Excel-mal brukt som beregningsmotor
- `requirements.txt` – avhengigheter

Kjøring:
1. Opprett virtuelt miljø (valgfritt)
2. Installer pakker:
   pip install -r requirements.txt
3. Start appen:
   streamlit run app.py

Notater:
- Appen bruker Excel-formlene direkte via Python-pakken `formulas`.
- Layouten er tilpasset web, men inndatafeltene, hovedresultatene og beregningslogikken følger Excel-arket.
- Tomme numeriske felt sendes ikke inn som overstyringer, slik at oppførselen ligger nærmere originalmalen.
