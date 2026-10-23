# import os
# import google.generativeai as genai
# from dotenv import load_dotenv
# from typing import List, Dict


# # Load environment variables
# load_dotenv()

# # New configuration format
# genai.configure(
#     api_key=os.getenv("GEMINI_API_KEY"),
#     transport='rest'  # Add this line to avoid gRPC timeout
# )

# # Use the latest model name
# model = genai.GenerativeModel('gemini-1.5-pro')  # Updated model name

# class Generator:
#     def __init__(self):
#         self.model = genai.GenerativeModel('gemini-1.5-pro')  # Updated model name
        
#     def generate_response(self, query: str, context: str, sources: List[Dict]) -> Dict:
#         prompt = f"""
#             You are SmartScholar, an AI study assistant. Use the following context to answer the query.
#             Include citations like [Source X] for each fact, matching the sources list provided. And if Required use your own intelligence to make the answer robust.

#             Context:
#             {context}

#             Sources:
#             {sources}

#             Query: {query}
#             Answer:
#             """
        
#         try:
#             response = self.model.generate_content(prompt)
#             return {
#                 "query": query,
#                 "answer": response.text,
#                 "sources": sources,
#                 "token_count": response.usage_metadata.total_token_count
#             }
#         except Exception as e:
#             return {
#                 "query": query,
#                 "error": f"Generation failed: {str(e)}"
#             }
        

# if __name__ == "__main__":
#     generator = Generator()

#     augmented = {'query': 'YouTube history', 'context': "YouTube, founded in 2005, has become the world's largest video-sharing platform...\n\n1.1 Overview of the Enterprise:", 'sources': [{'document_id': 'new.txt', 'chunk_order': 1, 'original_score': 0.6280466158966196, 'rerank_score': 2.8288989067077637}, {'document_id': 'new.txt', 'chunk_order': 0, 'original_score': 0.42788867665772556, 'rerank_score': -11.016846656799316}], 'token_count': 75}

#     result = generator.generate_response("What is YouTube's history?", augmented['context'], augmented['sources'])

#     print(result)


#################################################################################################################################
#################################################################################################################################

# import os
# from typing import List, Dict, Literal, Optional
# from dotenv import load_dotenv
# import google.generativeai as genai
# from pydantic_ai import agent
# from pydantic import BaseModel


# # Load environment variables
# load_dotenv()

# # Configure Gemini API
# genai.configure(api_key=os.getenv("GEMINI_API_KEY"), transport="rest")

# # Define supported query intents
# QueryIntent = Literal["factual", "explanatory", "technical", "conceptual", "general"]


# class QueryAgent(BaseModel):
#     """
#     Base class for all agents handling different query intents.
#     """
#     query: str

#     def system_prompt(self) -> str:
#         raise NotImplementedError("Subclasses must implement system_prompt()")

#     def generate_response(self) -> Dict:
#         """
#         Generates a response using Gemini 1.5 Pro based on the query intent.
#         """
#         prompt = self.system_prompt()
#         model = genai.GenerativeModel("gemini-1.5-pro")

#         try:
#             response = model.generate_content(prompt)
#             return {
#                 "query": self.query,
#                 "answer": response.text,
#                 "token_count": response.usage_metadata.total_token_count,
#             }
#         except Exception as e:
#             return {"query": self.query, "error": f"Generation failed: {str(e)}"}


# # Agents WITH Retrieval (Requires Context & Sources)
# @agent
# class FactualAgent(QueryAgent):
#     context: str
#     sources: List[Dict]

#     def system_prompt(self) -> str:
#         return f"""
#         You are SmartScholar, an AI study assistant. Answer the query with factual accuracy.
#         Cite sources in the format [Source X] where X is the document_id.

#         Context:
#         {self.context}

#         Sources:
#         {self.sources}

#         Query: {self.query}
#         Answer:
#         """


# @agent
# class ExplanatoryAgent(QueryAgent):
#     context: str
#     sources: List[Dict]

#     def system_prompt(self) -> str:
#         return f"""
#         You are SmartScholar, an AI that explains concepts step-by-step.
#         Provide a structured response with examples where necessary.
#         Cite sources like [Source X].

#         Context:
#         {self.context}

#         Sources:
#         {self.sources}

