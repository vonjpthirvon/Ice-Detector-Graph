import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from io import StringIO
import chardet
from datetime import timedelta
import copy

def calculate_icing(df: pd.DataFrame) -> pd.DataFrame:
    """Calculation of basic icing related variables based on the sensor MSO-frequency.
    These are icing intensity and ice accumulation. And some simple signal filtering has to be made in order 
    to calculate icing. Mostly based on the https://doi.org/10.1175/JAM2535.1 
    Quantitative Ice Accretion Information from the Automated Surface Observing System
    Charles C. Ryerson and Allan C. Ramsay. Sorry most of the comments are in Finnish!"""

    # Lasketaan 15 min liukuva minimi taajuudesta FZFREQ
    # HUOM. Liukuva minimi täytyy määrittää s.e. kyseisen ajan hetki ei ole mukana vain edeltävät 15 min
    # ESIM. ajanhetkelle klo 13:28 liukuva minimi määritellään arvoista 13:12-13:27, pythonissa shift(1) tekee tämän.
    # column nimi viittaa 15 minuuttiin, mutta todellisudessa 10 minuuttia.

    df['moving_minimun_15minutes'] = df['fzfreq'].shift(1).rolling(pd.Timedelta('15min1s')).min()
    # df['moving_minimun_15minutes'] = df['fzfreq'].shift(freq='30s').rolling(pd.Timedelta('10min1s')).min()

    # Lasketaan net frequency change, eli taajuuden muutos eri ajanhetkinä
    # Tämä antaa väärän tuloksen (nolla tai negatiivinen, eikä koskaan positiivinen), jos edellä on määritelty liukuva minimi s.e. kuluva ajanahetki on mukana.
    # Tämä suodattaa laitteen isompia kohinavärähtelyitä pois.
    df['NFC_orig'] = df['moving_minimun_15minutes'] - df['fzfreq']

    # Muunnetaan kaikki negatiiviset arvot nolliksi vektoroidusti.
    # Tämän jälkeen kaikki NFC olisivat nollia, mikäli liukuva 15min minimi on määritelty väärin, eli kuluva ajanhetki mukaan lukien. Tätä ei haluta.
    # df['NFC'] = np.maximum(df['NFC'], 0)
    
    # Lasketaan 10 min liukuva keskiarvo, nyt kuluva ajanhetki voi olla mukana.
    # Tällä yritetään poistaa laitteen omaa sisäistä kohinaa, joka näkyy heikkona epätodellisena jään kertymisenä.
    df['NFC_mean_10min'] = df['NFC_orig'].rolling(
        window='10min1s',# Ikkunan koko on 10 minuuttia 1s. Tämä 1 sekuntti siksi , että muuten tasan 15 min vanha havainto ei tule mukaan keskiarvon-laskentaan.
        min_periods=1,   # Laske mean, vaikka dataa olisi vähemmän kuin 15 min
        center = True    # Liukuvakeskiarvo havainto-arvon ympärillä.
    ).mean()

    # Muunnetaan kaikki negatiiviset arvot nolliksi vektoroidusti.
    df['NFC'] = np.maximum(df['NFC_orig'], 0)
    # df['NFC_mean_10min'] = np.maximum(df['NFC_mean_10min'], 0)

    # Lasketaan uusi suodatettu NFC. Joka on toivottavasti 0, jos datassa on vain kohinaa ilman oikeata jäätämistä.
    # Eli taajuudeen täytyy muuttoa keskimäärin vähintään 0.23 Hz 10 minuutin aikana, 
    # jotta tulkintan jään kertymäksi eikä kohinaksi ja (pääasiassa vesisateen aiheuttama) kohina jäisi pois 
    # mahdollisimman pitkästi. Tosin vähän vesisadesignaalia tulee joka tapauksessa läpi.
    # Tarkoittaa esimerkiksi sitä, että 10 min ajanjakson aikana on vähintään 3 kpl 1 Hz värähdyksiä
    # ja muut 7 kpl voivat olla nollia.
    df['NFC_filtered'] = np.where(
        # Ehto: Onko 10 minuutin mean (mukaan lukien nykyinen arvo) <= 0.23dHZ? Vesisadekohinan raja-arvo joka visuaalisesti 
        # määritetty datasta Mikkeli 29.9.2025 verrattuna Vantaan sadepäivän dataan 31.10.2025
        df['NFC_mean_10min'] < 0.17, 
        
        0, # Arvo, jos ehto TOTEUTUU (nollataan) eli tulkitaan data vain kohinaksi.
        
        df['NFC_mean_10min'] # Arvo, jos ehto EI TOTEUDU (käytetään alkuperäistä arvoa), eli tulkitaan data todelliseksi kertymäksi.
    )

    # instant luvuet
    df[f"mm_orig"] = df[f"NFC_orig"] * 0.00381

    # Calculate the cumulative sum
    df[f"cumul_mm_orig"] = df[f"mm_orig"].cumsum()

    # instant luvuet
    df[f"mm_mean_10min"] = df[f"NFC_mean_10min"] * 0.00381

    # Calculate the cumulative sum
    df[f"cumul_mm_mean_10min"] = df[f"mm_mean_10min"].cumsum()

    # instant luvuet
    df[f"mm_instant"] = df[f"NFC"] * 0.00381
    
    # muunnetaan Hertzi muutokset millimetreiksi. Kerroin 0.00381 tulee kirjallisuudesta.

    # Käsitellään mahdollisten sulatusjaksojen NaN arvoja vähäisemmäksi.
    # Logiigalla, että NaN korvataan edellisell ei-NaN-arvolla, jos se ei ole vanhempi kuin 15min.
    # Tämä idea tulee myös kirjallisuudesta
    nan_times = df[df["mm_instant"].isna()].index
    # Pitää kopioida taulukko toiseen muuttamattomaan taulukkoon, koska nyt taulukon arvoja korjataan.
    df_orig = df.copy()
    # print(f"mm_instant")
    # Käydään läpi jokainen mittausaika, jossa on NaN arvo.
    for mittausaika in nan_times:
        # Muodostetaan aikaikkuna, joka on tarkasteltavan Nan-mittausjasta taaksepäin 15 minuuuttia.
        window_start = mittausaika - timedelta(minutes=15)
        # Otetaan kaikki tuon aikaikkunan arvot tarkasteluun.
        window_df = df_orig.loc[window_start:mittausaika]
        # valid = window_df[f"mm_instant"].dropna()
        # Pudotetaan kaikki NaN arvot pois aikaikkunan datasta.-
        valid_df = window_df.dropna(subset=["mm_instant"]) # vaihtoehtoinen tapa jos halutaan säilyttää df:n rakenne.
        # Jos jäi vielä ei NaN arvoja jäljelle, niin muutetaan NaN arvo sopivasti. 
        # Jos ei ole enää NaN arvoja, niin "sulatusjakso" on kestänyt yli 15 minuuttia eikä sen jälkeen enää muuteta arvoja.
        if not valid_df.empty:
            # latest_valid = valid.iloc[-1]
            # Tarkastellaan suurin kellonaika, jolloin vielä saatiin ei NaN-arvo.
            latest_valid_time = valid_df.index.max()
            # katsotaan 15 min taaksepäin viimeisestä non-NaN-arvon kellonajasta.
            start_time =  latest_valid_time - timedelta(minutes=15)
            # Määritetään tämän uuden aikaikkunan (suurin non-NaN aika - 15 minuuttia) keskiarvoistusdata 
            mean_window_df = df_orig.loc[start_time:latest_valid_time]
            # Lasketaan uuden aikaikkunan keskiarvo.
            mean_value = mean_window_df["mm_instant"].mean()
            # latest_valid = valid.mean()
            # Sijoitetaan saatu keskiarvo tarkasteltavan NaN-arvon paikalle
            df.loc[mittausaika,f'mm_instant'] = mean_value
            #print(f"{mittausaika},{latest_valid}")
        #else:
            #print(f"{mittausaika}")

    # Calculate the cumulative sum
    df[f"cumul_mm"] = df[f"mm_instant"].cumsum()
    # Poistetaan NaN arvot
    df["cumul_mm"] = df["cumul_mm"].ffill()

    # instant luvuet
    df[f"mm_instant_filtered"] = df[f"NFC_filtered"] * 0.00381
    # Käsitellään mahdollisten sulatusjaksojen NaN arvoja vähäisemmäksi.
    # Logiigalla, että NaN korvataan edellisell ei-NaN-arvolla, jos se ei ole vanhempi kuin 15min.
    nan_times = df[df["mm_instant_filtered"].isna()].index
    df_orig = df.copy()
    # Pitää kopioida taulukko toiseen muuttamattomaan taulukkoon, koska nyt taulukon arvoja korjataan.
    # print(f"mm_instant_new")
    for mittausaika in nan_times:
        # print(f"{mittausaika}")
        window_start = mittausaika - timedelta(minutes=15)
        # print(f"{mittausaika}")
        window_df = df_orig.loc[window_start:mittausaika]
        #print(f"{mittausaika}")
        # valid = window_df[f"mm_instant_new"].dropna()
        # print(f"{mittausaika},{valid}")
        valid_df = window_df.dropna(subset=["mm_instant_filtered"]) # vaihtoehtoinen tapa jos halutaan säilyttää df:n rakenne.
        # Valitaan viimeisin, koska nehän on aikajärjestyksessä
        if not valid_df.empty: 
            # latest_valid = valid.iloc[-1]
            latest_valid_time = valid_df.index.max()
            start_time =  latest_valid_time - timedelta(minutes=15)
            mean_window_df = df_orig.loc[start_time:latest_valid_time]
            mean_value = mean_window_df["mm_instant_filtered"].mean()
            # latest_valid = valid.mean()
            df.loc[mittausaika,f'mm_instant_filtered'] = mean_value
            # print(f"{mittausaika},{latest_valid}")
            # df.loc[mittausaika,f'mm_instant_new'] = latest_valid
            # print(f"{mittausaika},{latest_valid}")
            # print(f"{df.loc[time]},{df.loc[time,'mm_instant_new']}")
        #else:
            # print(f"{mittausaika}")

    # Calculate the cumulative sum
    df[f"cumul_mm_filtered"] = df[f"mm_instant_filtered"].cumsum()
    # Poistetaan NaN arvot
    df["cumul_mm_filtered"] = df["cumul_mm_filtered"].ffill()   
    
    return df

