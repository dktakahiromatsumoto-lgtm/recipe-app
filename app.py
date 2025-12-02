import streamlit as st
import pandas as pd
import random

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
    recipe_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQN7zOdMeK_lRCOzG8coIdHkdawIbSvlLyhU5KpEHAbca75YCCT1gBwB85K2ah5gcr6Yd3rPessbNWN/pub?gid=0&single=true&output=csv"
    
    # 2. 食材マスタのCSV URL
    ingredient_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQN7zOdMeK_lRCOzG8coIdHkdawIbSvlLyhU5KpEHAbca75YCCT1gBwB85K2ah5gcr6Yd3rPessbNWN/pub?gid=805502789&single=true&output=csv"
    
    # ==========================================

    # ★ GoogleドライブのURLを画像用に変換する魔法の関数
    def convert_google_drive_url(url):
        url = str(url).strip()
        if "drive.google.com" in url and "/d/" in url:
            # ID部分を抜き出して、直リンク形式に書き換える
            file_id = url.split("/d/")[1].split("/")[0]
            return f"https://drive.google.com/uc?export=view&id={file_id}"
        return url

    # ① レシピデータの読み込み
    try:
        df_recipe = pd.read_csv(recipe_csv)
        df_recipe["ingredients"] = df_recipe["ingredients"].apply(lambda x: str(x).split("、") if pd.notnull(x) else [])
        if "target_stores" not in df_recipe.columns:
            df_recipe["target_stores"] = "共通"
        
        # GoogleドライブのURLがあれば変換する
        if "image" in df_recipe.columns:
            df_recipe["image"] = df_recipe["image"].apply(convert_google_drive_url)

        df_recipe = df_recipe.fillna("")
    except Exception:
        df_recipe = pd.DataFrame()

    # ② 食材データの読み込み
    try:
        df_ing = pd.read_csv(ingredient_csv)
        df_ing = df_ing.fillna("-")
        if "商品名" in df_ing.columns:
            df_ing["商品名"] = df_ing["商品名"].astype(str).str.strip()
            ing_dict = df_ing.set_index("商品名").to_dict(orient="index")
        else:
            ing_dict = {}
    except Exception:
        ing_dict = {}

    return df_recipe, ing_dict

df, ingredient_dict = load_data()

# ==========================================
# 📱 サイドバー（モード選択・フィルター）
# ==========================================
st.sidebar.title("🍳 Menu")
mode = st.sidebar.radio("モード選択", ["🔍 レシピ検索", "🎓 レシピ検定"])
st.sidebar.divider()

