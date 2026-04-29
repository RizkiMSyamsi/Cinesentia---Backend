"""
Text preprocessing pipeline for sentiment analysis.
Mirrors the exact preprocessing used during ML model training.
"""

import re
import string

import nltk
from nltk.corpus import stopwords, wordnet
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

# Download required NLTK resources (idempotent)
nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)
nltk.download("stopwords", quiet=True)
nltk.download("averaged_perceptron_tagger", quiet=True)
nltk.download("averaged_perceptron_tagger_eng", quiet=True)
nltk.download("wordnet", quiet=True)

# Initialize tools
_stop_words = set(stopwords.words("english"))
_lemmatizer = WordNetLemmatizer()

# Important stopwords to keep (negation, intensity, contrast)
_important_stopwords = {
    "not", "no", "nor", "never", "none", "nobody", "nothing", "neither",
    "n't", "don't", "didn't", "doesn't", "won't", "wouldn't", "can't",
    "cannot", "couldn't", "shouldn't", "mustn't", "isn't", "aren't",
    "wasn't", "weren't", "haven't", "hasn't", "hadn't", "without",
    "barely", "hardly", "scarcely", "very", "extremely", "really",
    "so", "too", "quite", "but", "although", "however", "yet",
}
_custom_stop_words = _stop_words - _important_stopwords

# Slang dictionary
_slang_dict = {
    "u": "you", "r": "are", "ur": "your", "btw": "by the way",
    "idk": "i do not know", "lol": "laughing out loud",
    "omg": "oh my god", "lmao": "laughing my ass off",
    "rofl": "rolling on the floor laughing", "brb": "be right back",
    "gtg": "got to go", "imo": "in my opinion", "tbh": "to be honest",
    "smh": "shaking my head", "nvm": "never mind",
    "bff": "best friend forever", "dm": "direct message",
    "ok": "okay", "ya": "yeah", "thx": "thanks", "ty": "thank you",
    "plz": "please", "bc": "because", "cuz": "because",
    "tho": "though", "k": "okay", "luv": "love", "fam": "friends",
    "vibes": "feelings", "im": "i am",
}

# Emoji pattern
_emoji_pattern = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map
    "\U0001F1E0-\U0001F1FF"  # flags
    "]+",
    flags=re.UNICODE,
)


def _get_wordnet_pos(tag):
    """Map POS tag to WordNet POS."""
    if tag.startswith("J"):
        return wordnet.ADJ
    elif tag.startswith("V"):
        return wordnet.VERB
    elif tag.startswith("N"):
        return wordnet.NOUN
    elif tag.startswith("R"):
        return wordnet.ADV
    return wordnet.NOUN


def _cleaning_text(text):
    """Remove emojis, mentions, hashtags, URLs, numbers, punctuation."""
    text = _emoji_pattern.sub(r"", text)
    text = re.sub(r"@[A-Za-z0-9]+", "", text)
    text = re.sub(r"#[A-Za-z0-9]+", "", text)
    text = re.sub(r"RT[\s]", "", text)
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[0-9]+", "", text)
    text = text.translate(str.maketrans("", "", string.punctuation))
    return text.strip()


def _casefolding_text(text):
    """Lowercase and normalize whitespace."""
    return re.sub(r"\s+", " ", text.lower()).strip()


def _standard_slangwords(text):
    """Replace slang words with their standard forms."""
    tokens = word_tokenize(text)
    return " ".join([_slang_dict.get(t.lower(), t) for t in tokens])


def _filtering_text(tokens):
    """Remove custom stop words (preserving negation and intensity words)."""
    return [t for t in tokens if t.lower() not in _custom_stop_words]


def _lemmatization_text(tokens):
    """Lemmatize tokens using POS tags."""
    pos_tags = nltk.pos_tag(tokens)
    return [_lemmatizer.lemmatize(w, _get_wordnet_pos(t)) for w, t in pos_tags]


def preprocess_text(text):
    """
    Full preprocessing pipeline matching the ML training pipeline.
    
    Pipeline: clean → casefold → slang → tokenize → filter → lemmatize → join
    """
    text = _cleaning_text(text)
    text = _casefolding_text(text)
    text = _standard_slangwords(text)
    tokens = word_tokenize(text)
    tokens = _filtering_text(tokens)
    tokens = _lemmatization_text(tokens)
    return " ".join(tokens)
