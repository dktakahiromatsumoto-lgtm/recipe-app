import streamlit as st
import pandas as pd
import random
import urllib.parse
from rapidfuzz import fuzz # 👈 これがあいまい検索の頭脳です

# ページ設定
st.set_page_config(page_title="Recipe Viewer", layout="wide")

# ==========================================
# 👇 設定エリア：URL設定
# ==========================================

# 1. レシピのCSV
recipe_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQN7zOdMeK_lRCOzG8coIdHkdawIbSvlLyhU5KpEHAbca75YCCT1gBwB85K2ah5gcr6Yd3rPessbNWN/pub?gid=0&single=true&output=csv"

# 2. 食材マスタのCSV
ingredient_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQN7zOdMeK_lRCOzG8coIdHkdawIbSvlLyhU5KpEHAbca75YCCT1gBwB85K2ah5gcr6Yd3rPessbNWN/pub?gid=805502789&single=true&output=csv"

# 3. お知らせのCSV
news_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQN7zOdMeK_lRCOzG8coIdHkdawIbSvlLyhU5KpEHAbca75YCCT1gBwB85K2ah5gcr6Yd3rPessbNWN/pub?gid=1725848377&single=true&output=csv"

# 4. 店舗マスタのCSV
store_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQN7zOdMeK_lRCOzG8coIdHkdawIbSvlLyhU5KpEHAbca75YCCT1gBwB85K2ah5gcr6Yd3rPessbNWN/pub?gid=285648220&single=true&output=csv"

# 5. Googleフォーム設定
form_base_url = "https://docs.google.com/forms/d/e/1FAIpQLSeLSyph6KJ3aPPgdCCxKuZ2tRLCZI13ftsM3-godUqzB1hOyg/viewform?usp=pp_url"
entry_id_store = "entry.1108417758"
entry_id_title = "entry.1493447951"

# ==========================================

# --- データ読み込み関数 ---
@st.cache_data(ttl=60)
def load_data():
    def convert_google_drive_url(url):
        url = str(url).strip()
        if "drive.google.com" in url and "/d/" in url:
            try:
                file_id = url.split("/d/")[1].split("/")[0]
                return f"https://drive.google.com/uc?export=view&id={file_id}"
            except IndexError:
                return url
        return url

    # ① レシピ
    try:
        df_recipe = pd.read_csv(recipe_csv)
        df_recipe["ingredients"] = df_recipe["ingredients"].apply(lambda x: str(x).split("、") if pd.notnull(x) else [])
        if "target_stores" not in df_recipe.columns:
            df_recipe["target_stores"] = "共通"
        if "image" in df_recipe.columns:
            df_recipe["image"] = df_recipe["image"].apply(convert_google_drive_url)
        df_recipe = df_recipe.fillna("")
    except:
        df_recipe = pd.DataFrame()

    # ② 食材マスタ
    try:
        df_ing = pd.read_csv(ingredient_csv)
        df_ing = df_ing.fillna("-")
        if "商品名" in df_ing.columns:
            df_ing["商品名"] = df_ing["商品名"].astype(str).str.strip()
            ing_dict = df_ing.set_index("商品名").to_dict(orient="index")
        else:
            ing_dict = {}
    except:
        ing_dict = {}

    # ③ お知らせ
    try:
        df_news = pd.read_csv(news_csv)
        df_news = df_news.fillna("")
    except:
        df_news = pd.DataFrame()

    # ④ 店舗マスタ
    try:
        df_stores = pd.read_csv(store_csv, dtype=str)
        df_stores = df_stores.fillna("")
        if "store_code" in df_stores.columns:
            df_stores["store_code"] = df_stores["store_code"].str.strip()
        if "password" in df_stores.columns:
            df_stores["password"] = df_stores["password"].str.strip()
    except:
        df_stores = pd.DataFrame()

    return df_recipe, ing_dict, df_news, df_stores

df, ingredient_dict, df_news, df_stores = load_data()


# --- ログイン機能 ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.store_name = ""

if not st.session_state.logged_in:
    st.markdown("### 🔑 Login")
    st.caption("店舗コードとパスワードを入力してください")
    input_code = st.text_input("店舗コード")
    input_password = st.text_input("パスワード", type="password")
    if st.button("ログイン"):
        if not df_stores.empty:
            match = df_stores[(df_stores["store_code"] == input_code) & (df_stores["password"] == input_password)]
            if not match.empty:
                st.session_state.logged_in = True
                st.session_state.store_name = match.iloc[0]["store_name"]
                st.rerun()
            else:
                st.error("店舗コードまたはパスワードが違います")
        else:
            if input_password == "5312":
                 st.session_state.logged_in = True
                 st.session_state.store_name = "管理者(緊急)"
                 st.rerun()
            else:
                 st.error("ログインできません")
    st.stop()

# --- レイアウト ---
st.sidebar.title(f"👤 {st.session_state.store_name}")
mode = st.sidebar.radio("メニュー", ["🏠 ホーム(お知らせ)", "🔍 レシピ検索", "🎓 レシピ検定"])
st.sidebar.divider()