# --- モード1：レシピ検索 ---
if mode == "🔍 レシピ検索":
    st.sidebar.subheader("絞り込み設定")

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

    search_query = st.sidebar.text_input("キーワード検索", placeholder="例: ポテト, 鶏肉...")

    if not df.empty and "category" in df.columns:
        categories = ["すべて"] + list(df["category"].unique())
        selected_category = st.sidebar.selectbox("カテゴリで絞り込み", categories)
    else:
        selected_category = "すべて"

    if not df.empty:
        filtered_df = df.copy()

        if selected_store != "すべて":
            filtered_df = filtered_df[filtered_df["target_stores"].astype(str).apply(lambda x: selected_store in x)]
        if search_query:
            filtered_df = filtered_df[
                filtered_df["title"].str.contains(search_query, case=False) |
                filtered_df["ingredients"].apply(lambda x: search_query in str(x))
            ]
        if selected_category != "すべて":
            filtered_df = filtered_df[filtered_df["category"] == selected_category]

        st.title("🔍 Recipe Search")
        st.write(f"検索結果: {len(filtered_df)} 件")

        if filtered_df.empty:
            st.info("条件に一致するレシピが見つかりませんでした。")
        else:
            cols = st.columns(3)
            for index, (i, row) in enumerate(filtered_df.iterrows()):
                col = cols[index % 3]
                with col:
                    with st.container(border=True):
                        # 画像表示（Googleドライブ対応）
                        if row["image"] and str(row["image"]).startswith("http"):
                            st.image(row["image"], use_container_width=True)
                        
                        st.subheader(row["title"])
                        st.caption(f"🏢 {row['target_stores']} | 📂 {row['category']}")
                        st.text(f"⏱ {row['time']}")
                        
                        with st.expander("詳細を見る"):
                            st.markdown("**🛒 材料**")
                            ingredients_list = row["ingredients"]
                            for ingredient_name in ingredients_list:
                                ingredient_name = str(ingredient_name).strip()
                                matched_info = None
                                if ingredient_name in ingredient_dict:
                                    matched_info = ingredient_dict[ingredient_name]
                                else:
                                    for master_name, info in ingredient_dict.items():
                                        if ingredient_name in master_name:
                                            matched_info = info
                                            break
                                if matched_info:
                                    with st.popover(f"ℹ️ {ingredient_name}"):
                                        st.markdown(f"### {matched_info.get('商品名', ingredient_name)}")
                                        st.caption(f"コード: {matched_info.get('商品コード', '-')}")
                                        st.markdown(f"**賞味期限**: {matched_info.get('賞味期限', '-')}")
                                        st.markdown(f"**保管温度**: {matched_info.get('納品温度帯(保管温度帯)', '-')}")
                                        st.markdown(f"**備考**: {matched_info.get('備考', '-')}")
                                else:
                                    st.write(f"・ {ingredient_name}")

                            st.markdown("---")
                            st.markdown("**📝 作り方**")
                            st.write(row["steps"])
    else:
        st.error("データの読み込みに失敗しました。")

# --- モード2：レシピ検定クイズ ---
elif mode == "🎓 レシピ検定":
    st.title("🎓 実力診断！レシピ検定")
    st.caption("ランダムに出題されるメニューの名前を答えよう！")

    if df.empty:
        st.error("データがありません。")
    elif len(df) < 4:
        st.warning("クイズをするには、少なくとも4つ以上のレシピが必要です。")
    else:
        if 'quiz_state' not in st.session_state:
            st.session_state.quiz_state = "start"
        if 'current_quiz' not in st.session_state:
            st.session_state.current_quiz = None

        def generate_quiz():
            correct_row = df.sample(1).iloc[0]
            wrong_titles = df[df["title"] != correct_row["title"]]["title"].sample(3).tolist()
            options = wrong_titles + [correct_row["title"]]
            random.shuffle(options)
            st.session_state.current_quiz = {
                "data": correct_row,
                "options": options,
                "correct_answer": correct_row["title"]
            }
            st.session_state.quiz_state = "answering"

        col1, col2 = st.columns([2, 1])
        with col2:
            st.write("")
            if st.button("🔄 次の問題へ / スタート", type="primary", use_container_width=True):
                generate_quiz()
                st.rerun()

        if st.session_state.quiz_state == "answering" and st.session_state.current_quiz:
            q = st.session_state.current_quiz
            row = q["data"]
            with col1:
                st.markdown("### Q. この料理の名前は？")
                if row["image"] and str(row["image"]).startswith("http"):
                    st.image(row["image"], width=400)
                else:
                    st.info("📷 画像がありません")
                    st.markdown("**ヒント：使われている材料**")
                    st.write(" / ".join(row["ingredients"]))
                
                st.write("")
                user_answer = st.radio("正解を選んでください:", q["options"], key="quiz_radio")
                
                if st.button("回答する"):
                    if user_answer == q["correct_answer"]:
                        st.balloons()
                        st.success(f"🎉 正解！これは「{q['correct_answer']}」です！")
                    else:
                        st.error(f"残念... 😢 正解は「{q['correct_answer']}」でした。")
        elif st.session_state.quiz_state == "start":
            st.info("右上の「スタート」ボタンを押して検定を開始してください！")
