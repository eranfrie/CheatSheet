# needed only if enable_ai is true.
# worst case, fail in runtime
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
except:
    pass

class SemanticSearch:
    def __init__(self):
        # load the model on demand just for the tests to run faster
        self._model = None

    def _load_model(self):
        # Other options:
        #    all-MiniLM-L6-v2 - a fast, lightweight model
        self._model = SentenceTransformer('all-MiniLM-L12-v2')

    def _encode_text(self, text_list):
        """Encode text into embedding."""
        if not self._model:
            self._load_model()

        return self._model.encode(text_list)

    def get_similar_cheatsheet(self, query, context_documents):
        if not self._model:
            self._load_model()

        query_embedding = self._encode_text([query])
        context_embeddings = self._encode_text(context_documents)

        similarities = cosine_similarity(query_embedding, context_embeddings)
        most_similar_idx = similarities.argmax()
        return context_documents[most_similar_idx]