def fetch_icedata(FMISID: int, starttime: str, endtime: str, place: str = None, sensor_id: int = None) -> pd.DataFrame:
    """ Valitaan paikkakunta ja tarkasteluaika, Jäätävä räntä nuoskatykky, ehkä jäätävä sumu,
    clambing/bridging tapahtuu klo 12UTC, mutta jäätäminenkin (nuoskatykky) voi jatkua vielä EFMA 22.12.2023 klo 12 UTC
    lumisade tuulen kanssa ja nollakeli jatkuu tuolloin myös
    place     = place
    starttime = start_datetime.strftime("%Y%m%dT%H%M")
    endtime   = end_datetime.strftime("%Y%m%dT%H%M") """

    # FMI OpenData-server
    url = 'http://opendata.fmi.fi/timeseries'
    producer_string = "opendata"

    # If there is more than one sensor in a site then the download string is a bit different compared to single sensor case.
    # MSOF frequensy main sensor oscillator.
    if sensor_id is not None:
        fzfreq_string = f"fzfreq_pt1m_instant(:{sensor_id}) as fzfreq"
    else:
        fzfreq_string = f"fzfreq_pt1m_instant as fzfreq"

    # definitions for data download
    payload = {
        "format": "csv",
        "timeformat": "sql",
        "producer": f"{producer_string}",
        "groupareas": "0",
        "precision": "double",
        "tz": "UTC",
        "timestep": "1m",
        "starttime": f"{starttime}",
        "endtime": f"{endtime}",
        "fmisid": f"{FMISID}",
        "param": (
            "fmisid,stationname,name,utctime,localtime,"
            f"{fzfreq_string}"
        )
    }

    # Creating and initializing Request-object
    req = requests.Request('GET',url,params=payload)
    prepared = req.prepare()

    # Print URL for debugging purposes just in case.
    print(prepared.url)

    # Download data
    response = requests.get(prepared.url)

    # Check if download was succesfull. 
    if response.status_code == 200:
        # Read CSV-data to df pd.DataFrame
        raw_data = response.content
        result = chardet.detect(raw_data)
        encoding = result['encoding']
        df = pd.read_csv(StringIO(raw_data.decode(encoding)))
        # print(df.head())
    else:
        print(f"Download failed with statuscode: {response.status_code}")
        return pd.DataFrame()

    # If there is more than one sensor in a site convert column name to ordinary.
    if f"fzfreq_#{sensor_id}" in df.columns:
        df = df.rename(columns={f"fzfreq_#{sensor_id}": "fzfreq"})

    # Convert "utctime"-column as datetime-format
    df["utctime"] = pd.to_datetime(df["utctime"], format="%Y-%m-%d %H:%M:%S")

    # UTC-time as index. Needed later.
    df.set_index('utctime', inplace=True)
    
    # Make sure there is timely order
    df = df.sort_index()

    # Calculate icing variables
    df_ice = calculate_icing(df)

    # If csv output is required uncomment these lines
    # if sensor_id is not None:
    #    df_ice.to_csv(f"{starttime}_{endtime}_{place}_{FMISID}_#{sensor_id}_muokattu.csv", index=True)
    # else:
    #    df_ice.to_csv(f"{starttime}_{endtime}_{place}_{FMISID}_muokattu.csv", index=True)
    
    # Output is dataframe
    return df_ice