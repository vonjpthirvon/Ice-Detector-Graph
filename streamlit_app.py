import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from io import StringIO
import chardet
from datetime import datetime, time, timedelta, date
from dateutil.relativedelta import relativedelta
# from data_fetchers import fetch_icedata
# from plotters import plot_icegraph, plot_parameter
from icing_utils.data_fetchers import fetch_icedata
from icing_utils.plotters import plot_icegraph, plot_parameter

## PÄÄOHJELMA ALKAA ###
# Käyttöliittymä
def main():
    st.title("Ice Detector Graph")
    st.set_page_config(page_title="Ice Detector Graph", layout="centered")
    places = {
        "Vantaa": 100968, "Turku": 101065, "Maarianhamina": 100907,
        "Pori": 101044, "Tampere": 101118, "Halli": 101315,"Tikkakoski": 137208,
        "Seinäjoki": 137188,"Vaasa": 101462,"Kruunupyy": 101662,"Siilinjärvi": 101570,
        "Joensuu": 101608,"Utti": 101191,"Lappeenranta": 101237,"Savonlinna": 101430,
        "Mikkeli": 855522,"Kajaani": 101725,"Oulu": 101786,"Kemi": 101840,"Kuusamo": 101886,
        "Rovaniemi": 137190,"Ivalo": 102033,"Kittilä": 101986
    }

    places = dict(sorted(places.items()))

    # Näytetään valintaruutu käyttäjälle
    place = st.selectbox("Place:", list(places.keys()))
    # print(place)

    # Haetaan FMISID käyttäjän valitseman paikan mukaan
    FMISID = places[place]
    sensor_id = None
    if place in ["Vantaa"]:
        sensor_id = st.selectbox("Valitse anturi:", [10, 37])
    # print(f"{FMISID}, {sensor_id}")

    # Päivämäärän ja kellonajan valinta
    # Käyttäjän syöte: aikaväli
    
    today = date.today()
    tomorrow = today + timedelta(days=1)

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date:", value = today)
        end_date = st.date_input("End Date:", value = tomorrow)
    with col2:
        start_time = st.time_input("Start Time:", value=time(0, 0))
        end_time = st.time_input("End Time:", value=time(0, 0))

    #Yhdistä päivämäärä ja kellonaika
    start_datetime = datetime.combine(start_date, start_time)
    end_datetime = datetime.combine(end_date, end_time)

    # Muunna tekstiksi
    starttime = start_datetime.strftime("%Y%m%dT%H%M")
    endtime   = end_datetime.strftime("%Y%m%dT%H%M")

    duration = end_datetime - start_datetime

    if start_datetime >= end_datetime:
        st.error("Start Time must be before End Time. Adjust dates and times.")
        return

    if end_datetime > start_datetime + relativedelta(months=1):
        st.error("Too long period (max 1 month). Adjust dates and times.")
        return

    # Datan haku napin painalluksella
    if st.button("Show Graph"):
        try:
            with st.spinner("Fetching data..."):
                if place in ["Vantaa"]:
                    # df = fetch_icedata_vantaa(place, starttime, endtime)
                    df = fetch_icedata(FMISID, starttime, endtime, place, sensor_id)
                else:
                    df = fetch_icedata(FMISID, starttime, endtime, place)

                if df is None or df.empty:
                    st.warning("No data found for selected time range.")
                    return
                else:
                    # print(f"Data retrieval succesfull...")
                    # print(f"Start: {df.index[0]},End: {df.index[-1]}, Location: {place}")
                    st.info(f"Data retrieval succesfull...")
                    st.info(f"Start: {df.index[0]},End: {df.index[-1]}, Location: {place}")

                st.session_state.df = df  # tallennetaan istuntotilaan
            # print(f"{df[0]},{df[-1]},{place},{starttime},{endtime}")

            with st.spinner("Plotting data..."):
                if place in ["Vantaa"]:
                    # print("Vantaa")
                    fig = plot_icegraph(df, place, FMISID, start_datetime, end_datetime, sensor_id)
                else:
                    # print("Muu paikka")
                    fig = plot_icegraph(df, place, FMISID, start_datetime, end_datetime)
                st.pyplot(fig)

        except Exception as e:
            st.error(f"Error occurred: {e}")

    # # Interaktiivinen kuvaajien valinta
    # df = st.session_state.get("df", None)
    # if df is not None:
    #     st.subheader("Interactive plotting")
    #     available_variables = df.select_dtypes(include=[np.number]).columns.tolist()
    #     selected_variables = st.multiselect("Valitse muuttujat:", available_variables, default=available_variables[-1])

    #     for param in selected_variables:
    #         fig = plot_parameter(df, param, start_datetime, end_datetime)
    #         # st.plotly_chart(fig, use_container_width=True)
    #         st.plotly_chart(fig, width='stretch')

if __name__ == "__main__":
    main()
