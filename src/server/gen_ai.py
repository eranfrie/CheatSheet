# needed only if enable_ai is true.
# worst case, fail in runtime
try:
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
except:
    pass


class GenAI:
    def __init__(self):
        # We load the model and tokenizer only when used
        # so that unittests will run faster.
        self._tokenizer = None
        self._model = None

    def _load(self):
        # load pre-trained model and tokenizer
        self._tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-large")
        self._model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-large")

    def generate_answer(self, context, query):
        if self._model is None or self._tokenizer is None:
            self._load()

        input_text = f"Context: {context}\nQuestion: {query}"
        inputs = self._tokenizer(input_text, return_tensors="pt", padding=True, truncation=True)
        outputs = self._model.generate(
            inputs['input_ids'],
            attention_mask=inputs['attention_mask'],
            max_length=500,                          # Increase max_length to allow longer answers
            num_return_sequences=1,                  # Generate only one answer (you can increase this for diversity)
            no_repeat_ngram_size=2,                  # Prevent repetition in long responses
            temperature=0.5,                         # Controls randomness (lower value = more predictable)
            top_k=50,                                # Limit to the top 50 most probable tokens
            top_p=0.95,                              # Use nucleus sampling (top-p) for diversity
            do_sample=True                           # Enables sampling (random generation) instead of greedy
        )

        # decode and clean the generated answer
        answer = self._tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
        # clean up any extra tokens
        answer = answer.replace("<|endoftext|>", "")
        return answer
