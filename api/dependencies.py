from config.settings import settings
from services.embeddings import EmbeddingsService
from services.vector_store import VectorStore
from services.document_processor import DocumentProcessor
from services.llm_provider import ClaudeProvider, GeminiProvider, FallbackLLMProvider
from services.orchestrator import Orchestrator
from agents.retriever import RetrieverAgent
from agents.web_researcher import WebResearcherAgent
from agents.synthesizer import SynthesizerAgent

# Singletons
_embeddings: EmbeddingsService | None = None
_vector_store: VectorStore | None = None
_document_processor: DocumentProcessor | None = None
_orchestrator: Orchestrator | None = None


def get_embeddings() -> EmbeddingsService:
    global _embeddings
    if _embeddings is None:
        _embeddings = EmbeddingsService()
    return _embeddings


def get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        embeddings = get_embeddings()
        _vector_store = VectorStore(dimension=embeddings.dimension, index_path=settings.faiss_index_path)
        _vector_store.load()
    return _vector_store


def get_document_processor() -> DocumentProcessor:
    global _document_processor
    if _document_processor is None:
        _document_processor = DocumentProcessor()
    return _document_processor


def get_llm_provider() -> FallbackLLMProvider:
    claude = ClaudeProvider(api_key=settings.anthropic_api_key, model=settings.claude_model)
    gemini = GeminiProvider(api_key=settings.google_api_key, model=settings.gemini_model)

    providers = {"claude": claude, "gemini": gemini}
    primary = providers.get(settings.llm_primary, gemini)
    fallback = providers.get(settings.llm_fallback, claude)
    return FallbackLLMProvider(primary=primary, fallback=fallback)


def get_orchestrator() -> Orchestrator:
    global _orchestrator
    if _orchestrator is None:
        llm = get_llm_provider()
        vs = get_vector_store()
        emb = get_embeddings()

        retriever = RetrieverAgent(llm_provider=llm, vector_store=vs, embeddings_service=emb)
        web_researcher = WebResearcherAgent(llm_provider=llm)
        synthesizer = SynthesizerAgent(llm_provider=llm)

        _orchestrator = Orchestrator(retriever, web_researcher, synthesizer)
    return _orchestrator
