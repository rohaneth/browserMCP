# 04: Each AI Algorithm From First Principles

This document explains the mathematical foundations and intuitive mechanics of each algorithm used in the repository from zero, complete with small numerical examples.

---

## 1. TF-IDF (Term Frequency - Inverse Document Frequency)
*Used in `apps/api/services/classifier.py` and `services/clustering.py`.*

### Intuitive Problem
If the word *"the"* appears 50 times in a document, it is meaningless. If the word *"kubernetes"* appears 5 times, it strongly signals the topic. TF-IDF gives high weight to words that appear frequently in a specific document but rarely across all documents.

### Mathematical Formulation
1. **Term Frequency (TF)**:
   $$\text{TF}(t, d) = \frac{\text{count of } t \text{ in } d}{\text{total words in } d}$$
   *(In our classifier, we use sublinear TF: $\text{TF}_{\text{sublinear}} = 1 + \ln(\text{count})$ if count > 0).*
2. **Inverse Document Frequency (IDF)**:
   $$\text{IDF}(t, D) = \ln\left(\frac{1 + |D|}{1 + \text{count of documents containing } t}\right) + 1$$
3. **TF-IDF Weight**:
   $$\text{TF-IDF}(t, d, D) = \text{TF}(t, d) \times \text{IDF}(t, D)$$

### Concrete Example
- Total Documents $|D| = 100$.
- Document $d_1$: *"python fast api endpoints stackoverflow error"* (6 words).
- Word A: *"python"* appears in 10 documents out of 100.
  - $\text{TF} = 1/6 \approx 0.167$
  - $\text{IDF} = \ln(101 / 11) + 1 = \ln(9.18) + 1 = 2.21 + 1 = 3.21$
  - $\text{TF-IDF} = 0.167 \times 3.21 = \mathbf{0.536}$
- Word B: *"the"* appears in 98 documents out of 100.
  - $\text{IDF} = \ln(101 / 99) + 1 = 0.02 + 1 = 1.02$
  - $\text{TF-IDF} = 0.167 \times 1.02 = \mathbf{0.170}$
- Result: *"python"* receives $3.15\times$ more importance than *"the"*.

---

## 2. Multinomial Naive Bayes
*Used in `apps/api/services/classifier.py`.*

### Intuitive Problem
Given a vector of word counts/TF-IDF weights $\vec{x}$, calculate the probability that the document belongs to category $C_k$ (e.g. `programming/development` vs `entertainment`).

### Mathematical Formulation
Using Bayes' Theorem:
$$P(C_k \mid \vec{x}) = \frac{P(C_k) \prod_{i=1}^n P(x_i \mid C_k)}{P(\vec{x})}$$
Taking logs to prevent floating-point underflow:
$$\log P(C_k \mid \vec{x}) \propto \log P(C_k) + \sum_{i=1}^n x_i \log P(w_i \mid C_k)$$
Where Laplace smoothing with $\alpha = 0.1$ prevents zero probabilities for unseen words:
$$P(w_i \mid C_k) = \frac{\text{Count}(w_i, C_k) + \alpha}{\sum_{w} \text{Count}(w, C_k) + \alpha \cdot |V|}$$

---

## 3. K-Means / MiniBatchKMeans Clustering
*Used in `apps/api/services/clustering.py`.*

### Intuitive Problem
Group $N$ browser event vectors into $K$ topic clusters such that events within the same cluster are semantically similar.

### Mathematical Formulation
Objective: Minimize total Within-Cluster Sum of Squares (Inertia):
$$J = \sum_{j=1}^K \sum_{\vec{x}_i \in S_j} \|\vec{x}_i - \vec{\mu}_j\|^2$$
Where $\vec{\mu}_j$ is the centroid (mean vector) of cluster $S_j$:
$$\vec{\mu}_j = \frac{1}{|S_j|} \sum_{\vec{x} \in S_j} \vec{x}$$

### MiniBatch Optimization
Instead of recalculating centroids over all $N$ vectors in every iteration, MiniBatchKMeans samples small random subsets ($B = 100$ vectors), finds nearest centroids, and performs an incremental gradient update:
$$\vec{\mu}_j \leftarrow (1 - \eta) \vec{\mu}_j + \eta \vec{x}_i$$
Where $\eta = \frac{1}{\text{count}_j}$. This converges dramatically faster on live streams.

---

## 4. Isolation Forest
*Used in `apps/api/services/anomaly_detection.py`.*

