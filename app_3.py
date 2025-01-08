import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import plotly.graph_objects as go
from prophet import Prophet
from prophet.plot import plot_plotly, plot_components_plotly
import re

st.title("鋼材価格予測アプリ")

# 鋼材の種類と対応するURL、テーブルクラスの辞書
steel_types = {
    "厚板　【19×5×10】": "https://www.japanmetal.com/memberwel/marketprice/soba_atsuita",
    "熱延鋼板　【1.6mm】": "https://www.japanmetal.com/memberwel/marketprice/soba_netsuusu",
    "冷延鋼板　【1.0mm】": "https://www.japanmetal.com/memberwel/marketprice/soba_reiusu",
    "等辺山形鋼　【6×50】": "https://www.japanmetal.com/memberwel/marketprice/soba_tohenyama"
}

# データ取得関数
def scrape_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        table = soup.find("table", class_="datbl")
        if not table:
            st.error("テーブルが見つかりませんでした。")
            return pd.DataFrame()

        data = []
        rows = table.find_all("tr")[2:]
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 2:
                date_str = cols[0].text.strip()
                price_str = cols[1].text.strip()

                price_str = re.sub(r'[^\d]', '', price_str)

                if price_str:
                    try:
                        price = int(price_str)
                        data.append([date_str, price])
                    except ValueError:
                        st.warning(f"数値変換エラー: {price_str} (元の文字列: {cols[1].text.strip()})")
                        continue
                else:
                    st.warning(f"空の価格データ: (元の文字列: {cols[1].text.strip()})")
                    continue

        df = pd.DataFrame(data, columns=["年月", "月初値"])
        df['年月'] = pd.to_datetime(df['年月'], format='%Y年%m月', errors='coerce')
        df = df.dropna(subset=['年月', '月初値'])
        return df

    except requests.exceptions.RequestException as e:
        st.error(f"Webサイトへのアクセスエラー: {e}")
        return pd.DataFrame()

# 鋼材種類の選択（マルチセレクト）
selected_steel_types = st.multiselect("鋼材の種類", list(steel_types.keys()))

# 季節性の選択
seasonality_option = st.selectbox("季節性の選択", ["季節性考慮（12ヶ月毎）", "季節性未考慮"])

# キャッシュを利用してデータ取得を高速化
@st.cache_data
def cached_scrape_data(url):
    return scrape_data(url)

# データ取得と予測を一度に行うボタン
if st.button("最新データを取得し予測"):
    for steel_type in selected_steel_types:
        url = steel_types[steel_type]
        df = cached_scrape_data(url)
        if not df.empty:
            df = df.sort_values('年月')
            st.write(f"{steel_type}のデータ取得成功")

            # 取得結果のグラフ表示
            st.subheader(f"{steel_type}の取得結果のグラフ")
            fig = go.Figure(data=[go.Scatter(x=df['年月'], y=df['月初値'], mode='lines+markers')])
            fig.update_layout(title=f"{steel_type}の鋼材価格推移", xaxis_title="年月", yaxis_title="月初値 (円/ton)")
            st.plotly_chart(fig)

            # 予測処理
            try:
                df_prophet = df.rename(columns={'年月': 'ds', '月初値': 'y'})
                model = Prophet(yearly_seasonality=(seasonality_option == "季節性考慮（12ヶ月毎）"))
                model.fit(df_prophet)

                # 予測期間の設定
                periods = 12 if seasonality_option == "季節性考慮（12ヶ月毎）" else 24
                future = model.make_future_dataframe(periods=periods, freq='MS')
                forecast = model.predict(future)

                # 予測結果のグラフ表示
                st.subheader(f"{steel_type}の予測結果のグラフ")
                fig_forecast = plot_plotly(model, forecast)
                fig_forecast.update_layout(title=f"{steel_type}の鋼材価格予測", xaxis_title="年月", yaxis_title="月初値 (円/ton)")
                st.plotly_chart(fig_forecast)

                fig_components = plot_components_plotly(model, forecast)
                st.plotly_chart(fig_components)

            except Exception as e:
                st.error(f"{steel_type}の予測中にエラーが発生しました: {e}")

        else:
            st.write(f"{steel_type}のデータの取得に失敗しました。")
