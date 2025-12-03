原因が判明しました！
スプレッドシートの項目名（見出し）で、見た目を整えるために\*\*「Alt+Enter（改行）」\*\*を使っていませんか？

コンピュータにとっては、

  * `開封後賞味期限目安`（1行）
  * `開封後賞味(改行)期限目安`（2行）

は、\*\*「完全に別の名前」\*\*として扱われてしまいます。
そのため、プログラムが「そんな名前の列はないよ」と判断してデータが空っぽになっていました。

スプレッドシートを直す必要はありません！
**「プログラム側で、読み込むときに勝手に改行を削除してあげる」** 処理を追加しました。これでどんな書き方をしていても正しく読み込まれます。

`app.py` を以下のコードに上書きしてください。

### 📋 修正版コード（列名の改行対応・app.py）

```python
import streamlit as st
import pandas as pd
import random
import urllib.parse
from rapidfuzz import fuzz
from streamlit_mic_recorder import speech_to_text

# ページ設定
st.set_page_config(page_title="Recipe Viewer", page_icon="img/favicon.ico", layout="wide")

# ==========================================
# 👇 設定エリア：URL設定完了済み
# ==========================================
recipe_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQN7zOdMeK_lRCOzG8coIdHkdawIbSvlLyhU5KpEHAbca75YCCT1gBwB85K2ah5gcr6Yd3rPessbNWN/pub?gid=0&single=true&output=csv"
ingredient_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQN7zOdMeK_lRCOzG8coIdHkdawIbSvlLyhU5KpEHAbca75YCCT1gBwB85K2ah5gcr6Yd3rPessbNWN/pub?gid=805502789&single=true&output=csv"
news_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQN7zOdMeK_lRCOzG8coIdHkdawIbSvlLyhU5KpEHAbca75YCCT1gBwB85K2ah5gcr6Yd3rPessbNWN/pub?gid=1725848377&single=true&output=csv"
store_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQN7zOdMeK_lRCOzG8coIdHkdawIbSvlLyhU5KpEHAbca75YCCT1gBwB85K2ah5gcr6Yd3rPessbNWN/pub?gid=285648220&single=true&output=csv"
news_log_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQFXVfpeGAVHkjw65-GFPStuh1PSvteeVcckdAGYKhIOZ1YBX3HftRHgXxY-ozV_AWk1E-s4zP4lqYC/pub?output=csv"

# フォーム設定
news_form_url = "https://docs.google.com/forms/d/e/1FAIpQLSeLSyph6KJ3aPPgdCCxKuZ2tRLCZI13ftsM3-godUqzB1hOyg/viewform?usp=pp_url"
news_entry_store = "entry.1108417758"
news_entry_title = "entry.1493447951"
feedback_form_url = "https://docs.google.com/forms/d/e/1FAIpQLSegPgDFDG8h_cxV2Z7BcBkw3rZWjCUU9mCpIPqwwp_C-laXPQ/viewform?usp=pp_url"
feedback_entry_store = "entry.1319375613"
feedback_entry_recipe = "entry.973206102"

# ==========================================

# --- CSSスタイル ---
st.markdown("""
<style>
    div[data-testid="column"] { align-self: center; }
    div.stButton > button { height: 3rem; border-radius: 20px; padding: 0px 10px; width: 100%; }
    
    @media (max-width: 768px) {
        div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stHorizontalBlock"] {
            flex-direction: row !important; flex-wrap: nowrap !important; gap: 0.5rem !important;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stHorizontalBlock"] [data-testid="column"] {
            width: auto !important; flex: unset !important; min-width: 0 !important;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stHorizontalBlock"] [data-testid="column"]:nth-child(1) {
            flex: 0 0 50px !important; max-width: 50px !important;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stHorizontalBlock"] [data-testid="column"]:nth-child(2) {
            flex: 1 1 auto !important;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stHorizontalBlock"] [data-testid="column"]:nth-child(3) {
            flex: 0 0 50px !important; max-width: 50px !important;
        }
    }
</style>
""", unsafe_allow_html=True)

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

    def clean_ingredients_list(raw_text):
        names = []
        if pd.isna(raw_text): return []
        for line in str(raw_text).split('\n'):
            parts = line.split('、')
            if parts[0].strip():
                names.append(parts[0].strip())
        return names

    # ① レシピ
    try:
        df_recipe = pd.read_csv(recipe_csv)
        # 列名の改行を削除してきれいにする（これでエラー回避！）
        df_recipe.columns = df_recipe.columns.str.replace('\n', '').str.replace('\r', '').str.strip()
        
        df_recipe["ingredients_raw"] = df_recipe["ingredients"].fillna("") 
        df_recipe["ingredients"] = df_recipe["ingredients_raw"].apply(clean_ingredients_list)
        
        if "target_stores" not in df_recipe.columns: df_recipe["target_stores"] = "共通"
        if "image" in df_recipe.columns: df_recipe["image"] = df_recipe["image"].apply(convert_google_drive_url)
        if "video" in df_recipe.columns:
            df_recipe["video"] = df_recipe["video"].apply(lambda x: convert_google_drive_url(x) if "drive.google.com" in str(x) else x)
        
        for col in ["tableware", "cutlery", "caution"]:
            if col not in df_recipe.columns:
                df_recipe[col] = "-"
        
        df_recipe = df_recipe.fillna("-")
    except: df_recipe = pd.DataFrame()

    # ② 食材マスタ
    try:
        df_ing = pd.read_csv(ingredient_csv)
        # ★ここが重要：列名の改行を削除する処理を追加！★
        df_ing.columns = df_ing.columns.str.replace('\n', '').str.replace('\r', '').str.strip()
        
        df_ing = df_ing.fillna("-")
        if "商品名" in df_ing.columns:
            df_ing["商品名"] = df_ing["商品名"].astype(str).str.strip()
            ing_dict = df_ing.set_index("商品名").to_dict(orient="index")
        else: ing_dict = {}
    except: ing_dict = {}

    # ③ お知らせ
    try:
        df_news = pd.read_csv(news_csv)
        df_news = df_news.fillna("")
    except: df_news = pd.DataFrame()

    # ④ 店舗マスタ
    try:
        df_stores = pd.read_csv(store_csv, dtype=str)
        df_stores = df_stores.fillna("")
        if "store_code" in df_stores.columns: df_stores["store_code"] = df_stores["store_code"].str.strip()
        if "password" in df_stores.columns: df_stores["password"] = df_stores["password"].str.strip()
    except: df_stores = pd.DataFrame()

    # ⑤ 既読ログ
    try:
        df_log = pd.read_csv(news_log_csv)
        df_log = df_log.fillna("")
    except: df_log = pd.DataFrame()

    return df_recipe, ing_dict, df_news, df_stores, df_log

df, ingredient_dict, df_news, df_stores, df_log = load_data()


# --- 材料文字列をパースして表データにする関数 ---
def parse_ingredients_to_df(raw_text):
    data = []
    lines = str(raw_text).split('\n')
    for line in lines:
        parts = line.split('、')
        if len(parts) >= 3:
            data.append({"食材": parts[0], "使用量": parts[1], "備考": parts[2]})
        elif len(parts) == 2:
            data.append({"食材": parts[0], "使用量": parts[1], "備考": ""})
        elif len(parts) == 1 and parts[0].strip():
            data.append({"食材": parts[0], "使用量": "", "備考": ""})
    if not data:
        return pd.DataFrame(columns=["食材", "使用量", "備考"])
    return pd.DataFrame(data)


# --- 印刷用HTML生成関数 ---
def generate_print_html(row, ing_df):
    ing_rows = ""
    for _, item in ing_df.iterrows():
        ing_rows += f"<tr><td>{item['食材']}</td><td>{item['使用量']}</td><td>{item['備考']}</td></tr>"

    steps_html = str(row["steps"]).replace("\n", "<br>")
    tableware_html = str(row["tableware"]).replace("\n", "<br>")
    cutlery_html = str(row["cutlery"]).replace("\n", "<br>")
    caution_html = str(row["caution"]).replace("\n", "<br>")
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{row['title']}</title>
        <style>
            body {{ font-family: sans-serif; padding: 20px; color: #000; }}
            .header-table {{ width: 100%; border-collapse: collapse; margin-bottom: 10px; }}
            .header-table th, .header-table td {{ border: 2px solid #000; padding: 8px; text-align: center; }}
            .header-table th {{ background-color: #eee; font-weight: bold; width: 15%; }}
            .title {{ font-size: 24px; font-weight: bold; text-align: center; }}
            .main-container {{ display: flex; gap: 10px; border: 2px solid #000; }}
            .left-col {{ flex: 1; padding: 10px; border-right: 2px solid #000; text-align: center; }}
            .right-col {{ flex: 1; display: flex; flex-direction: column; }}
            .info-row {{ border-bottom: 2px solid #000; padding: 5px; min-height: 50px; }}
            .info-row:last-child {{ border-bottom: none; }}
            .info-label {{ font-weight: bold; display: block; margin-bottom: 5px; font-size: 0.9em; }}
            .ing-table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.9em; }}
            .ing-table th, .ing-table td {{ border: 1px solid #000; padding: 6px; }}
            .ing-table th {{ background-color: #eee; text-align: center; }}
            .steps-box {{ border: 2px solid #000; border-top: none; padding: 15px; }}
            @media print {{ body {{ padding: 0; }} }}
        </style>
    </head>
    <body>
        <table class="header-table">
            <tr>
                <td class="title" colspan="4">{row['title']}</td>
                <th>調理時間</th>
                <td>{row['time']}</td>
            </tr>
        </table>
        <div class="main-container">
            <div class="left-col">
                <img src="{row['image']}" style="max-width:100%; max-height:300px; object-fit:contain;">
            </div>
            <div class="right-col">
                <div class="info-row"><span class="info-label">使用食器</span>{tableware_html}</div>
                <div class="info-row"><span class="info-label">カトラリー/コンディメント</span>{cutlery_html}</div>
                <div class="info-row" style="flex:1;"><span class="info-label">詳細・注意事項</span><span style="color:red;">{caution_html}</span></div>
            </div>
        </div>
        <table class="ing-table">
            <thead><tr><th>食材</th><th>使用量</th><th>備考</th></tr></thead>
            <tbody>{ing_rows}</tbody>
        </table>
        <div class="steps-box"><b>手順：</b><br>{steps_html}</div>
        <script>window.onload=function(){{window.print();}}</script>
    </body>
    </html>
    """
    return html

# --- 全画面表示用ダイアログ ---
@st.dialog("レシピ詳細", width="large")
def show_recipe_modal(row, ing_dict):
    col_header, col_print = st.columns([8, 1])
    with col_header: st.header(row["title"])
    
    ing_df = parse_ingredients_to_df(row["ingredients_raw"])

    with col_print:
        html_data = generate_print_html(row, ing_df)
        st.download_button(label="🖨️", data=html_data, file_name=f"{row['title']}.html", mime="text/html", help="印刷用ファイルをダウンロード")
    
    if "video" in row and str(row["video"]).startswith("http"):
        with st.expander("🎥 調理動画を見る", expanded=False):
            st.video(row["video"])

    c1, c2 = st.columns([1.2, 1])
    with c1:
        if row["image"] and str(row["image"]).startswith("http"):
            st.image(row["image"], use_container_width=True)
        st.caption(f"⏱ 調理時間: {row['time']} | 📂 {row['category']}")

    with c2:
        with st.container(border=True):
            st.markdown(f"**🍽️ 使用食器**")
            st.markdown(str(row['tableware']).replace("\n", "  \n"))
            st.divider()
            st.markdown(f"**🍴 カトラリー・コンディメント**")
            st.markdown(str(row['cutlery']).replace("\n", "  \n"))
            st.divider()
            st.markdown(f"**⚠️ 詳細・注意事項**")
            st.info(str(row['caution']).replace("\n", "  \n"))

    st.divider()

    c3, c4 = st.columns([1, 1])
    
    with c3:
        st.subheader("🛒 食材・分量")
        for _, item in ing_df.iterrows():
            name = item['食材']
            cols = st.columns([2, 1, 2])
            
            matched_info = None
            if name in ingredient_dict: matched_info = ingredient_dict[name]
            else:
                for k, info in ingredient_dict.items():
                    if name in k: matched_info = info; break
            
            with cols[0]:
                if matched_info:
                    with st.popover(f"ℹ️ {name}", use_container_width=True):
                        st.markdown(f"**{matched_info.get('商品名', name)}**")
                        st.caption(f"商品コード: {matched_info.get('商品コード', '-')}")
                        # ★ここを変更：ご希望の項目を表示するように修正★
                        st.markdown(f"**賞味期限**: {matched_info.get('賞味期限', '-')}")
                        st.markdown(f"**保管(開封後)**: {matched_info.get('開封後温度帯', '-')}")
                        st.markdown(f"**期限(開封後)**: {matched_info.get('開封後賞味期限目安', '-')}")
                else:
                    st.write(name)
            with cols[1]: st.write(item['使用量'])
            with cols[2]: st.caption(item['備考'])
            st.markdown("<hr style='margin: 0.2rem 0; border-top: 1px solid #eee;'>", unsafe_allow_html=True)

    with c4:
        st.subheader("📝 作り方")
        st.markdown(str(row["steps"]).replace("\n", "  \n"))

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

        my_read_titles = []
        if not df_log.empty:
            my_logs = df_log[df_log["店舗名"] == st.session_state.store_name]
            my_read_titles = my_logs["確認した記事"].unique().tolist()

        unread_news = []
        read_news = []
        for index, row in df_news.iterrows():
            if row['title'] in my_read_titles: read_news.append(row)
            else: unread_news.append(row)

        st.subheader(f"⚡ 未読のお知らせ ({len(unread_news)})")
        if not unread_news: st.success("🎉 全て確認済みです！")
        else:
            for row in unread_news:
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
                        st.link_button("✅ 既読", link, type="primary")

        if read_news:
            st.divider()
            with st.expander(f"🗄️ 既読のお知らせ履歴 ({len(read_news)})"):
                for row in read_news:
                    st.markdown(f"**✅ {row.get('title', '無題')}**")
                    st.caption(f"📅 {row.get('date', '')}")
                    st.write(row.get('content', ''))
                    st.divider()

# --- 🔍 レシピ検索 ---
elif mode == "🔍 レシピ検索":
    st.title("🔍 Recipe Search")
    
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ""
    if 'last_voice_text' not in st.session_state:
        st.session_state.last_voice_text = None

    def clear_search():
        st.session_state.search_query = ""

    with st.container(border=True):
        col_mic, col_text, col_clear = st.columns([1, 6, 0.7], gap="small")
        with col_mic:
            voice_text = speech_to_text(language='ja', start_prompt="🎤", stop_prompt="⏹️", just_once=True, key='voice_input', use_container_width=True)
        if voice_text and voice_text != st.session_state.last_voice_text:
            st.session_state.search_query = voice_text
            st.session_state.last_voice_text = voice_text
        with col_text:
            search_query = st.text_input("キーワード検索", key="search_query", placeholder="料理名や材料を入力...", label_visibility="collapsed")
        with col_clear:
            st.button("✖", on_click=clear_search, help="検索ワードを削除", use_container_width=True)

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
                q = search_query.lower()
                title = str(row['title']).lower()
                ingredients = " ".join(row['ingredients']) if isinstance(row['ingredients'], list) else str(row['ingredients'])
                ingredients = ingredients.lower()
                title_score = fuzz.partial_ratio(q, title)
                ing_score = fuzz.partial_ratio(q, ingredients)
                return max(title_score * 1.1, ing_score)
            
            filtered_df['match_score'] = filtered_df.apply(get_fuzzy_score, axis=1)
            filtered_df = filtered_df[filtered_df['match_score'] > 60]
            filtered_df = filtered_df.sort_values('match_score', ascending=False)

        st.write(f"検索結果: {len(filtered_df)} 件")
        if filtered_df.empty: st.info("見つかりませんでした")
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
                        st.caption(f"🏢 {row['target_stores']} | 📂 {row['category']} | ⏱ {row['time']}")
                        
                        # ★ここも修正：詳細アコーディオン内もポップオーバー＆改行対応★
                        with st.expander("詳細"):
                            st.markdown("**🛒 食材・分量**")
                            ing_df_simple = parse_ingredients_to_df(row["ingredients_raw"])
                            
                            for _, item in ing_df_simple.iterrows():
                                name = item['食材']
                                cols_exp = st.columns([2, 1, 2])
                                matched_info = None
                                if name in ingredient_dict: matched_info = ingredient_dict[name]
                                else:
                                    for k, info in ingredient_dict.items():
                                        if name in k: matched_info = info; break
                                
                                with cols_exp[0]:
                                    if matched_info:
                                        with st.popover(f"ℹ️ {name}", use_container_width=True):
                                            st.markdown(f"**{matched_info.get('商品名', name)}**")
                                            st.caption(f"商品コード: {matched_info.get('商品コード', '-')}")
                                            # ★詳細アコーディオン内も同じ項目を表示★
                                            st.markdown(f"**賞味期限**: {matched_info.get('賞味期限', '-')}")
                                            st.markdown(f"**保管(開封後)**: {matched_info.get('開封後温度帯', '-')}")
                                            st.markdown(f"**期限(開封後)**: {matched_info.get('開封後賞味期限目安', '-')}")
                                    else:
                                        st.write(name)
                                with cols_exp[1]: st.write(item['使用量'])
                                with cols_exp[2]: st.caption(item['備考'])
                                st.markdown("<hr style='margin: 0.2rem 0; border-top: 1px solid #eee;'>", unsafe_allow_html=True)

                            st.markdown("**📝 作り方**")
                            st.markdown(str(row["steps"]).replace("\n", "  \n"))
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
                    st.write("ヒント: " + str(row["ingredients_raw"]))
                user_answer = st.radio("選択:", q["options"], key="quiz_radio")
                if st.button("回答"):
                    if user_answer == q["correct_answer"]:
                        st.balloons()
                        st.success("🎉 正解！")
                    else: st.error(f"残念... 正解は「{q['correct_answer']}」")
    else: st.warning("データ不足")
```
