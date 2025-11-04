import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
from io import StringIO
import chardet
# from datetime import datetime, time
from datetime import datetime, time, timedelta, date
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def plot_icegraph(
    df: pd.DataFrame,
    place: str,
    fmisid: int,
    start_datetime: datetime,
    end_datetime: datetime,
    sensor_id: int = None) -> Figure:
    """plotting of ice data"""
    # Create a figure and two subplots (one above the other)

    # Plotattavan jakson pituus
    duration = end_datetime - start_datetime

    # Muunna tekstiksi
    starttime = start_datetime.strftime("%Y%m%dT%H%M")
    endtime   = end_datetime.strftime("%Y%m%dT%H%M")
    
    # If sensor_id exists. And if not.
    if sensor_id is not None:
        fzfreq_label = f"fzfreq#{sensor_id}"
    else:
        fzfreq_label = f"fzfreq"

    fig, (ax1, ax2, ax3, ax4, ax5) = plt.subplots(5, 1, figsize=(16, 16), sharex = True)

    ax2.plot(df.index, df[f"fzfreq"], label=f"{fzfreq_label}", linestyle=':', color = 'blue')
    ax2.plot(df.index, df[f"moving_minimun_15minutes"], label=f"fz10min", marker="", linestyle=':', color = 'red')
    # ax4.plot(df.index, df[f"NFC_orig"], label=f"NFC_orig", linestyle=':', color = 'blue')
    ax4.plot(df.index, df[f"NFC"], label=f"NFC", linestyle='--', color = 'red')
    ax5.plot(df.index, df[f"NFC_filtered"], label=f"NFC_filtered", linestyle=':', color = 'red')
    ax3.plot(df.index, df[f"mm_instant"], label=f"mm inst", linestyle='--', color = 'blue')
    ax3.plot(df.index, df[f"mm_instant_filtered"], label=f"mm instant filtered", linestyle=':', color = 'red')
    ax1.plot(df.index, df[f"cumul_mm_filtered"], label=f"cumul mm filtered", linestyle='--', color = 'red')
    # ax1.plot(df.index, df[f"cumul_mm_orig"], label=f"cumul mm orig", linestyle=':', color= 'blue')
    ax1.plot(df.index, df[f"cumul_mm"], label=f"cumul mm", linestyle='-.', color= 'green')

    # ax1.set_xlabel("Kellonaika")
    ax2.set_ylabel("FZFREQ/Hz")
    ax2.set_title("FZFREQ raw/min(10min) filtered ")
    ax2.grid(True, which='major', axis='both',linestyle='--', color='gray', linewidth=0.5)

    ax4.set_ylabel("NFC/dHz")
    ax4.set_title("Net Frequency Change ")
    ax4.grid(True, which='major', axis='both',linestyle='--', color='gray', linewidth=0.5)

    ax5.set_ylabel("NFC_new/dHz")
    ax5.set_title("Net Frequency Change Filtered")
    ax5.grid(True, which='major', axis='both',linestyle='--', color='gray', linewidth=0.5)

    ax3.set_ylabel("ice intensity/(mm/1min)")
    ax3.set_title("Instantaneous ice accretion ")
    ax3.grid(True, which='major', axis='both',linestyle='--', color='gray', linewidth=0.5)

    # ax4.set_xlabel("Kellonaika")
    ax1.set_ylabel("ice accumulation/mm")
    ax1.set_title("Ice Accumulation ")
    ax1.grid(True, which='major', axis='both',linestyle='--', color='gray', linewidth=0.5)

    # Yhteneväiset aika-akselit
    axes = [ax1, ax2, ax3, ax4, ax5]
    for ax in axes:
        ax.set_xlim(pd.Timestamp(f'{starttime}'), pd.Timestamp(f'{endtime}'))

        # Päämerkinnät (major ticks) joka 3. tunti
        # ax.xaxis.set_major_locator(mdates.HourLocator(interval=3))
        if duration <= timedelta(days=3):
            ax.xaxis.set_major_locator(mdates.HourLocator(byhour=range(0, 24, 3)))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

            # Väli-merkinnät (minor ticks) joka tunti tai muuten erilainen
            ax.xaxis.set_minor_locator(mdates.HourLocator(interval=1))
            plt.xlabel("Kellonaika")
        elif duration <= timedelta(days=8):
            ax.xaxis.set_major_locator(mdates.HourLocator(byhour=range(0, 24, 6)))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

            # Väli-merkinnät (minor ticks) joka tunti
            ax.xaxis.set_minor_locator(mdates.HourLocator(interval=3))
            plt.xlabel("Kellonaika")
        else:
            ax.xaxis.set_major_locator(mdates.HourLocator(byhour=range(0, 24, 24)))
            # ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d'))

            # Väli-merkinnät (minor ticks) joka tunti
            ax.xaxis.set_minor_locator(mdates.HourLocator(interval=12))
            plt.xlabel("Päivän numero")


        # Pystyviivat: major ja minor
        ax.grid(which='major', linestyle='-', linewidth=0.8, color='gray')       # vahvemmat viivat
        ax.grid(which='minor', linestyle='--', linewidth=0.5, color='lightgray') # kevyet viivat
        ax.legend()

    # plt.xlabel("Kellonaika")
    if sensor_id is not None:
        plt.suptitle(f"{place}#{sensor_id}: {fmisid}: {starttime}-{endtime} UTC")
    else:
        plt.suptitle(f"{place}: {fmisid}: {starttime}-{endtime} UTC")
    
    plt.tight_layout(rect=[0, 0, 1, 0.98])  # jätetään tilaa otsikolle
    # st.pyplot(fig)
    return fig

def plot_parameter(df: pd.DataFrame, parameter: str, start_datetime: datetime, end_datetime:datetime) -> go.Figure:
    fig = px.line(df, x=df.index, y=parameter, \
        title=f'{df["stationname"].iloc[0]} {start_datetime.date()} - {end_datetime.date()}'        
        )
    return fig

