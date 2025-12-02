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

# --- データを読み込む機能 ---
@st.cache_data(ttl=60)
def load_data():
    # ↓↓↓ ここにスプレッドシートのURLを貼ってください（必須！） ↓↓↓
    csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQN7zOdMeK_lRCOzG8coIdHkdawIbSvlLyhU5KpEHAbca75YCCT1gBwB85K2ah5gcr6Yd3rPessbNWN/pub?output=csv" 
    # ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑

    try:
        df = pd.read_csv(csv_url)
        
        # データの整理
        # 材料をリスト化
        df["ingredients"] = df["ingredients"].apply(lambda x: str(x).split("、") if pd.notnull(x) else [])
        # 業態（target_stores）がない場合は「共通」として扱う
        if "target_stores" not in df.columns:
            df["target_stores"] = "共通"
        
        df = df.fillna("")
        return df
    except Exception as e:
        return pd.DataFrame()

df = load_data()

# --- サイドバー（検索・フィルター） ---
st.sidebar.title("🔍 レシピ検索")

# 1. 業態切り替え（新機能！）
st.sidebar.subheader("🏢 業態切り替え")
# データに含まれる業態を自動で抽出してリストにする
if not df.empty:
    # 業態の候補を作成（重複をなくしてリスト化）
    all_stores = set()
    for stores in df["target_stores"]:
        # "ビッグエコー、カラオケマック"のように複数ある場合も考慮して分解
        for store in str(stores).split("、"):
            if store.strip():
                all_stores.add(store.strip())
    
    store_options = ["すべて"] + sorted(list(all_stores))
    selected_store = st.sidebar.selectbox("表示する業態を選択", store_options)
else:
    selected_store = "すべて"

st.sidebar.divider()

# 2. キーワード検索
search_query = st.sidebar.text_input("キーワード検索", placeholder="例: ポテト, 鶏肉...")

# 3. カテゴリフィルター
if not df.empty and "category" in df.columns:
    categories = ["すべて"] + list(df["category"].unique())
    selected_category = st.sidebar.selectbox("カテゴリで絞り込み", categories)
else:
    selected_category = "すべて"

# --- データフィルタリング処理 ---
if not df.empty:
    filtered_df = df.copy()

    # A. 業態で絞り込み（選択された業態が含まれているか）
    if selected_store != "すべて":
        # その文字が含まれている行だけを残す
        filtered_df = filtered_df[
            filtered_df["target_stores"].astype(str).apply(lambda x: selected_store in x)
        ]

    # B. キーワードで絞り込み
    if search_query:
        filtered_df = filtered_df[
            filtered_df["title"].str.contains(search_query, case=False) |
            filtered_df["ingredients"].apply(lambda x: search_query in str(x))
        ]

    # C. カテゴリで絞り込み
    if selected_category != "すべて":
        filtered_df = filtered_df[filtered_df["category"] == selected_category]

    # --- メイン画面表示 ---
    st.title("🍳 Recipe Viewer")
    
    # 選択中の業態を表示
    if selected_store != "すべて":
        st.caption(f"表示中: **{selected_store}** のメニュー")
    
    st.write(f"検索結果: {len(filtered_df)} 件")

    if filtered_df.empty:
        st.info("条件に一致するレシピが見つかりませんでした。")
    else:
        cols = st.columns(3)
        for index, (i, row) in enumerate(filtered_df.iterrows()):
            col = cols[index % 3]
            with col:
                with st.container(border=True):
                    if row["image"] and str(row["image"]).startswith("http"):
                        st.image(row["image"], use_container_width=True)
                    
                    st.subheader(row["title"])
                    # 業態タグも表示
                    st.caption(f"🏢 {row['target_stores']} | 📂 {row['category']}")
                    st.text(f"⏱ {row['time']}")
                    
                    with st.expander("詳細を見る"):
                        st.markdown("**🛒 材料**")
                        st.write(", ".join(row["ingredients"]))
                        st.markdown("**📝 作り方**")
                        st.write(row["steps"])
else:
    st.error("データの読み込みに失敗しました。URLを確認してください。")
