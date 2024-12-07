from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


# TODO revise comments
class SemanticSearch:
    def __init__(self):
        # Load the Sentence-BERT model for semantic search
        # self._model = SentenceTransformer('all-MiniLM-L6-v2')  # A fast, lightweight model
        self._model = SentenceTransformer('all-MiniLM-L12-v2')

    # Function to encode text into embeddings
    def _encode_text(self, text_list):
        return self._model.encode(text_list)

    # Function to calculate cosine similarity and retrieve most relevant context
    def _retrieve_most_relevant_context(self, query, context_documents):
        query_embedding = self._encode_text([query])  # Encode the query into embedding
        context_embeddings = self._encode_text(context_documents)  # Encode the context documents

        # Calculate cosine similarity between the query embedding and context embeddings
        similarities = cosine_similarity(query_embedding, context_embeddings)

        # Find the index of the most similar context
        most_similar_idx = similarities.argmax()

        # Return the most relevant context
        return context_documents[most_similar_idx]

    def get_similar_cheatsheet(self, query, context_documents):
        relevant_context = self._retrieve_most_relevant_context(query, context_documents)
        return relevant_context
