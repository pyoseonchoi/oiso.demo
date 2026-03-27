from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

TRANSLATE_AGENT_PROMPT = """You will receive input in the following format:

<user_language>
The user's native language
</user_language>
<translation_target>
The content to be translated
</translation_target>

Your task is to translate the text within the <translation_target> tags into the language specified in the <user_language> tags. 
Do not provide any text, explanations, or commentary other than the translation itself."""

translator_agent = create_agent(
    ChatOpenAI(model="gpt-4.1-nano", temperature=0.7),
    system_prompt=TRANSLATE_AGENT_PROMPT
)