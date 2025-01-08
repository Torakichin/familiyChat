import streamlit as st
import sqlite3
import datetime
import time

# データベースファイルのパス
DB_FILE = "chat_history.db"
PASSWORD = "198311"  # 平文パスワード

# ページ設定
st.set_page_config(page_title="家族チャット", layout="centered", page_icon="")
st.write(
    """<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>""",
    unsafe_allow_html=True,
)

# データベース接続とテーブル作成
def init_db():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        st.error(f"データベースの初期化に失敗しました: {e}")

# メッセージをデータベースに保存
def save_message(user, message):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO messages (user, message, timestamp) VALUES (?, ?, ?)", (user, message, timestamp))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        st.error(f"メッセージの保存に失敗しました: {e}")

# メッセージ履歴を取得
def get_messages(limit=None):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        if limit:
            cursor.execute("SELECT user, message, timestamp FROM messages ORDER BY timestamp DESC LIMIT ?", (limit,))
        else:
            cursor.execute("SELECT user, message, timestamp FROM messages ORDER BY timestamp")
        messages = cursor.fetchall()
        conn.close()
        return messages[::-1]
    except sqlite3.Error as e:
        st.error(f"メッセージの取得に失敗しました: {e}")
        return []

# アプリケーションの初期化
init_db()

# パスワード入力
if "password_correct" not in st.session_state:
    st.session_state.password_correct = False

if not st.session_state.password_correct:
    password = st.text_input("パスワードを入力してください", type="password")
    if password == PASSWORD:
        st.session_state.password_correct = True
        st.experimental_rerun()
    elif password != "":
        st.error("パスワードが違います")

if st.session_state.password_correct:
    # 全履歴表示フラグ
    if "show_all_messages" not in st.session_state:
        st.session_state.show_all_messages = False

    # 入力フォームを最上部に配置
    with st.container():
        col1, col2 = st.columns([1, 3])
        with col1:
            user = st.selectbox("名前を選択", ["父", "母", "ののか", "まさむね"])
        with col2:
            prompt = st.chat_input("メッセージを入力してください")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # メッセージ送信処理
    if user and prompt:
        st.session_state.messages.append({"role": "user", "content": prompt, "user": user})
        save_message(user, prompt)
        st.balloons()  # バルーンを飛ばす
        time.sleep(2) # 2秒待機
        st.experimental_rerun()

    # メッセージ表示領域
    message_area = st.container()

    # メッセージ履歴を表示（最新のメッセージが上に表示されるように変更）
    with message_area:
        messages_to_show = get_messages() if st.session_state.show_all_messages else get_messages(5)

        for message in messages_to_show[::-1]:
            with st.chat_message(message[0]):
                st.markdown(message[1])
                st.caption(message[2]) # タイムスタンプのみ表示

    # 過去の履歴を見るボタンを最下部に配置
    if st.button("過去の履歴を全て見る", key="show_all_button"):
        st.session_state.show_all_messages = True

else:
    st.stop()
