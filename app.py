import streamlit as st
import pandas as pd
import random
import urllib.parse
from rapidfuzz import fuzz
from streamlit_mic_recorder import speech_to_text

# ページ設定
st.set_page_config(page_title="Recipe Viewer", layout="wide")

# ==========================================
# 👇 設定エリア：URL設定完了済み
# ==========================================
recipe_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQN7zOdMeK_lRCOzG8coIdHkdawIbSvlLyhU5KpEHAbca75YCCT1gBwB85K2ah5gcr6Yd3rPessbNWN/pub?gid=0&single=true&output=csv"
ingredient_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQN7zOdMeK_lRCOzG8coIdHkdawIbSvlLyhU5KpEHAbca75YCCT1gBwB85K2ah5gcr6Yd3rPessbNWN/pub?gid=805502789&single=true&output=csv"
news_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQN7zOdMeK_lRCOzG8coIdHkdawIbSvlLyhU5KpEHAbca75YCCT1gBwB85K2ah5gcr6Yd3rPessbNWN/pub?gid=1725848377&single=true&output=csv"
store_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQN7zOdMeK_lRCOzG8coIdHkdawIbSvlLyhU5KpEHAbca75YCCT1gBwB85K2ah5gcr6Yd3rPessbNWN/pub?gid=285648220&single=true&output=csv"

# フォーム設定
news_form_url = "https://docs.google.com/forms/d/e/1FAIpQLSeLSyph6KJ3aPPgdCCxKuZ2tRLCZI13ftsM3-godUqzB1hOyg/viewform?usp=pp_url"
news_entry_store = "entry.1108417758"
news_entry_title = "entry.1493447951"
feedback_form_url = "https://docs.google.com/forms/d/e/1FAIpQLSegPgDFDG8h_cxV2Z7BcBkw3rZWjCUU9mCpIPqwwp_C-laXPQ/viewform?usp=pp_url"
feedback_entry_store = "entry.1319375613"
feedback_entry_recipe = "entry.973206102"

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
            except IndexError: return url
        return url

    try:
        df_recipe = pd.read_csv(recipe_csv)
        df_recipe["ingredients"] = df_recipe["ingredients"].apply(lambda x: str(x).split("、") if pd.notnull(x) else [])
        if "target_stores" not in df_recipe.columns: df_recipe["target_stores"] = "共通"
        if "image" in df_recipe.columns: df_recipe["image"] = df_recipe["image"].apply(convert_google_drive_url)
        df_recipe = df_recipe.fillna("")
    except: df_recipe = pd.DataFrame()

    try:
        df_ing = pd.read_csv(ingredient_csv)
        df_ing = df_ing.fillna("-")
        if "商品名" in df_ing.columns:
            df_ing["商品名"] = df_ing["商品名"].astype(str).str.strip()
            ing_dict = df_ing.set_index("商品名").to_dict(orient="index")
        else: ing_dict = {}
    except: ing_dict = {}

    try:
        df_news = pd.read_csv(news_csv)
        df_news = df_news.fillna("")
    except: df_news = pd.DataFrame()

    try:
        df_stores = pd.read_csv(store_csv, dtype=str)
        df_stores = df_stores.fillna("")
        if "store_code" in df_stores.columns: df_stores["store_code"] = df_stores["store_code"].str.strip()
        if "password" in df_stores.columns: df_stores["password"] = df_stores["password"].str.strip()
    except: df_stores = pd.DataFrame()

    return df_recipe, ing_dict, df_news, df_stores

df, ingredient_dict, df_news, df_stores = load_data()


