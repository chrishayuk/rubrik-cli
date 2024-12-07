from llm_client import LLMClient

llm = LLMClient(provider="ollama", model="llama3.3")
messages = [{"role": "user", "content": "Who was Albert Einstein?"}]

print("Testing streaming...")
for token in llm.create_completion_stream(messages):
    print("TOKEN:", token, flush=True)