#         Query: {self.query}
#         Answer:
#         """


# @agent
# class TechnicalAgent(QueryAgent):
#     context: str
#     sources: List[Dict]

#     def system_prompt(self) -> str:
#         return f"""
#         You are SmartScholar, an AI study assistant with expertise in technical subjects.
#         Provide a structured, precise response using markdown for formatting (if needed).
#         Cite sources like [Source X].

#         Context:
#         {self.context}

#         Sources:
#         {self.sources}

#         Query: {self.query}
#         Answer:
#         """


# @agent
# class ConceptualAgent(QueryAgent):
#     context: str
#     sources: List[Dict]

#     def system_prompt(self) -> str:
#         return f"""
#         You are SmartScholar, an AI tutor that explains complex concepts using analogies and intuition.
#         Provide a clear, engaging answer that simplifies the topic.
#         Cite sources like [Source X].

#         Context:
#         {self.context}

#         Sources:
#         {self.sources}

#         Query: {self.query}
#         Answer:
#         """


# @agent
# class GeneralAgent(QueryAgent):
#     context: str
#     sources: List[Dict]

#     def system_prompt(self) -> str:
#         return f"""
#         You are SmartScholar, an AI that provides overviews of topics.
#         Answer the query in a structured, easy-to-understand manner.
#         Cite sources like [Source X].

#         Context:
#         {self.context}

#         Sources:
#         {self.sources}

#         Query: {self.query}
#         Answer:
#         """


# # Agents WITHOUT Retrieval (No Context & Sources)
# @agent
# class FactualAgentNoRetrieval(QueryAgent):
#     def system_prompt(self) -> str:
#         return f"""
#         You are SmartScholar, an AI study assistant. Provide a factual answer based on your knowledge.
#         Answer directly and concisely.

#         Query: {self.query}
#         Answer:
#         """


# @agent
# class ExplanatoryAgentNoRetrieval(QueryAgent):
#     def system_prompt(self) -> str:
#         return f"""
#         You are SmartScholar, an AI that explains concepts step-by-step.
#         Provide a structured response with clear explanations.

#         Query: {self.query}
#         Answer:
#         """


# @agent
# class TechnicalAgentNoRetrieval(QueryAgent):
#     def system_prompt(self) -> str:
#         return f"""
#         You are SmartScholar, an AI study assistant with expertise in technical subjects.
#         Provide a structured, detailed response.

#         Query: {self.query}
#         Answer:
#         """


# @agent
# class ConceptualAgentNoRetrieval(QueryAgent):
#     def system_prompt(self) -> str:
#         return f"""
#         You are SmartScholar, an AI tutor that simplifies complex concepts.
#         Use engaging explanations and analogies.

#         Query: {self.query}
#         Answer:
#         """


# @agent
# class GeneralAgentNoRetrieval(QueryAgent):
#     def system_prompt(self) -> str:
#         return f"""
#         You are SmartScholar, an AI that provides general information and overviews.
#         Answer in an easy-to-understand and structured manner.

#         Query: {self.query}
#         Answer:
#         """


# class Generator:
#     """
#     Main Generator class that selects the appropriate agent based on query intent.
#     """
#     retrieval_agents = {
#         "factual": FactualAgent,
#         "explanatory": ExplanatoryAgent,
#         "technical": TechnicalAgent,
#         "conceptual": ConceptualAgent,
#         "general": GeneralAgent,
#     }

#     non_retrieval_agents = {
#         "factual": FactualAgentNoRetrieval,
#         "explanatory": ExplanatoryAgentNoRetrieval,
#         "technical": TechnicalAgentNoRetrieval,
#         "conceptual": ConceptualAgentNoRetrieval,
#         "general": GeneralAgentNoRetrieval,
#     }

#     def __init__(self):
#         self.model = genai.GenerativeModel("gemini-1.5-pro")

#     def generate_with_retrieval(self, query: str, intent: QueryIntent, context: str, sources: List[Dict]) -> Dict:
#         """
#         Generates response using retrieval-based agents. Requires context and sources.
#         """
#         if not context or not sources:
#             return {"error": "Retrieval mode requires both context and sources."}

#         AgentClass = self.retrieval_agents.get(intent, GeneralAgent)
#         agent_instance = AgentClass(query=query, context=context, sources=sources)
#         return agent_instance.generate_response()

