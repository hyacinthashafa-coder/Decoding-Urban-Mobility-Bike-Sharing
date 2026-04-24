import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import zipfile
import requests
from io import BytesIO

# 1. KONFIGURASI HALAMAN
st.set_page_config(
    page_title="Bike Sharing Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)
sns.set_style("whitegrid")

# 2. LOAD DATASET
@st.cache_data
def load_data():
    main_data = pd.read_csv("dashboard/main_data.csv")
    main_data["dteday"] = pd.to_datetime(main_data["dteday"])
    
    # Tambahkan tipe hari
    main_data['day_type'] = main_data['weekday'].apply(
        lambda x: 'Weekend' if x == 0 or x == 6 else 'Weekday'
    )
    
    return main_data

main_data = load_data()

# 3. SIDEBAR FILTER
st.sidebar.title("Filter Eksplorasi")

start_date, end_date = st.sidebar.date_input(
    "Rentang Waktu",
    [main_data['dteday'].min(), main_data['dteday'].max()]
)

season = st.sidebar.multiselect(
    "Pilih Musim",
    options=main_data["season"].unique(),
    default=main_data["season"].unique()
)

day_type_filter = st.sidebar.multiselect(
    "Tipe Hari",
    options=["Weekday", "Weekend"],
    default=["Weekday", "Weekend"]
)

hour_range = st.sidebar.slider("Rentang Jam", 0, 23, (0, 23))

# 4. FILTERING LOGIC
filtered_data = main_data[
    (main_data['dteday'] >= pd.to_datetime(start_date)) &
    (main_data['dteday'] <= pd.to_datetime(end_date)) &
    (main_data['season'].isin(season)) &
    (main_data['day_type'].isin(day_type_filter)) &
    (main_data['hr'] >= hour_range[0]) &
    (main_data['hr'] <= hour_range[1])
]

# 5. KPI METRICS
st.title("🚴 Bike Sharing Dashboard 🚴")
st.markdown("Dashboard untuk menganalisis pola perilaku penyewaan sepeda.")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Penyewaan", f"{filtered_data['cnt'].sum():,.0f}")
c2.metric("Rata-rata/Jam", f"{filtered_data['cnt'].mean():.2f}")
c3.metric("User Casual", f"{filtered_data['casual'].sum():,.0f}")
c4.metric("User Registered", f"{filtered_data['registered'].sum():,.0f}")

st.markdown("---")

# 6. MAIN TREND & HEATMAP
st.subheader("Tren Penyewaan Harian")
trend = filtered_data.groupby("dteday")["cnt"].sum()
fig, ax = plt.subplots(figsize=(12, 4))
ax.plot(trend, color="#72BCD4", linewidth=2)
st.pyplot(fig)

st.write("---")
st.subheader("Heatmap Kepadatan Jam dan Hari")

weekday_map = {0: "Minggu", 1: "Senin", 2: "Selasa", 3: "Rabu", 4: "Kamis", 5: "Jumat", 6: "Sabtu"}
day_order = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]

heatmap_data = filtered_data.copy()
heatmap_data['weekday_name'] = heatmap_data['weekday'].map(weekday_map)
heatmap_data['weekday_name'] = pd.Categorical(
    heatmap_data['weekday_name'], 
    categories=day_order, 
    ordered=True
)

pivot_table = heatmap_data.groupby(
    ['weekday_name', 'hr'], 
    observed=False
)['cnt'].mean().unstack()

fig, ax = plt.subplots(figsize=(15, 6))

sns.heatmap(
    pivot_table,
    cmap="YlGnBu",
    ax=ax
)

ax.set_xlabel("Jam")
ax.set_ylabel("Hari")
ax.set_title("Heatmap Penyewaan Sepeda Berdasarkan Hari dan Jam")

st.pyplot(fig)

# 7. FITUR SLIDER: DETAIL PER HARI
st.write("---")
st.subheader("🔍 Analisis Pola Penyewaan Harian")
st.info("Gunakan slider di bawah untuk melihat bagaimana pola jam berubah di setiap hari.")

selected_day = st.select_slider(
    "Pilih Hari Spesifik:",
    options=["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
)

day_to_num = {"Minggu": 0, "Senin": 1, "Selasa": 2, "Rabu": 3, "Kamis": 4, "Jumat": 5, "Sabtu": 6}
specific_day_df = filtered_data[filtered_data['weekday'] == day_to_num[selected_day]].copy()
specific_day_df = specific_day_df.rename(columns={"hr": "Jam"})

col_l, col_r = st.columns(2)

with col_l:
    st.markdown(f"**Rata-rata Penyewaan per Jam ({selected_day})**")
    if not specific_day_df.empty:
        hourly_plot = specific_day_df.groupby("Jam")["cnt"].mean()
        fig, ax = plt.subplots()
        sns.lineplot(x=hourly_plot.index, y=hourly_plot.values, marker="o", color="#1f77b4")
        ax.set_xlabel("Jam")
        ax.set_ylabel("Rata-rata Penyewaan")
        st.pyplot(fig)

with col_r:
    st.markdown(f"**Casual vs Registered ({selected_day})**")
    if not specific_day_df.empty:
        user_plot = specific_day_df.groupby("Jam")[["casual","registered"]].mean()
        fig, ax = plt.subplots()
        sns.lineplot(data=user_plot["casual"], label="Casual", marker="o")
        sns.lineplot(data=user_plot["registered"], label="Registered", marker="o")
        ax.set_xlabel("Jam")
        ax.set_ylabel("Rata-rata Penyewaan")
        st.pyplot(fig)

# 8. WEATHER & SEASON ANALYSIS
st.write("---")
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Analisis Berdasarkan Hari")

    day_stats = filtered_data.groupby("weekday")["cnt"].mean().reset_index()
    day_stats["weekday"] = day_stats["weekday"].map(weekday_map)
    day_stats = day_stats.sort_values("cnt", ascending=True)

    colors = ["#72BCD4"] * len(day_stats)
    colors[-1] = "#FFD700"  # highlight tertinggi (kuning)

    fig, ax = plt.subplots(figsize=(6,4))
    ax.barh(day_stats["weekday"], day_stats["cnt"], color=colors)

    ax.set_xlabel("Rata-rata Penyewaan")
    ax.set_ylabel("Hari")
    ax.set_title("Rata-rata Penyewaan Sepeda per Hari")

    st.pyplot(fig)

with col_b:
    st.subheader("Analisis Berdasarkan Cuaca")

    weather_stats = filtered_data.groupby("weathersit")["cnt"].mean().reset_index()
    weather_stats = weather_stats.sort_values("cnt", ascending=True)

    colors = ["#72BCD4"] * len(weather_stats)
    colors[-1] = "#FFD700"  # highlight tertinggi (kuning)

    fig, ax = plt.subplots(figsize=(6,4))
    ax.barh(weather_stats["weathersit"].astype(str), weather_stats["cnt"], color=colors)

    ax.set_xlabel("Rata-rata Penyewaan")
    ax.set_ylabel("Kondisi Cuaca")
    ax.set_title("Pengaruh Kondisi Cuaca terhadap Penyewaan")

    st.pyplot(fig)
