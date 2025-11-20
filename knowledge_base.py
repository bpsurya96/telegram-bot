"""
Knowledge Base Module
Manages document storage and retrieval
"""

DOCUMENTS = [
    {
        "id": "python_intro",
        "title": "Python Programming Basics",
        "content": """
Python is a high-level, interpreted programming language created by Guido van Rossum 
and first released in 1991. It emphasizes code readability with significant indentation. 
Python supports multiple programming paradigms including procedural, object-oriented, 
and functional programming.
""",
        "metadata": {"source": "python_basics.md", "category": "programming"}
    },
    {
        "id": "python_uses",
        "title": "Python Applications",
        "content": """
Python is widely used in various domains: web development (Django, Flask), data science 
(pandas, NumPy), machine learning (TensorFlow, PyTorch, scikit-learn), automation and 
scripting, scientific computing, game development, and desktop applications. Its extensive 
standard library and third-party packages make it versatile for almost any task.
""",
        "metadata": {"source": "python_basics.md", "category": "programming"}
    },
    {
        "id": "ml_intro",
        "title": "Machine Learning Introduction",
        "content": """
Machine learning is a subset of artificial intelligence that enables systems to learn 
and improve from experience without being explicitly programmed. It focuses on developing 
algorithms that can access data and use it to learn for themselves. Common types include 
supervised learning, unsupervised learning, and reinforcement learning.
""",
        "metadata": {"source": "ml_intro.md", "category": "ai"}
    },
    {
        "id": "ml_algorithms",
        "title": "Common ML Algorithms",
        "content": """
Popular machine learning algorithms include: Linear Regression for prediction, 
Decision Trees for classification, Random Forests for ensemble learning, 
Support Vector Machines (SVM) for classification, K-Means for clustering, 
and Neural Networks for deep learning. Each algorithm has specific use cases 
and performance characteristics.
""",
        "metadata": {"source": "ml_intro.md", "category": "ai"}
    },
    {
        "id": "deep_learning",
        "title": "Deep Learning Overview",
        "content": """
Deep learning uses artificial neural networks with multiple layers (deep networks) 
to progressively extract higher-level features from raw input. Popular frameworks 
include TensorFlow, PyTorch, and Keras. Applications include computer vision 
(image classification, object detection), natural language processing (chatbots, 
translation), speech recognition, and game playing (AlphaGo).
""",
        "metadata": {"source": "ml_intro.md", "category": "ai"}
    },
    {
        "id": "docker_intro",
        "title": "Docker Containerization",
        "content": """
Docker is a platform for developing, shipping, and running applications in containers. 
Containers package software with all its dependencies, ensuring consistency across 
different environments. Docker uses OS-level virtualization to deliver software in 
packages called containers, which are isolated from one another and bundle their 
own software, libraries, and configuration files.
""",
        "metadata": {"source": "devops.md", "category": "infrastructure"}
    },
    {
        "id": "docker_benefits",
        "title": "Benefits of Docker",
        "content": """
Key benefits of Docker include: Portability (run anywhere), Consistency (same environment 
in dev/staging/prod), Isolation (containers don't interfere with each other), 
Efficiency (lightweight compared to VMs), Scalability (easy to scale up/down), 
Version control (track container images), and Rapid deployment (start containers 
in seconds).
""",
        "metadata": {"source": "devops.md", "category": "infrastructure"}
    },
    {
        "id": "kubernetes_intro",
        "title": "Kubernetes Orchestration",
        "content": """
Kubernetes (K8s) is an open-source container orchestration platform that automates 
deployment, scaling, and management of containerized applications. It groups containers 
into logical units for easy management and discovery. Key concepts include Pods 
(smallest deployable units), Services (network access), Deployments (desired state), 
and Namespaces (virtual clusters).
""",
        "metadata": {"source": "devops.md", "category": "infrastructure"}
    },
    {
        "id": "git_basics",
        "title": "Git Version Control",
        "content": """
Git is a distributed version control system for tracking changes in source code during 
software development. It allows multiple developers to work together on non-linear 
development. Key concepts include: repositories (project storage), commits (snapshots), 
branches (parallel development), merging (combining changes), and remote repositories 
(GitHub, GitLab).
""",
        "metadata": {"source": "git_guide.md", "category": "tools"}
    },
    {
        "id": "rest_api",
        "title": "REST API Design",
        "content": """
REST (Representational State Transfer) is an architectural style for designing networked 
applications. RESTful APIs use HTTP methods: GET (retrieve), POST (create), PUT (update), 
DELETE (remove). Key principles include statelessness, client-server separation, 
cacheability, uniform interface, and layered system. Common formats are JSON and XML.
""",
        "metadata": {"source": "api_design.md", "category": "web"}
    }
]

def get_all_documents():
    """Return all documents in the knowledge base"""
    return DOCUMENTS

def get_document_chunks():
    """
    Split documents into chunks for better retrieval.
    Each chunk is a separate searchable unit.
    """
    chunks = []
    for doc in DOCUMENTS:
        # Simple chunking: each document as one chunk
        # For larger documents, you'd split into paragraphs or sentences
        chunks.append({
            "id": doc["id"],
            "text": f"{doc['title']}\n\n{doc['content'].strip()}",
            "metadata": {
                **doc["metadata"],
                "title": doc["title"]
            }
        })
    return chunks