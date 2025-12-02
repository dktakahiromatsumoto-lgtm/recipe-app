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

# --- データを読み込む機能（2つのシートを読み込む） ---
@st.cache_data(ttl=60)
def load_data():
    # ---------------------------------------------------------
    # 👇 ここにURLを2つ貼ってください！
    # ---------------------------------------------------------
    
    # 1. レシピのCSV URL
    recipe_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQN7zOdMeK_lRCOzG8coIdHkdawIbSvlLyhU5KpEHAbca75YCCT1gBwB85K2ah5gcr6Yd3rPessbNWN/pub?output=csv"
    
    # 2. 食材マスタのCSV URL（新しく作った方）
    ingredient_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQN7zOdMeK_lRCOzG8coIdHkdawIbSvlLyhU5KpEHAbca75YCCT1gBwB85K2ah5gcr6Yd3rPessbNWN/pub?output=csv"
    
    # ---------------------------------------------------------

    # ① レシピデータの読み込み
    try:
        df_recipe = pd.read_csv(recipe_csv)
        df_recipe["ingredients"] = df_recipe["ingredients"].apply(lambda x: str(x).split("、") if pd.notnull(x) else [])
        if "target_stores" not in df_recipe.columns:
            df_recipe["target_stores"] = "共通"
        df_recipe = df_recipe.fillna("")
    except Exception:
        df_recipe = pd.DataFrame()

    # ② 食材データの読み込み
    try:
        df_ing = pd.read_csv(ingredient_csv)
        df_ing = df_ing.fillna("-") # 空欄はハイフンにする
        # 検索しやすいように「商品名」をキーにした辞書に変換
        ing_dict = df_ing.set_index("商品名").to_dict(orient="index")
    except Exception:
        ing_dict = {}

    return df_recipe, ing_dict

df, ingredient_dict = load_data()

# --- サイドバー（検索・フィルター） ---
st.sidebar.title("🔍 レシピ検索")

# 1. 業態切り替え
st.sidebar.subheader("🏢 業態切り替え")
if not df.empty:
    all_stores = set()
    for stores in df["target_stores"]:
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

    # A. 業態で絞り込み
    if selected_store != "すべて":
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
                    st.caption(f"🏢 {row['target_stores']} | 📂 {row['category']}")
                    st.text(f"⏱ {row['time']}")
                    
                    with st.expander("詳細を見る"):
                        st.markdown("**🛒 材料 (タップで詳細)**")
                        
                        # 材料をボタン（ポップオーバー）として表示
                        # Streamlitの仕様上、ボタンを横に並べるためにcolumnsを使います
                        ingredients_list = row["ingredients"]
                        
                        # 材料ごとにボタンを作成
                        for ingredient_name in ingredients_list:
                            ingredient_name = ingredient_name.strip()
                            # マスタに情報があるか確認
                            if ingredient_name in ingredient_dict:
                                info = ingredient_dict[ingredient_name]
                                # ポップオーバー（吹き出し）を表示
                                with st.popover(f"ℹ️ {ingredient_name}"):
                                    st.markdown(f"### {ingredient_name}")
                                    st.caption(f"商品コード: {info.get('商品コード', '-')}")
                                    
                                    # 重要な情報を表形式で表示
                                    st.markdown("#### 📦 管理情報")
                                    st.markdown(f"""
                                    | 項目 | 内容 |
                                    | :--- | :--- |
                                    | **賞味期限** | {info.get('賞味期限', '-')} |
                                    | **開封後期限** | {info.get('開封後賞味期限目安', '-')} |
                                    | **保管温度** | {info.get('納品温度帯(保管温度帯)', '-')} |
                                    | **開封後温度** | {info.get('開封後温度帯', '-')} |
                                    """)
                                    
                                    st.markdown("#### 🏢 仕入・規格")
                                    st.write(f"メーカー: {info.get('メーカー名', '-')}")
                                    st.write(f"規格: {info.get('規格', '-')}")
                                    st.write(f"備考: {info.get('備考', '-')}")

                            else:
                                # 情報がない場合はただのテキストで表示
                                st.write(f"・ {ingredient_name}")

                        st.markdown("---")
                        st.markdown("**📝 作り方**")
                        st.write(row["steps"])
else:
    st.error("データの読み込みに失敗しました。2つのURLが正しいか確認してください。")