### Intuitive Problem
Normal events (e.g., visiting `google.com` at 2 PM on Tuesday) are surrounded by hundreds of similar points in feature space. Anomalous events (e.g., visiting an obscure ad tracking iframe at 3:30 AM with a 500-character input) sit alone in sparse regions.

### Mathematical Formulation
1. Construct an ensemble of $t$ randomized Isolation Trees ($iTrees$).
2. For each tree, recursively split data by picking a random feature $q$ and a random split value $p$ between $\min(q)$ and $\max(q)$ until the sample is isolated in a leaf node.
3. Path length $h(x)$ is the number of edges traversed from root to leaf.
4. Average path length $c(n)$ for a dataset of size $n$:
   $$c(n) = 2 \left(\ln(n - 1) + 0.5772156649\right) - \frac{2(n - 1)}{n}$$
5. Anomaly Score:
   $$s(x, n) = 2^{-\frac{E(h(x))}{c(n)}}$$
- If $E(h(x)) \to 0$, $s \to 1$ (Definite Anomaly).
- If $E(h(x)) \to c(n)$, $s \to 0.5$ (Normal instance).

---

## 5. Cosine Similarity & Vector Dot Product
*Used in `services/embeddings.py`, `services/search.py`, `services/reranker.py`, and `services/recommendation.py`.*

### Intuitive Problem
Compute the geometric angle between two normalized semantic vectors $\vec{a}$ and $\vec{b}$, independent of their length.

### Mathematical Formulation
$$\text{Cosine Similarity}(\vec{a}, \vec{b}) = \frac{\vec{a} \cdot \vec{b}}{\|\vec{a}\|_2 \|\vec{b}\|_2} = \frac{\sum_{i=1}^d a_i b_i}{\sqrt{\sum_{i=1}^d a_i^2} \sqrt{\sum_{i=1}^d b_i^2}}$$
When vectors are pre-normalized to unit length ($\|\vec{a}\|_2 = 1$), cosine similarity simplifies directly to the inner product:
$$\text{Cosine Similarity}(\vec{a}, \vec{b}) = \vec{a} \cdot \vec{b} = \sum_{i=1}^d a_i b_i$$

### Numerical Example
- Query vector $\vec{q} = [0.6, 0.8]$ (Length = $\sqrt{0.36 + 0.64} = 1.0$)
- Candidate A $\vec{c}_1 = [0.6, 0.8]$ ➔ $\text{Sim} = (0.6)(0.6) + (0.8)(0.8) = \mathbf{1.0}$ (Identical meaning).
- Candidate B $\vec{c}_2 = [0.8, -0.6]$ ➔ $\text{Sim} = (0.6)(0.8) + (0.8)(-0.6) = 0.48 - 0.48 = \mathbf{0.0}$ (Orthogonal / Unrelated).

---

## 6. Reciprocal Rank Fusion (RRF)
*Used in `apps/api/services/search.py`.*

### Intuitive Problem
How do you merge two ranked lists from completely different scoring algorithms (e.g. Keyword BM25 score ranging from $0 - 45$ vs Semantic Cosine ranging from $0.0 - 1.0$) without delicate manual coefficient tuning?

### Mathematical Formulation
$$\text{RRF Score}(d) = \sum_{m \in M} \frac{1}{k + r_m(d)}$$
Where:
- $M$ is the set of retrieval systems (e.g., Keyword Search, Vector Search).
- $r_m(d)$ is the 1-indexed rank position of document $d$ in system $m$.
- $k$ is the smoothing constant (set to $k = 60$ in research literature and our code).

### Numerical Example
- Document $X$ ranks #1 in Keyword Search ($r_1 = 1$) and #10 in Vector Search ($r_2 = 10$).
  $$\text{Score}(X) = \frac{1}{60 + 1} + \frac{1}{60 + 10} = \frac{1}{61} + \frac{1}{70} = 0.01639 + 0.01428 = \mathbf{0.03067}$$
- Document $Y$ ranks #3 in Keyword Search ($r_1 = 3$) and #3 in Vector Search ($r_2 = 3$).
  $$\text{Score}(Y) = \frac{1}{60 + 3} + \frac{1}{60 + 3} = \frac{1}{63} + \frac{1}{63} = 0.01587 + 0.01587 = \mathbf{0.03174}$$
- Result: Document $Y$ (consistently high in both) wins over Document $X$ (high in one, low in the other).
