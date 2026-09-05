# 12: Applied AI & System Glossary

A comprehensive, beginner-friendly dictionary of all technical terms used across this project.

---

- **Model Context Protocol (MCP)**: An open JSON-RPC standard defined by Anthropic enabling AI clients to discover, inspect, and invoke local tools, data stores, and computational routines over standard input/output (`stdio`) or SSE.
- **Embedding (Vector)**: A fixed-length list of floating-point numbers (e.g. 384 dimensions) representing the semantic meaning of a text string in multidimensional space.
- **Cosine Similarity**: A mathematical metric evaluating the cosine of the angle between two vectors, measuring directional alignment regardless of vector magnitude (ranges from $-1.0$ to $+1.0$).
- **Reciprocal Rank Fusion (RRF)**: An information retrieval fusion algorithm that merges ranked lists from multiple search systems by summing inverse ordinal ranks ($\frac{1}{k + \text{rank}}$).
- **RAG (Retrieval-Augmented Generation)**: The architecture of enhancing an LLM prompt with relevant records retrieved from a local database before generating an answer.
- **Reranker**: A scoring component that re-evaluates a small pool of candidate documents from initial retrieval to improve precision at the top ranks.
- **Bi-Encoder**: An embedding architecture where queries and documents are embedded into dense vectors independently, allowing fast dot-product comparisons.
- **Cross-Encoder**: An attention architecture where query and document are passed through a transformer together, allowing full cross-attention at the cost of higher latency.
- **Multinomial Naive Bayes**: A probabilistic supervised classifier based on Bayes' Theorem with the assumption that features (word occurrences) are conditionally independent given the class label.
- **TF-IDF (Term Frequency-Inverse Document Frequency)**: A statistical feature weighting scheme that scales word frequencies by how rare they are across the entire document corpus.
- **K-Means Clustering**: An unsupervised partitioning algorithm that clusters $N$ vector points into $K$ clusters by iteratively minimizing the sum of squared distances to cluster centroids.
- **MiniBatchKMeans**: A fast variant of K-Means that performs updates using small, randomly sampled batches of vectors instead of the entire dataset.
- **Isolation Forest**: An unsupervised anomaly detection algorithm that isolates outliers using randomized binary decision trees.
- **Grounding**: Constraining an AI model's answers strictly to verifiable facts present in the provided reference context.
- **Hallucination**: When a generative language model outputs a statement that is unsupported by or contradicts the source evidence.
- **Levenshtein Distance**: The minimum number of single-character edits (insertions, deletions, substitutions) required to transform one string into another.
- **Sessionization**: Grouping timestamped interaction events into discrete user sessions based on an inactivity timeout threshold.
