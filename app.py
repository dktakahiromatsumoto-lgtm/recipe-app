import streamlit as st
import pandas as pd

# ページ設定
st.set_page_config(page_title="Recipe Viewer", layout="wide")

# --- パスワード認証機能 ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    password = st.text_input("パスワードを入力してください", type="password")
    if password == "5312":  # パスワード設定
        st.session_state.logged_in = True
        st.rerun()
    else:
        st.info("パスワードを入力するとレシピが表示されます。")
        st.stop()

# --- データを読み込む機能（スプレッドシート対応版） ---
@st.cache_data(ttl=60)
def load_data():
    # ↓↓↓ ここにスプレッドシートの「CSV形式のURL」を貼ってください！ ↓↓↓
    csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQN7zOdMeK_lRCOzG8coIdHkdawIbSvlLyhU5KpEHAbca75YCCT1gBwB85K2ah5gcr6Yd3rPessbNWN/pubhtml"
    # ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑

    try:
        df = pd.read_csv(csv_url)
        # データの整理
        df["ingredients"] = df["ingredients"].apply(lambda x: str(x).split("、") if pd.notnull(x) else [])
        df = df.fillna("")
        return df
    except Exception as e:
        # URLが空だったり間違っている場合のエラー対策
        return pd.DataFrame()

df = load_data()

# --- サイドバー（検索・フィルター） ---
st.sidebar.title("🔍 レシピ検索")

# キーワード検索
search_query = st.sidebar.text_input("キーワードを入力", placeholder="例: トマト, 鶏肉...")

# カテゴリフィルター
if not df.empty:
    categories = ["すべて"] + list(df["category"].unique())
    selected_category = st.sidebar.selectbox("カテゴリで絞り込み", categories)
else:
    selected_category = "すべて"

# --- データフィルタリング処理 ---
if not df.empty:
    filtered_df = df.copy()

    # キーワードで絞り込み
    if search_query:
        filtered_df = filtered_df[
            filtered_df["title"].str.contains(search_query, case=False) |
            filtered_df["ingredients"].apply(lambda x: search_query in str(x))
        ]

    # カテゴリで絞り込み
    if selected_category != "すべて":
        filtered_df = filtered_df[filtered_df["category"] == selected_category]

    # --- メイン画面（グリッド表示） ---
    st.title("🍳 Recipe Viewer")
    st.write(f"検索結果: {len(filtered_df)} 件")

    if filtered_df.empty:
        st.info("条件に一致するレシピが見つかりませんでした。")
    else:
        cols = st.columns(3)
        for index, (i, row) in enumerate(filtered_df.iterrows()):
            col = cols[index % 3]
            with col:
                with st.container(border=True):
                    # 画像があれば表示
                    if row["image"] and str(row["image"]).startswith("http"):
                        st.image(row["image"], use_container_width=True)
                    
                    st.subheader(row["title"])
                    st.caption(f"⏱ {row['time']} | 📂 {row['category']}")
                    
                    with st.expander("詳細を見る"):
                        st.markdown("**🛒 材料**")
                        st.write(", ".join(row["ingredients"]))
                        st.markdown("**📝 作り方**")
                        st.write(row["steps"])
else:
    st.error("データの読み込みに失敗しました。URLを確認してください。")

# --- フッター ---
st.divider()
st.caption("Recipe App powered by Streamlit")
