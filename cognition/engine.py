from openai import OpenAI

client = OpenAI()
MODEL = "gpt-5.3"


def think(prompt):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400)
    return response.choices[0].message.content