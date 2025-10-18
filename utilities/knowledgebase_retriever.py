from typing import List, Optional, Dict, Any
from utilities.llm_manager import get_custom_vector_db
from configuration import SSTDConfig
from agno.agent import Agent

class KnowledgebaseRetriever:
    def __init__(self, user_id: str, kb_list: List[str], top_k: int = 20):
        self.user_id = user_id
        self.kb_list = kb_list
        self.top_k = 20

    def get_retriever(self):
        def retriever(query: str, agent: Optional[Agent] = None, num_documents: int = 20, **kwargs) -> Optional[List[Dict[str, Any]]]:
            results = []
            try:
                for kb_name in self.kb_list:
                    vector_db = get_custom_vector_db(schema=SSTDConfig.SSTD_SCHEMA, table_name=SSTDConfig.KB_TABLE)
                    kb_filters = {"kb_name":kb_name, "user_id":self.user_id}
                    docs = vector_db.search(query=query, limit=self.top_k, filters=kb_filters)
                    for doc in docs:
                        results.append({
                            "id": getattr(doc, "id", None),
                            "name": getattr(doc, "name", None),
                            "content": getattr(doc, "content", ""),
                            "meta_data": getattr(doc, "meta_data", {})
                        })
                print("Documents Retrieved Successfully!")
                return results
            except Exception as e:
                print("Error:", e)
                return None
        return retriever

