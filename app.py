import re
import os
import streamlit as st
from openai import OpenAI
from google import genai
import anthropic

from concurrent.futures import ThreadPoolExecutor, as_completed

# =====================================================================
# 各種AIクライアントの初期化
# =====================================================================
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

gemini_client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

# 環境変数がうまく動かない場合は、以下のように直接キーを記述しても大丈夫です
# claude_client = anthropic.Anthropic(api_key="sk-ant-xxxxxxxxxxxxxxxxxxxxxxx")
claude_client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

# =====================================================================
# 各AIの呼び出し関数
# =====================================================================
def ask_gpt(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # 必要に応じて gpt-4o-mini などに変更してください
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"GPTエラー: {e}"

def ask_gemini(prompt):
    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Geminiエラー: {e}"

def ask_claude(prompt):
    try:
        response = claude_client.messages.create(
            model="claude-haiku-4-5-20251001",  # ← 動作確認できた100%正確なモデル名
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        return f"Claudeエラー: {e}"

import base64

def image_to_text(uploaded_file):
    try:
        image_bytes = uploaded_file.read()

        image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "この画像の文字だけをそのまま出力してください。"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ]
        )

        return response.choices[0].message.content

    except Exception as e:
        st.error(e)
        return ""

def get_score(text):

    match = re.search(r"(\d+)\s*点", text)

    if match:
        return match.group(1)

    return "?"

def run_grading(question, answer, mode, level_prompt):

    if mode == "英作文":
        prompt = f"""
    あなたは大学受験英語の添削者です。

    以下の条件を必ず守ってください：
    {level_prompt}

    【問題】
    {question}

    【答案】
    {answer}

    以下の形式で出力してください。

    【採点】
    100点満点

    【文法ミス】

    【表現の改善】

    【模範解答】

    【解説】
    """
    elif mode == "数学記述":
        prompt = f"""
    あなたは大学受験数学の採点者です。

    以下の条件を必ず守ってください：
    {level_prompt}

    【問題】
    {question}

    【答案】
    {answer}

    以下の形式で出力してください。

    【採点】
    100点満点

    【正しい点】

    【論理の不足】

    【改善点】

    【模範解答】

    【解説】
    """
    else:
        prompt = f"""
    あなたは大学受験理科の採点者です。

    以下の条件を必ず守ってください：
    {level_prompt}
        

    【問題】
    {question}

    【答案】
    {answer}

    以下の形式で出力してください。

    【採点】
    100点満点

    【正しい点】

    【不足点】

    【改善点】

    【模範解答】

    【解説】
    """

        # 画面上の進捗ステータス表示
        gpt_status = st.empty()
        gemini_status = st.empty()
        claude_status = st.empty()

        gpt_status.info("🤖 GPT 添削中...")
        gemini_status.info("✨ Gemini 添削中...")
        claude_status.info("🦉 Claude 添削中...")

        gpt_result = ""
        gemini_result = ""
        claude_result = ""

        # 3つのスレッドで並列処理を実行
        with ThreadPoolExecutor(max_workers=3) as executor:

            futures = {
                executor.submit(ask_gpt, prompt): "gpt",
                executor.submit(ask_gemini, prompt): "gemini",
                executor.submit(ask_claude, prompt): "claude"
            }

            for future in as_completed(futures):
                ai_name = futures[future]
                result = future.result()

                if ai_name == "gpt":
                    gpt_result = result
                    gpt_status.success("🤖 GPT 完了")
                elif ai_name == "gemini":
                    gemini_result = result
                    gemini_status.success("✨ Gemini 完了")
                elif ai_name == "claude":
                    claude_result = result
                    claude_status.success("🦉 Claude 完了")

        gpt_score = get_score(gpt_result)
        gemini_score = get_score(gemini_result)
        claude_score = get_score(claude_result)
        
        st.subheader("採点結果")

        score1, score2, score3 = st.columns(3)

        with score1:
            st.metric("GPT", f"{gpt_score}点")

        with score2:
            st.metric("Gemini", f"{gemini_score}点")

        with score3:
            st.metric("Claude", f"{claude_score}点")
        
        # 画面を3分割して結果を横並びで表示
        st.divider()

        with st.expander("🤖 GPT の添削結果"):
            st.write(gpt_result)

        with st.expander("✨ Gemini の添削結果"):
            st.write(gemini_result)

        with st.expander("🦉 Claude の添削結果"):
            st.write(claude_result)

# =====================================================================
# Streamlit UI画面の構築
# =====================================================================
st.title("AI添削比較ツール")

mode = st.selectbox(
    "問題タイプ",
    ["英作文", "数学記述", "理科記述"]
)

level = st.selectbox(
    "対象レベル",
    ["小学生", "中学生", "高校生",]
)

question = st.text_area("問題文")
problem_image = st.file_uploader(
    "または問題画像をアップロード",
    type=["png", "jpg", "jpeg"]
)
answer = st.text_area("答案")
answer_image = st.file_uploader(
    "または答案画像をアップロード",
    type=["png", "jpg", "jpeg"]
)

if problem_image:
    st.image(problem_image, caption="問題画像")

if answer_image:
    st.image(answer_image, caption="答案画像")

if level == "小学生":
    level_prompt = "小学生にも理解できるように、やさしい言葉で説明してください。"
elif level == "中学生":
    level_prompt = "中学生レベルの標準的な説明にしてください。"
else:
    level_prompt = "高校生・大学受験レベルとして適切な厳密な解説をしてください。"

# --------------------
# OCRボタン
# --------------------
if problem_image or answer_image:

    if st.button("OCR実行"):

        if not question.strip() and not problem_image:
            st.warning("問題文を入力するか、問題画像をアップロードしてください")
            st.stop()

        if not answer.strip() and not answer_image:
            st.warning("答案を入力するか、答案画像をアップロードしてください")
            st.stop()

        if problem_image:
            question = image_to_text(problem_image)
            
        if answer_image:
            answer = image_to_text(answer_image)

        st.session_state.question = question
        st.session_state.answer = answer

    if (problem_image or answer_image) and "question" in st.session_state:

        st.subheader("OCR結果")

        st.session_state.question = st.text_area(
            "問題文",
            st.session_state.question
        )

        st.session_state.answer = st.text_area(
            "答案",
            st.session_state.answer
        )

    if "question" in st.session_state:

        if st.button("添削開始"):

            question = st.session_state.question
            answer = st.session_state.answer

            run_grading(
                question,
                answer,
                mode,
                level_prompt
            )

        # モードに応じたプロンプトの出し分け
          

if not problem_image and not answer_image:

    if st.button("添削開始"):

        question = question
        answer = answer

        run_grading(
            question,
            answer,
            mode,
            level_prompt
        )