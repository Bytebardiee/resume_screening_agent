import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

def test_model(model_name):
    print(f"Testing model: {model_name}")
    try:
        llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key)
        response = llm.invoke([HumanMessage(content="Hello, are you working?")])
        print(f"Success! Response: {response.content}")
        return True
    except Exception as e:
        print(f"Failed: {e}")
        return False

models_to_test = [
    "gemini-1.5-flash",
    "models/gemini-1.5-flash",
    "gemini-1.5-flash-001",
    "gemini-1.5-pro",
    "gemini-pro"
]

for m in models_to_test:
    if test_model(m):
        break
