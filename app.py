import streamlit as st
import pandas as pd

# ページ設定
st.set_page_config(page_title="Recipe Viewer", layout="wide")
# --- 変更箇所：ログインしたら入力欄を消す設定 ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    password = st.text_input("パスワードを入力してください", type="password")
    if password == "5312": # パスワード
        st.session_state.logged_in = True
        st.rerun()
    else:
        st.info("パスワードを入力するとレシピが表示されます。")
        st.stop()
# --------------------------------------------------
# --------------------------
# --- 1. データ準備（事前にアップロードされたレシピを想定） ---
# 実際にはCSVやデータベースから読み込みますが、ここではデモデータを定義します
# --- 変更箇所ここから ---
def load_data():
    # Excelファイルを読み込む
    try:
        df = pd.read_excel("recipes.xlsx")
        
        # 「材料」がExcelだと文字(例: "肉、野菜")なので、リスト(例: ["肉", "野菜"])に変換する処理
        # ここでは読点「、」で区切る設定にしています
        df["ingredients"] = df["ingredients"].apply(lambda x: str(x).split("、") if pd.notnull(x) else [])
        
        # 欠損値（空欄）があれば埋める
        df = df.fillna("")
        return df
        
    except FileNotFoundError:
        st.error("エラー: 'recipes.xlsx' が見つかりません。デスクトップに保存しましたか？")
        return pd.DataFrame() # 空のデータを返す
# --- 変更箇所ここまで ---

df = load_data()

# --- 2. サイドバー（検索・フィルター） ---
st.sidebar.title("🔍 レシピ検索")

# キーワード検索
search_query = st.sidebar.text_input("キーワードを入力", placeholder="例: トマト, 鶏肉...")

# カテゴリフィルター
categories = ["すべて"] + list(df["category"].unique())
selected_category = st.sidebar.selectbox("カテゴリで絞り込み", categories)

# --- 3. データフィルタリング処理 ---
filtered_df = df.copy()

# キーワードで絞り込み（タイトル または 材料 に含まれるか）
if search_query:
    filtered_df = filtered_df[
        filtered_df["title"].str.contains(search_query, case=False) |
        filtered_df["ingredients"].apply(lambda x: search_query in str(x))
    ]

# カテゴリで絞り込み
if selected_category != "すべて":
    filtered_df = filtered_df[filtered_df["category"] == selected_category]

# --- 4. メイン画面（直感的なグリッド表示） ---
st.title("🍳 Recipe Viewer")
st.write(f"検索結果: {len(filtered_df)} 件")

if filtered_df.empty:
    st.info("条件に一致するレシピが見つかりませんでした。")
else:
    # 3列のカラムを作成してカード風に表示
    cols = st.columns(3)
    
    for index, (i, row) in enumerate(filtered_df.iterrows()):
        col = cols[index % 3] # カラムを循環させる
        
        with col:
            # カード風のコンテナ
            with st.container(border=True):
                # 画像表示（実際にはアップロードされた画像のパスを指定）
                st.image(row["image"], use_container_width=True)
                
                st.subheader(row["title"])
                st.caption(f"⏱ {row['time']} | 📂 {row['category']}")
                
                # 詳細を見るためのエキスパンダー
                with st.expander("詳細を見る"):
                    st.markdown("**🛒 材料**")
                    st.write(", ".join(row["ingredients"]))
                    
                    st.markdown("**📝 作り方**")
                    st.write(row["steps"])

# --- フッター ---
st.divider()
st.caption("Upload your recipes specifically tailored for intuitive browsing.")