# --- 印刷用HTML生成関数 ---
def generate_print_html(row, ing_dict):
    ing_html = ""
    for ing in row["ingredients"]:
        ing = str(ing).strip()
        detail = ""
        if ing in ing_dict:
            info = ing_dict[ing]
            detail = f"<br><span style='font-size:0.8em; color:#666;'>（期限: {info.get('賞味期限','-')} / 保管: {info.get('納品温度帯(保管温度帯)','-')}）</span>"
        elif any(ing in k for k in ing_dict):
             for k, info in ing_dict.items():
                 if ing in k:
                     detail = f"<br><span style='font-size:0.8em; color:#666;'>（期限: {info.get('賞味期限','-')} / 保管: {info.get('納品温度帯(保管温度帯)','-')}）</span>"
                     break
        ing_html += f"<li><b>{ing}</b>{detail}</li>"

    steps_html = str(row["steps"]).replace("\n", "<br>")

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{row['title']}</title>
        <style>
            body {{ font-family: "Helvetica Neue", Arial, "Hiragino Kaku Gothic ProN", "Hiragino Sans", Meiryo, sans-serif; padding: 40px; color: #333; }}
            h1 {{ border-bottom: 3px solid #ff4b4b; padding-bottom: 10px; margin-bottom: 5px; }}
            .meta {{ color: #666; margin-bottom: 20px; font-size: 0.9em; }}
            .container {{ display: flex; gap: 30px; margin-bottom: 30px; }}
            .image-box {{ flex: 1; text-align: center; }}
            .image-box img {{ max-width: 100%; max-height: 350px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
            .ing-box {{ flex: 1; background: #f9f9f9; padding: 20px; border-radius: 8px; }}
            h2 {{ background: #eee; padding: 5px 10px; border-left: 5px solid #ff4b4b; font-size: 1.2em; }}
            ul {{ padding-left: 20px; line-height: 1.6; }}
            .steps-box {{ line-height: 1.8; font-size: 1.05em; }}
            @media print {{ body {{ padding: 0; }} }}
        </style>
    </head>
    <body>
        <h1>{row['title']}</h1>
        <div class="meta">
            🏢 {row['target_stores']} | 📂 {row['category']} | ⏱ 調理時間: {row['time']}
        </div>
        <div class="container">
            <div class="image-box"><img src="{row['image']}" alt="料理画像"></div>
            <div class="ing-box"><h2>🛒 材料・規格</h2><ul>{ing_html}</ul></div>
        </div>
        <div class="steps-box"><h2>📝 調理手順</h2><div>{steps_html}</div></div>
        <script>window.onload = function() {{ window.print(); }}</script>
    </body>
    </html>
    """
    return html


# --- 全画面表示用ダイアログ ---
@st.dialog("レシピ詳細", width="large")
def show_recipe_modal(row, ing_dict):
    col_header, col_print = st.columns([8, 1])
    with col_header: st.header(row["title"])
    with col_print:
        html_data = generate_print_html(row, ing_dict)
        st.download_button(label="🖨️", data=html_data, file_name=f"{row['title']}.html", mime="text/html", help="印刷用ファイルをダウンロード")
    
    if row["image"] and str(row["image"]).startswith("http"):
        st.image(row["image"], use_container_width=True)
    
    st.caption(f"🏢 {row['target_stores']} | 📂 {row['category']} | ⏱ {row['time']}")
    st.divider()
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("🛒 材料")
        for ingredient_name in row["ingredients"]:
            ingredient_name = str(ingredient_name).strip()
            matched_info = None
            if ingredient_name in ing_dict: matched_info = ing_dict[ingredient_name]
            else:
                for master_name, info in ing_dict.items():
                    if ingredient_name in master_name: matched_info = info; break
            
            if matched_info:
                with st.popover(f"ℹ️ {ingredient_name}"):
                    st.markdown(f"**{matched_info.get('商品名', ingredient_name)}**")
                    st.caption(f"期限: {matched_info.get('賞味期限', '-')}")
                    st.caption(f"保管: {matched_info.get('納品温度帯(保管温度帯)', '-')}")
            else: st.write(f"・ {ingredient_name}")

    with col2:
        st.subheader("📝 作り方")
        st.write(row["steps"])

    st.divider()
    store_enc = urllib.parse.quote(str(st.session_state.store_name))
    recipe_enc = urllib.parse.quote(str(row['title']))
    fb_link = f"{feedback_form_url}&{feedback_entry_store}={store_enc}&{feedback_entry_recipe}={recipe_enc}"
    st.link_button("💬 このレシピへ意見を送る", fb_link, use_container_width=True)


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
            else: st.error("違います")
        else:
            if input_password == "secret123":
                 st.session_state.logged_in = True
                 st.session_state.store_name = "管理者(緊急)"
                 st.rerun()
            else: st.error("エラー")
    st.stop()

# --- レイアウト ---
st.sidebar.title(f"👤 {st.session_state.store_name}")
mode = st.sidebar.radio("メニュー", ["🏠 ホーム", "🔍 レシピ検索", "🎓 検定"])
st.sidebar.divider()

# --- 🏠 ホーム ---
if mode == "🏠 ホーム":
    st.title("📢 お知らせ")
    if df_news.empty: st.info("現在、お知らせはありません。")
    else:
        if "date" in df_news.columns:
            try: df_news["date"] = pd.to_datetime(df_news["date"], errors='coerce'); df_news = df_news.sort_values("date", ascending=False)
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
                    store_enc = urllib.parse.quote(str(st.session_state.store_name))
                    title_enc = urllib.parse.quote(str(row.get('title', '')))
                    link = f"{news_form_url}&{news_entry_store}={store_enc}&{news_entry_title}={title_enc}"
                    st.link_button("✅ 既読", link)

# --- 🔍 レシピ検索 ---
elif mode == "🔍 レシピ検索":
    st.title("🔍 Recipe Search")
    
    # ★検索・削除機能の改善★
    # キーワード保持用のセッションステートを初期化
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ""
    if 'last_voice_text' not in st.session_state:
        st.session_state.last_voice_text = None

    # 削除ボタンの機能
    def clear_search():
        st.session_state.search_query = ""

    col_mic, col_text, col_clear = st.columns([1, 4, 0.5], gap="small")
    
    with col_mic:
        st.write("") 
        voice_text = speech_to_text(language='ja', start_prompt="🎤 音声", stop_prompt="⏹️", just_once=True, key='voice_input', use_container_width=True)
    
    # 音声入力があった場合、かつ前回と同じでなければ更新する（リロードによるゾンビ復活防止）
    if voice_text and voice_text != st.session_state.last_voice_text:
        st.session_state.search_query = voice_text
        st.session_state.last_voice_text = voice_text

    with col_text:
        # keyを指定してsession_stateと直接同期させる
        search_query = st.text_input(
            "キーワード検索", 
            key="search_query", # これにより st.session_state.search_query が入力値になります
            placeholder="料理名や材料...", 
            label_visibility="collapsed"
        )

    with col_clear:
        st.write("") 
        # コールバックでクリア
        st.button("✖", on_click=clear_search, help="検索ワードを削除")

    if not df.empty:
        all_stores = set()
        for stores in df["target_stores"]:
            for store in str(stores).split("、"):
                if store.strip(): all_stores.add(store.strip())
        store_options = ["すべて"] + sorted(list(all_stores))
        selected_store = st.sidebar.selectbox("業態", store_options)
    else: selected_store = "すべて"
    
    if not df.empty and "category" in df.columns:
        categories = ["すべて"] + list(df["category"].unique())
        selected_category = st.sidebar.selectbox("カテゴリ", categories)
    else: selected_category = "すべて"

    if not df.empty:
        filtered_df = df.copy()
        if selected_store != "すべて":
            filtered_df = filtered_df[filtered_df["target_stores"].astype(str).apply(lambda x: selected_store in x)]
        if selected_category != "すべて":
            filtered_df = filtered_df[filtered_df["category"] == selected_category]
        if search_query:
            def get_fuzzy_score(row):
                title_score = fuzz.partial_ratio(search_query.lower(), str(row['title']).lower())
                ingredients_str = " ".join(row['ingredients'])
                ing_score = fuzz.partial_ratio(search_query.lower(), ingredients_str.lower())
                return max(title_score, ing_score)
            filtered_df['match_score'] = filtered_df.apply(get_fuzzy_score, axis=1)
            filtered_df = filtered_df[filtered_df['match_score'] > 50]
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
                        
                        if st.button(f"🔍 {row['title']}", key=f"btn_{index}", use_container_width=True):
                            show_recipe_modal(row, ingredient_dict)
                        
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
                                        if ingredient_name in master_name: matched_info = info; break
                                if matched_info:
                                    with st.popover(f"ℹ️ {ingredient_name}"):
                                        st.markdown(f"### {matched_info.get('商品名', ingredient_name)}")
                                        st.caption(f"コード: {matched_info.get('商品コード', '-')}")
                                        st.markdown(f"**賞味期限**: {matched_info.get('賞味期限', '-')}")
                                        st.markdown(f"**保管温度**: {matched_info.get('納品温度帯(保管温度帯)', '-')}")
                                else: st.write(f"・ {ingredient_name}")
                            st.markdown("---")
                            st.markdown("**📝 作り方**")
                            st.write(row["steps"])
                            
                            st.divider()
                            store_enc = urllib.parse.quote(str(st.session_state.store_name))
                            recipe_enc = urllib.parse.quote(str(row['title']))
                            fb_link = f"{feedback_form_url}&{feedback_entry_store}={store_enc}&{feedback_entry_recipe}={recipe_enc}"
                            st.link_button("💬 このレシピへ意見を送る", fb_link)

# --- 🎓 レシピ検定 ---
elif mode == "🎓 検定":
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
            if st.button("🔄 スタート", type="primary"):
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
