import streamlit as st
import pandas as pd

# ページ設定
st.set_page_config(page_title="Recipe Viewer", layout="wide")

# --- パスワード認証機能 ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    password = st.text_input("パスワードを入力してください", type="password")
    if password == "5312":
        st.session_state.logged_in = True
        st.rerun()
    else:
        st.info("パスワードを入力するとレシピが表示されます。")
        st.stop()

# --- データを読み込む機能 ---
@st.cache_data(ttl=60)
def load_data():
    # ==========================================
    # 👇 ここにURLを2つ貼ってください（必須！）
    # ==========================================
    
    # 1. レシピのCSV URL
    recipe_csv = "https://docs.google.com/spreadsheets/d/1X7ORyihc-4p5DxOEZvYps26R7nVavdy_FeqBlD0z6tQ/edit?gid=0#gid=0"
    
    # 2. 食材マスタのCSV URL
    ingredient_csv = "https://docs.google.com/spreadsheets/d/1X7ORyihc-4p5DxOEZvYps26R7nVavdy_FeqBlD0z6tQ/edit?gid=805502789#gid=805502789"
    
    # ==========================================

    # ① レシピデータの読み込み
    try:
        df_recipe = pd.read_csv(recipe_csv)
        # データの掃除（空白除去など）
        df_recipe["ingredients"] = df_recipe["ingredients"].apply(lambda x: str(x).split("、") if pd.notnull(x) else [])
        if "target_stores" not in df_recipe.columns:
            df_recipe["target_stores"] = "共通"
        df_recipe = df_recipe.fillna("")
    except Exception:
        df_recipe = pd.DataFrame()

    # ② 食材データの読み込み
    try:
        df_ing = pd.read_csv(ingredient_csv)
        df_ing = df_ing.fillna("-")
        
        # 検索用の辞書を作成（商品名がキー）
        # ※ここでのポイント：検索ミスを防ぐため、文字列型にして前後の空白を削除
        if "商品名" in df_ing.columns:
            df_ing["商品名"] = df_ing["商品名"].astype(str).str.strip()
            ing_dict = df_ing.set_index("商品名").to_dict(orient="index")
        else:
            ing_dict = {}
            
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
                        
                        ingredients_list = row["ingredients"]
                        
                        for ingredient_name in ingredients_list:
                            ingredient_name = str(ingredient_name).strip() # 空白削除
                            
                            # --- あいまい検索ロジック ---
                            matched_info = None
                            
                            # 1. 完全一致
                            if ingredient_name in ingredient_dict:
                                matched_info = ingredient_dict[ingredient_name]
                            else:
                                # 2. 部分一致（マスタ名の中にレシピ材料名が含まれるか）
                                for master_name, info in ingredient_dict.items():
                                    if ingredient_name in master_name:
                                        matched_info = info
                                        break
                            # -------------------------

                            if matched_info:
                                with st.popover(f"ℹ️ {ingredient_name}"):
                                    st.markdown(f"### {matched_info.get('商品名', ingredient_name)}")
                                    st.caption(f"商品コード: {matched_info.get('商品コード', '-')}")
                                    
                                    st.markdown("#### 📦 管理情報")
                                    st.markdown(f"""
                                    | 項目 | 内容 |
                                    | :--- | :--- |
                                    | **賞味期限** | {matched_info.get('賞味期限', '-')} |
                                    | **開封後期限** | {matched_info.get('開封後賞味期限目安', '-')} |
                                    | **保管温度** | {matched_info.get('納品温度帯(保管温度帯)', '-')} |
                                    | **開封後温度** | {matched_info.get('開封後温度帯', '-')} |
                                    """)
                                    
                                    st.markdown("#### 🏢 仕入・規格")
                                    st.write(f"メーカー: {matched_info.get('メーカー名', '-')}")
                                    st.write(f"規格: {matched_info.get('規格', '-')}")
                                    st.write(f"備考: {matched_info.get('備考', '-')}")
                            else:
                                st.write(f"・ {ingredient_name}")

                        st.markdown("---")
                        st.markdown("**📝 作り方**")
                        st.write(row["steps"])

    # --- 🔧 診断ツール（ここから下が表示されない原因を探るツールです） ---
    st.divider()
    with st.expander("🔧 管理者用：データ診断モード"):
        st.write("### 1. 食材マスタの状態")
        if ingredient_dict:
            st.success(f"✅ 読み込み成功！ {len(ingredient_dict)} 件の食材があります。")
            st.write("▼ 読み込んだデータの一部")
            st.dataframe(pd.DataFrame.from_dict(ingredient_dict, orient='index').head(5))
        else:
            st.error("❌ 食材マスタが読み込めませんでした。URLを確認してください。")

        st.write("### 2. マッチング テスト")
        test_word = st.text_input("レシピ側の材料名を入力してテスト", placeholder="例: 玉ねぎ")
        if test_word:
            found = False
            if test_word in ingredient_dict:
                st.success(f"✅ 完全一致でヒット！: {test_word}")
                found = True
            else:
                for master_name in ingredient_dict.keys():
                    if test_word in master_name:
                        st.info(f"🆗 部分一致でヒット！: {test_word} ⊂ {master_name}")
                        found = True
                        break
            if not found:
                st.error(f"⚠️ ヒットしませんでした。マスタにある名前: {list(ingredient_dict.keys())[:5]}...")

else:
    st.error("データの読み込みに失敗しました。URLを確認してください。")
