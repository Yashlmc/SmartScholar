import os
from typing import List, Dict, Literal
from pydantic import BaseModel
import ollama


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
        Generates a response using the LLaMA model via Ollama.
        """
        prompt = self.system_prompt()

        try:
            response = ollama.chat(
                model='phi',
                messages=[
                    {"role": "system", "content": "You are SmartScholar, an intelligent AI assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            return {
                "query": self.query,
                "answer": response['message']['content'],
                "model": "phi"
            }
        except Exception as e:
            return {"query": self.query, "error": f"Generation failed: {str(e)}"}


# Agents WITH Retrieval (Requires Context & Sources)
class FactualAgent(QueryAgent):
    context: str
    sources: List[Dict]

    def system_prompt(self) -> str:
        return f"""Answer the query with factual accuracy and cite sources in the format [Source X].

Context:
{self.context}

Sources:
{self.sources}

Query: {self.query}
Answer:"""


class ExplanatoryAgent(QueryAgent):
    context: str
    sources: List[Dict]

    def system_prompt(self) -> str:
        return f"""Explain the concept step-by-step and provide examples. Cite sources like [Source X].

Context:
{self.context}

Sources:
{self.sources}

Query: {self.query}
Answer:"""


class TechnicalAgent(QueryAgent):
    context: str
    sources: List[Dict]

    def system_prompt(self) -> str:
        return f"""Provide a structured, precise technical response. Use markdown formatting. Cite sources like [Source X].

Context:
{self.context}

Sources:
{self.sources}

Query: {self.query}
Answer:"""


class ConceptualAgent(QueryAgent):
    context: str
    sources: List[Dict]

    def system_prompt(self) -> str:
        return f"""Explain the complex concept using analogies and intuitive reasoning. Cite sources like [Source X].

Context:
{self.context}

Sources:
{self.sources}

Query: {self.query}
Answer:"""


class GeneralAgent(QueryAgent):
    context: str
    sources: List[Dict]

    def system_prompt(self) -> str:
        return f"""Provide a general overview in a clear and structured way. Cite sources like [Source X].

Context:
{self.context}

Sources:
{self.sources}

Query: {self.query}
Answer:"""


# Agents WITHOUT Retrieval
class FactualAgentNoRetrieval(QueryAgent):
    def system_prompt(self) -> str:
        return f"""Provide a factual answer based on your knowledge.

Query: {self.query}
Answer:"""


class ExplanatoryAgentNoRetrieval(QueryAgent):
    def system_prompt(self) -> str:
        return f"""Explain the concept step-by-step in a clear manner.

Query: {self.query}
Answer:"""


class TechnicalAgentNoRetrieval(QueryAgent):
    def system_prompt(self) -> str:
        return f"""Provide a structured and detailed technical explanation.

Query: {self.query}
Answer:"""


class ConceptualAgentNoRetrieval(QueryAgent):
    def system_prompt(self) -> str:
        return f"""Explain the concept using analogies and simple reasoning.

Query: {self.query}
Answer:"""


class GeneralAgentNoRetrieval(QueryAgent):
    def system_prompt(self) -> str:
        return f"""Give a general, easy-to-understand overview.

Query: {self.query}
Answer:"""


class Generator:
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

    def generate_with_retrieval(self, query: str, intent: QueryIntent, context: str, sources: List[Dict]) -> Dict:
        if not context or not sources:
            return {"error": "Retrieval mode requires both context and sources."}
        AgentClass = self.retrieval_agents.get(intent, GeneralAgent)
        return AgentClass(query=query, context=context, sources=sources).generate_response()

    def generate_without_retrieval(self, query: str, intent: QueryIntent) -> Dict:
        AgentClass = self.non_retrieval_agents.get(intent, GeneralAgentNoRetrieval)
        return AgentClass(query=query).generate_response()


if __name__ == "__main__":
    generator = Generator()

    # With Retrieval
    augmented = {
        "query": "What is YouTube's history?",
        "context": "YouTube, founded in 2005, has become the world's largest video-sharing platform...",
        "sources": [
            {"document_id": "new.txt", "chunk_order": 1, "original_score": 0.62, "rerank_score": 2.82},
            {"document_id": "new.txt", "chunk_order": 0, "original_score": 0.42, "rerank_score": -11.01}
        ],
    }

    print("With Retrieval:\n", generator.generate_with_retrieval(
        query=augmented["query"],
        intent="factual",
        context=augmented["context"],
        sources=augmented["sources"]
    ))

    # Without Retrieval
    print("\nWithout Retrieval:\n", generator.generate_without_retrieval(
        query="Explain quantum entanglement.",
        intent="conceptual"
    ))
