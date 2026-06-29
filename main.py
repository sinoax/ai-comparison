import os
from openai import OpenAI
from google import genai

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

gemini_client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

def ask_gpt(prompt):
    response = client.responses.create(
        model="gpt-5",
        input=prompt
    )
    return response.output_text

def ask_gemini(prompt):
    try:
        response = gemini_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
        )

        return response.text

    except Exception as e:
        return f"Geminiエラー: {e}"
    
def multiline_input():
    print("答案を入力してください。")
    print("終了したら END と入力してください。")

    lines = []

    while True:
        line = input()

        if line == "END":
            break

        lines.append(line)

    return "\n".join(lines)

mode = input(
        "問題タイプを選択してください\n"
        "1: 英作文\n"
        "2: 数学記述\n"
        "3: 理科記述\n"
        "入力: "
    )

question = input("問題文を入力してください:\n")
answer = multiline_input()

if mode == "1":
    prompt = f"""
あなたは大学受験英語の添削者です。

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

elif mode == "2":
    prompt = f"""
あなたは大学受験数学の採点者です。

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

elif mode == "3":
    prompt = f"""
あなたは大学受験理科の採点者です。

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

else:
    print("1〜3を入力してください")
    exit()

gpt_result = ask_gpt(prompt)
gemini_result = ask_gemini(prompt)

print("\n====================")
print("GPT 添削結果 ") 
print("====================\n")

print(gpt_result)

print("\n====================")
print("Gemini 添削結果 ") 
print("====================\n")

print(gemini_result)