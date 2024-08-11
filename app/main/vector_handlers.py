
from logging import getLogger
from typing import Any, List
from app.main.settings import getOpenai

import numpy as np

logger = getLogger()
client = getOpenai()


async def create_vector(data):
  if data:
    response = await client.embeddings.create(
      input = data,
      model = "text-embedding-ada-002"
    )

    vectors = [embed.embedding for embed in response.data]
    return vectors if len(vectors) > 1 else vectors[0]
  else:
    return False

def calculate_vector_difference(v1, v2):
    return np.array(v2) - np.array(v1)

# Back End E3
def calculate_momentum(vector_sequence, window_size=2):

    if len(vector_sequence) < 1:
        raise ValueError("Not enough vectors in the sequence")

    recent_vectors = [np.array(v) for v in vector_sequence]

    differences = [calculate_vector_difference(recent_vectors[i], recent_vectors[i+1])
                   for i in range(len(recent_vectors)-1)]

    momentum = np.mean(differences, axis=0)
    return momentum

def predict_next_vector(vector_sequence, window_size=2):
    momentum = calculate_momentum(vector_sequence, window_size)
    last_vector = np.array(vector_sequence[-1])
    return last_vector + momentum

# return k closest vectors
def get_closest_components(components, vectors, target_vector, k: int = 3):
    diffs = [np.linalg.norm(np.array(vector) - np.array(target_vector)) for vector in vectors]
    together = list(zip(diffs, components))
    together.sort(key=lambda x: x[0])
    top_k = [component for (_, component) in together[:k]]

    return top_k

