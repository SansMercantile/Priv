# backend/ai_core/neural_encoder.py

import numpy as np
from typing import List, Union

# In a real implementation, this would use a library like transformers or tensorflow.
# For this simulation, we'll use a placeholder that generates deterministic vectors.
import hashlib

class NeuralEncoder:
    """
    A placeholder for a sophisticated neural network model (e.g., a Transformer-based model like BERT or GPT)
    that encodes textual and numerical data into high-dimensional vector representations (embeddings).
    These embeddings capture the semantic meaning of the input, allowing for nuanced comparisons and analysis.
    """
    def __init__(self, model_name: str = "simulated_transformer", vector_size: int = 768):
        """
        Initializes the encoder. In a real application, this would load a pre-trained model.
        
        Args:
            model_name (str): The name of the model to load (used for simulation here).
            vector_size (int): The dimensionality of the output vectors.
        """
        self.model_name = model_name
        self.vector_size = vector_size
        print(f"Neural Encoder initialized with simulated model '{self.model_name}' (Vector size: {self.vector_size}).")

    def encode_text(self, text: Union[str, List[str]]) -> np.ndarray:
        """
        Encodes a single string or a list of strings into a vector or a matrix of vectors.
        
        Args:
            text (Union[str, List[str]]): The input text.
            
        Returns:
            np.ndarray: The resulting embedding(s).
        """
        if isinstance(text, str):
            return self._generate_embedding(text)
        elif isinstance(text, list):
            return np.array([self._generate_embedding(t) for t in text])
        else:
            raise TypeError("Input must be a string or a list of strings.")

    def _generate_embedding(self, input_string: str) -> np.ndarray:
        """
        Generates a deterministic, pseudo-random embedding from a string using a hash function.
        This simulates the output of a real neural network for consistent demo purposes.
        """
        # Use SHA-256 to create a deterministic hash from the input string
        hash_object = hashlib.sha256(input_string.encode())
        hex_dig = hash_object.hexdigest()
        
        # Use the hash as a seed for a random number generator
        seed = int(hex_dig, 16) % (2**32)
        rng = np.random.RandomState(seed)
        
        # Generate a random vector and normalize it
        embedding = rng.rand(self.vector_size)
        embedding = (embedding - 0.5) * 2 # Scale to [-1, 1]
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
            
        return embedding

    def calculate_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calculates the cosine similarity between two vectors.
        Values closer to 1 indicate higher similarity.
        
        Args:
            vec1 (np.ndarray): The first vector.
            vec2 (np.ndarray): The second vector.
            
        Returns:
            float: The cosine similarity score.
        """
        vec1 = vec1.flatten()
        vec2 = vec2.flatten()
        
        dot_product = np.dot(vec1, vec2)
        norm_vec1 = np.linalg.norm(vec1)
        norm_vec2 = np.linalg.norm(vec2)
        
        if norm_vec1 == 0 or norm_vec2 == 0:
            return 0.0
            
        return dot_product / (norm_vec1 * norm_vec2)

# Example Usage:
if __name__ == '__main__':
    encoder = NeuralEncoder()

    # Encode single strings
    text1 = "Apple Inc. announced a stock buyback program."
    text2 = "The tech giant Apple will repurchase shares."
    text3 = "The price of oranges has increased due to bad weather."

    embedding1 = encoder.encode_text(text1)
    embedding2 = encoder.encode_text(text2)
    embedding3 = encoder.encode_text(text3)

    print(f"Shape of embedding 1: {embedding1.shape}")
    
    # Calculate similarity
    similarity_1_2 = encoder.calculate_similarity(embedding1, embedding2)
    similarity_1_3 = encoder.calculate_similarity(embedding1, embedding3)

    print(f"Similarity between '{text1}' and '{text2}': {similarity_1_2:.4f}")
    print(f"Similarity between '{text1}' and '{text3}': {similarity_1_3:.4f}")
    
    # Encode a list of strings
    texts = ["US inflation rate rises unexpectedly.", "Federal Reserve considers interest rate hikes.", "New iPhone sales exceed expectations."]
    embeddings_batch = encoder.encode_text(texts)
    print(f"Shape of batch embeddings: {embeddings_batch.shape}")