#     def generate_without_retrieval(self, query: str, intent: QueryIntent) -> Dict:
#         """
#         Generates response using non-retrieval agents (only uses query).
#         """
#         AgentClass = self.non_retrieval_agents.get(intent, GeneralAgentNoRetrieval)
#         agent_instance = AgentClass(query=query)
#         return agent_instance.generate_response()


# if __name__ == "__main__":
#     generator = Generator()

#     # Example with Retrieval (Requires Context & Sources)
#     augmented = {
#         "query": "What is YouTube's history?",
#         "context": "YouTube, founded in 2005, has become the world's largest video-sharing platform...",
#         "sources": [
#             {"document_id": "new.txt", "chunk_order": 1, "original_score": 0.62, "rerank_score": 2.82},
#             {"document_id": "new.txt", "chunk_order": 0, "original_score": 0.42, "rerank_score": -11.01}
#         ],
#     }

#     result_with_retrieval = generator.generate_with_retrieval(
#         query=augmented["query"], intent="factual", context=augmented["context"], sources=augmented["sources"]
#     )
#     print("With Retrieval:\n", result_with_retrieval)

#     # Example without Retrieval (Only Query)
#     result_without_retrieval = generator.generate_without_retrieval(
#         query="Explain quantum entanglement.", intent="conceptual"
#     )
#     print("\nWithout Retrieval:\n", result_without_retrieval)


###############################################################################################################################
###############################################################################################################################
###############################################################################################################################






import os
from typing import List, Dict, Literal
from dotenv import load_dotenv
import google.generativeai as genai
from pydantic import BaseModel


# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"), transport="rest")

# Define supported query intents
QueryIntent = Literal["factual", "explanatory", "technical", "conceptual", "general"]


class QueryAgent(BaseModel):
    """
    Base class for all agents handling different query intents.
    """
    query: str

    def system_prompt(self) -> str:
        raise NotImplementedError("Subclasses must implement system_prompt()")

    def generate_response(self) -> Dict:
        """
        Generates a response using Gemini 1.5 Pro based on the query intent.
        """
        prompt = self.system_prompt()
        model = genai.GenerativeModel("gemini-1.5-pro")

        try:
            response = model.generate_content(prompt)
            return {
                "query": self.query,
                "answer": response.text,
                "token_count": response.usage_metadata.total_token_count,
            }
        except Exception as e:
            return {"query": self.query, "error": f"Generation failed: {str(e)}"}


# Agents WITH Retrieval (Requires Context & Sources)
class FactualAgent(QueryAgent):
    context: str
    sources: List[Dict]

    def system_prompt(self) -> str:
        return f"""
        You are SmartScholar, an AI study assistant. Answer the query with factual accuracy.
        Cite sources in the format [Source X] where X is the document_id.

        Context:
        {self.context}

        Sources:
        {self.sources}

        Query: {self.query}
        Answer:
        """


class ExplanatoryAgent(QueryAgent):
    context: str
    sources: List[Dict]

    def system_prompt(self) -> str:
        return f"""
        You are SmartScholar, an AI that explains concepts step-by-step.
        Provide a structured response with examples where necessary.
        Cite sources like [Source X].

        Context:
        {self.context}

        Sources:
        {self.sources}

        Query: {self.query}
        Answer:
        """


class TechnicalAgent(QueryAgent):
    context: str
    sources: List[Dict]

    def system_prompt(self) -> str:
        return f"""
        You are SmartScholar, an AI study assistant with expertise in technical subjects.
        Provide a structured, precise response using markdown for formatting (if needed).
        Cite sources like [Source X].

        Context:
        {self.context}

        Sources:
        {self.sources}

        Query: {self.query}
        Answer:
        """


class ConceptualAgent(QueryAgent):
    context: str
    sources: List[Dict]

    def system_prompt(self) -> str:
        return f"""
        You are SmartScholar, an AI tutor that explains complex concepts using analogies and intuition.
        Provide a clear, engaging answer that simplifies the topic.
        Cite sources like [Source X].

        Context:
        {self.context}

        Sources:
        {self.sources}

        Query: {self.query}
        Answer:
        """


