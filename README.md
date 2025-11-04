# Ice-Detector-Graph

**Ice-Detector-Graph** on Streamlit-pohjainen sovellus, joka visualisoi jään kertymistä ja siihen liittyviä sääparametreja eri paikkakunnilla Suomessa. Sovellus hyödyntää FMI:n avointa rajapintaa ja tarjoaa interaktiivisia kuvaajia jään muodostumisen analysointiin.

## 🔧 Ominaisuudet

- Valitse paikkakunta ja anturi (esim. Vantaa: #10 tai #37)
- Määritä aikaväli ja kellonajat
- Hae data FMI:n OpenData-rajapinnasta
- Visualisoi:
  - Jään kertymä (mm)
  - Jään intensiteetti (mm/min)
  - Taajuusmuutokset (Hz)
  - Suodatettu ja alkuperäinen NFC (Net Frequency Change)
- Interaktiivinen muuttujien valinta ja Plotly-kuvaajat

## 📁 Tiedostot

- `streamlit_app.py`: Käyttöliittymä ja päälogiikka
- `data_fetchers.py`: Datan haku FMI:n rajapinnasta ja jään laskenta
- `plotters.py`: Matplotlib- ja Plotly-pohjaiset kuvaajat

## ▶️ Käynnistys

Varmista, että sinulla on tarvittavat riippuvuudet asennettuna:

```bash