# --- 🏠 ホーム ---
if mode == "🏠 ホーム(お知らせ)":
    st.title("📢 本部からのお知らせ")
    if df_news.empty:
        st.info("現在、お知らせはありません。")
    else:
        if "date" in df_news.columns:
            try:
                df_news["date"] = pd.to_datetime(df_news["date"], errors='coerce')
                df_news = df_news.sort_values("date", ascending=False)
            except: pass
        for index, row in df_news.iterrows():
            is_important = str(row.get("important", "")).upper() == "TRUE"
            with st.container(border=True):
                col1, col2 = st.columns([0.8, 0.2])
                with col1:
                    title_text = row.get('title', '無題')
                    if is_important: st.markdown(f"### 🔴 {title_text}")
                    else: st.markdown(f"### {title_text}")
                    if "date" in row and pd.notnull(row['date']):
                        try: st.caption(f"📅 {row['date'].strftime('%Y/%m/%d')}")
                        except: st.caption(f"📅 {row.get('date', '')}")
                    st.write(row.get('content', ''))
                with col2:
                    st.write("") 
                    store_encoded = urllib.parse.quote(str(st.session_state.store_name))
                    title_encoded = urllib.parse.quote(str(row.get('title', '')))
                    link = f"{form_base_url}&{entry_id_store}={store_encoded}&{entry_id_title}={title_encoded}"
                    st.link_button("✅ 既読", link)

# --- 🔍 レシピ検索（ファジー検索対応版） ---
elif mode == "🔍 レシピ検索":
    st.title("🔍 Recipe Search")
    st.caption("🗣️ 音声入力対応：キーボードのマイクボタンを押して話しかけてください")
    
    if not df.empty:
        all_stores = set()
        for stores in df["target_stores"]:
            for store in str(stores).split("、"):
                if store.strip(): all_stores.add(store.strip())
        store_options = ["すべて"] + sorted(list(all_stores))
        selected_store = st.sidebar.selectbox("業態絞り込み", store_options)
    else: selected_store = "すべて"
        
    search_query = st.sidebar.text_input("キーワード (音声入力OK)", placeholder="例: ハンバーグ、鶏肉...")
    
    if not df.empty and "category" in df.columns:
        categories = ["すべて"] + list(df["category"].unique())
        selected_category = st.sidebar.selectbox("カテゴリ", categories)
    else: selected_category = "すべて"

    # --- 検索ロジック ---
    if not df.empty:
        filtered_df = df.copy()
        
        # 1. 業態フィルター
        if selected_store != "すべて":
            filtered_df = filtered_df[filtered_df["target_stores"].astype(str).apply(lambda x: selected_store in x)]
        
        # 2. カテゴリフィルター
        if selected_category != "すべて":
            filtered_df = filtered_df[filtered_df["category"] == selected_category]

        # 3. キーワード検索（ファジー検索）
        if search_query:
            # 検索用のスコア計算関数
            def get_fuzzy_score(row):
                # タイトルとの類似度
                title_score = fuzz.partial_ratio(search_query.lower(), str(row['title']).lower())
                
                # 材料との類似度（リストを文字列にして検索）
                ingredients_str = " ".join(row['ingredients'])
                ing_score = fuzz.partial_ratio(search_query.lower(), ingredients_str.lower())
                
                # どちらか高い方を採用
                return max(title_score, ing_score)

            # スコアを計算して列に追加
            filtered_df['match_score'] = filtered_df.apply(get_fuzzy_score, axis=1)
            
            # スコアが50点以上のものだけ残す（この数字を下げるともっと緩くなります）
            filtered_df = filtered_df[filtered_df['match_score'] > 50]
            
            # スコアが高い順に並び替え
            filtered_df = filtered_df.sort_values('match_score', ascending=False)

        st.write(f"検索結果: {len(filtered_df)} 件")
        
        if filtered_df.empty:
            st.info("見つかりませんでした")
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
                        with st.expander("詳細"):
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
                                else:
                                    st.write(f"・ {ingredient_name}")
                            st.markdown("---")
                            st.markdown("**📝 作り方**")
                            st.write(row["steps"])

# --- 🎓 レシピ検定 ---
elif mode == "🎓 レシピ検定":
    st.title("🎓 レシピ検定")
    if not df.empty and len(df) >= 4:
        if 'quiz_state' not in st.session_state: st.session_state.quiz_state = "start"
        if 'current_quiz' not in st.session_state: st.session_state.current_quiz = None
        def generate_quiz():
            correct_row = df.sample(1).iloc[0]
            wrong_titles = df[df["title"] != correct_row["title"]]["title"].sample(3).tolist()
            options = wrong_titles + [correct_row["title"]]
            random.shuffle(options)
            st.session_state.current_quiz = {"data": correct_row, "options": options, "correct_answer": correct_row["title"]}
            st.session_state.quiz_state = "answering"
        col1, col2 = st.columns([2, 1])
        with col2:
            st.write("")
            if st.button("🔄 次の問題 / スタート", type="primary"):
                generate_quiz()
                st.rerun()
        if st.session_state.quiz_state == "answering" and st.session_state.current_quiz:
            q = st.session_state.current_quiz
            row = q["data"]
            with col1:
                st.markdown("### Q. この料理名は？")
                if row["image"] and str(row["image"]).startswith("http"): st.image(row["image"], width=400)
                else:
                    st.info("📷 画像なし")
                    st.write("ヒント: " + " / ".join(row["ingredients"]))
                user_answer = st.radio("選択:", q["options"], key="quiz_radio")
                if st.button("回答"):
                    if user_answer == q["correct_answer"]:
                        st.balloons()
                        st.success("🎉 正解！")
                    else: st.error(f"残念... 正解は「{q['correct_answer']}」")
    else: st.warning("データ不足")