class GeneralAgent(QueryAgent):
    context: str
    sources: List[Dict]

    def system_prompt(self) -> str:
        return f"""
        You are SmartScholar, an AI that provides overviews of topics.
        Answer the query in a structured, easy-to-understand manner.
        Cite sources like [Source X].

        Context:
        {self.context}

        Sources:
        {self.sources}

        Query: {self.query}
        Answer:
        """

# Agents WITHOUT Retrieval (No Context & Sources)
class FactualAgentNoRetrieval(QueryAgent):
    def system_prompt(self) -> str:
        return f"""
        You are SmartScholar, an AI study assistant. Provide a factual answer based on your knowledge.
        Answer directly and concisely.

        Query: {self.query}
        Answer:
        """

class ExplanatoryAgentNoRetrieval(QueryAgent):
    def system_prompt(self) -> str:
        return f"""
        You are SmartScholar, an AI that explains concepts step-by-step.
        Provide a structured response with clear explanations.

        Query: {self.query}
        Answer:
        """

class TechnicalAgentNoRetrieval(QueryAgent):
    def system_prompt(self) -> str:
        return f"""
        You are SmartScholar, an AI study assistant with expertise in technical subjects.
        Provide a structured, detailed response.

        Query: {self.query}
        Answer:
        """

class ConceptualAgentNoRetrieval(QueryAgent):
    def system_prompt(self) -> str:
        return f"""
        You are SmartScholar, an AI tutor that simplifies complex concepts.
        Use engaging explanations and analogies.

        Query: {self.query}
        Answer:
        """


class GeneralAgentNoRetrieval(QueryAgent):
    def system_prompt(self) -> str:
        return f"""
        You are SmartScholar, an AI that provides general information and overviews.
        Answer in an easy-to-understand and structured manner.

        Query: {self.query}
        Answer:
        """


class Generator:
    """
    Main Generator class that selects the appropriate agent based on query intent.
    """
    retrieval_agents = {
        "factual": FactualAgent,
        "explanatory": ExplanatoryAgent,
        "technical": TechnicalAgent,
        "conceptual": ConceptualAgent,
        "general": GeneralAgent,
    }

    non_retrieval_agents = {
        "factual": FactualAgentNoRetrieval,
        "explanatory": ExplanatoryAgentNoRetrieval,
        "technical": TechnicalAgentNoRetrieval,
        "conceptual": ConceptualAgentNoRetrieval,
        "general": GeneralAgentNoRetrieval,
    }

    def __init__(self):
        self.model = genai.GenerativeModel("gemini-2.0-flash")

    def generate_with_retrieval(self, query: str, intent: QueryIntent, context: str, sources: List[Dict]) -> Dict:
        """
        Generates response using retrieval-based agents. Requires context and sources.
        """
        if not context or not sources:
            return {"error": "Retrieval mode requires both context and sources."}

        AgentClass = self.retrieval_agents.get(intent, GeneralAgent)
        agent_instance = AgentClass(query=query, context=context, sources=sources)
        return agent_instance.generate_response()

    def generate_without_retrieval(self, query: str, intent: QueryIntent) -> Dict:
        """
        Generates response using non-retrieval agents (only uses query).
        """
        AgentClass = self.non_retrieval_agents.get(intent, GeneralAgentNoRetrieval)
        agent_instance = AgentClass(query=query)
        return agent_instance.generate_response()


if __name__ == "__main__":
    generator = Generator()

    # Example with Retrieval (Requires Context & Sources)
    augmented = {
        "query": "What is YouTube's history?",
        "context": "YouTube, founded in 2005, has become the world's largest video-sharing platform...",
        "sources": [
            {"document_id": "new.txt", "chunk_order": 1, "original_score": 0.62, "rerank_score": 2.82},
            {"document_id": "new.txt", "chunk_order": 0, "original_score": 0.42, "rerank_score": -11.01}
        ],
    }

    result_with_retrieval = generator.generate_with_retrieval(
        query=augmented["query"], intent="factual", context=augmented["context"], sources=augmented["sources"]
    )
    print("With Retrieval:\n", result_with_retrieval)

    # Example without Retrieval (Only Query)
    result_without_retrieval = generator.generate_without_retrieval(
        query="Explain quantum entanglement.", intent="conceptual"
    )
    print("\nWithout Retrieval:\n", result_without_retrieval)