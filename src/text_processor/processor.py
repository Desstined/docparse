from typing import List, Optional
import re
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from langdetect import detect
import spacy
from spacy.language import Language

from src.config import settings

class TextProcessor:
    def __init__(self):
        # Download required NLTK data
        nltk.download('punkt')
        nltk.download('stopwords')
        nltk.download('averaged_perceptron_tagger')
        
        # Initialize spaCy
        self.nlp = spacy.load('en_core_web_sm')
        
        # Configuration
        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP
        self.max_chunks = settings.MAX_CHUNKS_PER_DOCUMENT

    def clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters and extra whitespace
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        # Remove numbers
        text = re.sub(r'\d+', '', text)
        
        return text.strip()

    def detect_language(self, text: str) -> str:
        """Detect the language of the text."""
        try:
            return detect(text)
        except:
            return 'en'  # Default to English if detection fails

    def chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks."""
        # Clean the text first
        text = self.clean_text(text)
        
        # Split into sentences
        sentences = sent_tokenize(text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence.split())
            
            # If adding this sentence would exceed chunk size
            if current_length + sentence_length > self.chunk_size:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                    # Keep some sentences for overlap
                    overlap_sentences = []
                    overlap_length = 0
                    for sent in reversed(current_chunk):
                        sent_length = len(sent.split())
                        if overlap_length + sent_length > self.chunk_overlap:
                            break
                        overlap_sentences.insert(0, sent)
                        overlap_length += sent_length
                    current_chunk = overlap_sentences
                    current_length = overlap_length
            
            current_chunk.append(sentence)
            current_length += sentence_length
            
            # Check if we've reached max chunks
            if len(chunks) >= self.max_chunks:
                break
        
        # Add the last chunk if it exists
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks

    def extract_entities(self, text: str) -> List[dict]:
        """Extract named entities from text using spaCy."""
        doc = self.nlp(text)
        entities = []
        
        for ent in doc.ents:
            entities.append({
                'text': ent.text,
                'label': ent.label_,
                'start': ent.start_char,
                'end': ent.end_char
            })
        
        return entities

    def get_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """Extract keywords from text using spaCy."""
        doc = self.nlp(text)
        
        # Get noun phrases and named entities
        keywords = []
        
        # Add noun phrases
        for chunk in doc.noun_chunks:
            keywords.append(chunk.text)
        
        # Add named entities
        for ent in doc.ents:
            keywords.append(ent.text)
        
        # Remove duplicates and sort by frequency
        keyword_freq = {}
        for keyword in keywords:
            keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1
        
        # Sort by frequency and get top N
        sorted_keywords = sorted(
            keyword_freq.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [keyword for keyword, _ in sorted_keywords[:top_n]]

    def get_summary(self, text: str, sentences: int = 5) -> str:
        """Generate a simple extractive summary of the text."""
        doc = self.nlp(text)
        
        # Score sentences based on word frequency
        sentence_scores = {}
        word_freq = {}
        
        # Calculate word frequencies
        for word in doc:
            if not word.is_stop and not word.is_punct:
                word_freq[word.text] = word_freq.get(word.text, 0) + 1
        
        # Score sentences
        for sent in doc.sents:
            for word in sent:
                if word.text in word_freq:
                    sentence_scores[sent] = sentence_scores.get(sent, 0) + word_freq[word.text]
        
        # Get top sentences
        summary_sentences = sorted(
            sentence_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:sentences]
        
        # Sort sentences by their original order
        summary_sentences.sort(key=lambda x: x[0].start)
        
        return ' '.join([sent.text for sent, _ in summary_sentences]) 