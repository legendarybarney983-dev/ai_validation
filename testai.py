from openai import OpenAI

client = OpenAI(
    base_url="http://172.16.90.32:8001/v1",
    api_key="dummy"
)

response = client.chat.completions.create(
    model="Llama-3.2-3B-Instruct-Q4_K_M.gguf",
    messages=[
        {
            "role": "user",
            "content": "Say hello in kannada"
        }
    ],
    temperature=0
)

print(response.choices[0].message.content)