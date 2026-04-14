from langgraph.graph import MessagesState

# https://docs.langchain.com/oss/python/langgraph/graph-api#messagesstate 
# 참고 바람
class CustomMessagesState(MessagesState):
    mode: str