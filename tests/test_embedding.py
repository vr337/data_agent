
from data_agent.infra.embedding.manager import get_embedding_client_manger

if __name__=="__main__":
     def test():
        # 初始化客户端
        embedding_client_manager=get_embedding_client_manger()
        embedding_client_manager.init_client()
        # 单文本嵌入
        result1= embedding_client_manager.client.embed_query("hello")
        print(result1)
        print(len(result1))
        # 多文本嵌入
        result2= embedding_client_manager.client.embed_documents(["hello","world"])
        print(result2)
        print(len(result2))
test()