from data_agent.agent.llm import get_llm_client

if __name__=="__main__":
    llm=get_llm_client()

    print(llm.invoke("你好呀"))