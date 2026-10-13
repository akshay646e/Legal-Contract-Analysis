from typing import Dict, Any, List
from app.rag.vector_store import vector_store
from app.services.llm_factory import LLMFactory, MockLLMService
from app.config import settings
from app.core.logging import logger

RAG_QA_SYSTEM_PROMPT = """
You are an expert Legal Assistant specializing in Contract Review and Due Diligence.
Your task is to answer the user's question about the contract based STRICTLY on the retrieved context excerpts provided below.

Rules:
1. Ground your answer completely in the provided contract excerpts.
2. Quote relevant phrasing directly where helpful to assure legal certainty.
3. If the provided excerpts do not contain sufficient information to answer the question, clearly state: "The retrieved contract sections do not contain specific terms addressing this question." Do NOT hallucinate.
4. Keep the explanation professional, precise, and practical for legal/business decision-makers.
"""

class ContractQAService:
    @classmethod
    def ask(cls, contract_id: str, question: str) -> Dict[str, Any]:
        """
        Executes grounded legal RAG Q&A:
        1. Retrieves top-k semantically relevant contract chunks from the vector store.
        2. Formulates grounded prompt with retrieved excerpts.
        3. Calls LLM with temperature=0.0 to prevent hallucination.
        4. Extracts and returns citations with exact section references and quotes.
        """
        logger.info(f"Querying contract [yellow]{contract_id}[/yellow]: [cyan]{question}[/cyan]")
        
        # 1. Retrieve top chunks for this contract
        retrieved_chunks = vector_store.similarity_search(
            contract_id=contract_id,
            query=question,
            k=4
        )

        provider = LLMFactory.get_provider()
        if provider == "mock":
            return MockLLMService.answer_question(question, retrieved_chunks)

        client = LLMFactory.get_client()
        if not client:
            return MockLLMService.answer_question(question, retrieved_chunks)

        try:
            # Build context snippet from retrieved chunks
            context_blocks = []
            citations = []

            for idx, c in enumerate(retrieved_chunks):
                sec_header = f"Section {c.get('section_number', '')} ({c.get('section_title', 'Untitled')})"
                text = c.get("text", "")
                context_blocks.append(f"--- Context Excerpt {idx + 1} [{sec_header}] ---\n{text}")

                citations.append({
                    "section_number": c.get("section_number", ""),
                    "section_title": c.get("section_title", "Contract Excerpt"),
                    "page_number": c.get("page_number", 1),
                    "verbatim_quote": text[:280] + ("..." if len(text) > 280 else ""),
                    "relevance_score": c.get("score", 0.90)
                })

            combined_context = "\n\n".join(context_blocks)

            user_prompt = f"""
Retrieved Contract Context:
{combined_context}

User Question:
{question}

Provide your grounded legal analysis and answer:
"""

            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL_NAME,
                temperature=0.0, # Zero temperature for maximum factual grounding
                messages=[
                    {"role": "system", "content": RAG_QA_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ]
            )

            reply_text = response.choices[0].message.content

            return {
                "reply": reply_text,
                "citations": citations
            }
        except Exception as e:
            logger.error(f"OpenAI RAG query failed ({e}). Falling back to heuristic mock.")
            return MockLLMService.answer_question(question, retrieved_chunks)
