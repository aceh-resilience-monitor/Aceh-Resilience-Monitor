# Sea Labs Bootcamp Application Portfolio & Interview Guide

This document is prepared to help you apply for the **Sea Labs Bootcamp (Sea Group/Shopee)**. It provides professionally written descriptions of your two core software engineering and machine learning projects in both English and Indonesian. It highlights your system design capabilities, backend scalability, and robust machine learning engineering skills.

---

## 📋 Sea Labs Application Form Response

**Application Prompt:**
> *Do you have any experience related to Software Engineering/Programming/Coding? If yes, please provide a short description of your experience (e.g. projects, tech stacks/programming languages you are familiar with, etc).*

---

### 🇬🇧 English Version (Recommended)
> **Note:** Sea Labs operates globally under Sea Group (Shopee). Submit your application in English to stand out as a premium candidate.

Yes, I have extensive hands-on experience in Software Engineering and Machine Learning Engineering, specializing in **MLOps, serverless backend architectures, and advanced natural language processing (NLP)**. I have designed and deployed end-to-end data pipelines and deep learning systems, with a strong focus on clean code, automated testing, and scalable cloud systems.

Here is a summary of my two key engineering projects:

#### 1. ARM (Anomali Reaksi Masyarakat) — MLOps & Serverless Data Pipeline
*   **Role:** ML & Cloud Systems Engineer (Lead)
*   **Tech Stack:** Python, Azure Functions (Serverless), Azure Machine Learning, MLflow, Azure Blob Storage, Node.js (Frontend), Pytest (CI/CD), Git.
*   **System Architecture & Engineering Depth:**
    *   **Serverless Ingestion:** Engineered an event-driven scraping microservice using **Azure Functions** running under a cron scheduler, fetching social media and public reactions, and streaming raw JSON data to **Azure Blob Storage**.
    *   **MLOps Pipeline:** Designed a decoupled training and batch inference pipeline using **Azure Machine Learning Workspace** on GPU/CPU compute clusters, utilizing **MLflow** for model tracking, lineage logging, and automated model registration.
    *   **Decoupled Dashboard:** Built a high-performance frontend using **Node.js/Vanilla JS** deployed via **Azure Static Web Apps**, consuming optimized API streams to render real-time sentiment anomalies.
    *   **Reliability:** Implemented rigorous test-driven development using **Pytest** (covering 70+ integration and unit tests) to guarantee pipeline reliability.

#### 2. UU-ITE Violation Detection — Deep Learning NLP & Adversarial Obfuscation Bypassing
*   **Role:** Lead Machine Learning & Backend Engineer (Undergraduate Thesis Project)
*   **Tech Stack:** Python, PyTorch, TensorFlow/Keras, HuggingFace Transformers, IndoBERT (`indobenchmark/indobert-base-p2`), FastText, Streamlit, Pandas, Regex.
*   **System Architecture & Engineering Depth:**
    *   **Adversarial Preprocessing Pipeline:** Social media comments often contain complex obfuscations to bypass filters (e.g., gambling spams using Cyrillic lookalikes, split letters, and mathematical fonts). I engineered a highly robust **multi-stage normalization pipeline** that resolves visual homoglyphs (e.g., translating Cyrillic `А/С` back to Latin `A/C`), normalizes mathematical fonts (e.g., `𝗕𝗥𝗢𝗪𝗜𝗡` to `BROWIN`), merges split arrays (`ᴡ ᴀ ᴋ ᴀ ᴛ ᴏ` to `wakato`), and maps emojis to semantic tokens. It integrates a custom **~440,000-entry Indonesian slang dictionary** for high-accuracy normalization.
    *   **Sequence Modeling & Transformers:** Implemented and compared two architectures: a **Hybrid CNN-BiLSTM** combining Conv1D (local feature extraction) and Bidirectional LSTMs (temporal sequence modeling) with trainable 300d FastText embeddings, and a fine-tuned **IndoBERT Transformer** (110M params) with custom special tokens injected into the tokenizer.
    *   **Streamlit & Legal Engine:** Deployed an interactive application showcasing real-time token-by-token preprocessing changes and outputting classification probabilities mapped to exact **Indonesian Cyber Law (UU ITE Articles 27 & 28)** references and criminal penalties.

---

### 🇮🇩 Indonesian Version (Bahasa Indonesia)

Ya, saya memiliki pengalaman praktis yang mendalam di bidang Software Engineering dan Machine Learning Engineering, dengan spesialisasi pada **MLOps, arsitektur serverless backend, serta pemrosesan bahasa alami (NLP)**. Saya terbiasa merancang dan menerapkan pipeline data ujung-ke-ujung (end-to-end) serta sistem deep learning berskala besar dengan fokus pada penulisan kode yang bersih, pengujian otomatis, dan skalabilitas sistem cloud.

Berikut adalah ringkasan dari dua proyek rekayasa utama saya:

#### 1. ARM (Anomali Reaksi Masyarakat) — MLOps & Serverless Data Pipeline
*   **Peran:** ML & Cloud Systems Engineer (Lead)
*   **Tech Stack:** Python, Azure Functions (Serverless), Azure Machine Learning, MLflow, Azure Blob Storage, Node.js (Frontend), Pytest (CI/CD), Git.
*   **Arsitektur Sistem & Kedalaman Teknis:**
    *   **Serverless Ingestion:** Membangun microservice scraping berbasis event menggunakan **Azure Functions** yang berjalan otomatis dengan trigger cron, mengumpulkan data reaksi publik dari media sosial, dan menulis data JSON mentah langsung ke **Azure Blob Storage**.
    *   **MLOps Pipeline:** Merancang pipeline pelatihan dan batch inference yang terpisah (decoupled) menggunakan **Azure Machine Learning Workspace** di kluster komputasi GPU/CPU, memanfaatkan **MLflow** untuk pelacakan performa model, pencatatan silsilah data (lineage), serta registrasi model otomatis.
    *   **Decoupled Dashboard:** Membangun frontend berkinerja tinggi menggunakan **Node.js/Vanilla JS** yang di-deploy via **Azure Static Web Apps**, mengonsumsi aliran data JSON yang dioptimalkan untuk menyajikan visualisasi anomali reaksi secara real-time.
    *   **Reliabilitas Pengujian:** Menerapkan pengujian otomatis menggunakan **Pytest** dengan lebih dari 70 skenario unit dan integration testing untuk memastikan keandalan pipeline data secara konsisten.

#### 2. UU-ITE Violation Detection — Deep Learning NLP & Adversarial Obfuscation Bypassing
*   **Peran:** Lead Machine Learning & Backend Engineer (Tugas Akhir S1 Informatika)
*   **Tech Stack:** Python, PyTorch, TensorFlow/Keras, HuggingFace Transformers, IndoBERT (`indobenchmark/indobert-base-p2`), FastText, Streamlit, Pandas, Regex.
*   **Arsitektur Sistem & Kedalaman Teknis:**
    *   **Adversarial Preprocessing Pipeline:** Komentar media sosial sering menggunakan manipulasi karakter untuk menghindari filter sensor otomatis (contoh: spam judi menggunakan huruf Cyrillic lookalike, spasi terpisah, dan font matematika tebal). Saya mengembangkan **multi-stage preprocessing pipeline** berbasis Regex dan Unicode normalizer yang mampu mendeteksi homoglyph visual (menerjemahkan Cyrillic `А/С` kembali ke Latin `A/C`), menormalkan font matematika (contoh: `𝗕𝗥𝗢𝗪𝗜𝗡` menjadi `BROWIN`), menyatukan kata terpisah (`ᴡ ᴀ ᴋ ᴀ ᴛ ᴏ` menjadi `wakato`), serta memetakan emoji menjadi token semantik. Sistem ini terintegrasi dengan **kamus slang kustom berisi ~440.000 entri** untuk normalisasi bahasa gaul Indonesia.
    *   **Sequence Modeling & Transformers:** Mengimplementasikan dan membandingkan dua arsitektur deep learning: **Hybrid CNN-BiLSTM** yang menggabungkan Conv1D (ekstraksi fitur lokal n-gram) dan Bidirectional LSTM (pemodelan konteks urutan kalimat) menggunakan trainable FastText 300d embeddings, serta fine-tuning **IndoBERT Transformer** (110M params) dengan injeksi token khusus (special tokens) pada tokenizer.
    *   **Streamlit & Legal Engine:** Membangun aplikasi demo interaktif menggunakan **Streamlit** untuk menampilkan visualisasi langkah demi langkah proses pembersihan teks secara real-time, serta memetakan hasil prediksi model secara langsung ke pasal hukum cyber terkait (**UU ITE Pasal 27 & 28**) lengkap dengan ancaman pidananya.

---

## 🎯 Key Technical Selling Points (Why Sea Labs Will Love This)

Sea Labs recruiters look for fundamental engineering logic and structural robustness. Here are the core pillars to emphasize in your profile and interview:

1.  **Adversarial Preprocessing (Robust Logic over Simple APIs):**
    *   Standard text classification projects simply run `tokenizer.encode()` and feed it to a model. That fails completely on social media where spammers write `J_u_d_i` or `𝐉𝐮𝐝𝐢`.
    *   You solved this by building a custom deterministic **Adversarial Preprocessing Pipeline** that handles visual homoglyphs, font transformations, and zero-width spaces before tokenization. This proves you think like a software engineer who writes custom algorithms to handle edge cases, not just an ML wrapper user.
2.  **Serverless & Decoupled Architecture (System Design & Scalability):**
    *   In the **ARM** project, you did not build a monolithic app. You decoupled the scraping microservice (**Azure Functions**) from the storage layer (**Blob Storage**) and the model workspace (**Azure ML**).
    *   This is exactly how Shopee and Sea Group design their microservices. Emphasize that decoupling makes services highly scalable, fault-tolerant, and independently maintainable.
3.  **Strict Test-Driven Development (Engineering Discipline):**
    *   Having **70+ unit and integration tests** in the **ARM** repository proves to Sea Labs that you practice production-grade software engineering. It shows that you value CI/CD, system stability, and predictable software behaviors.

---

## 🎤 Sea Labs Technical Interview Preparation (Grill-Me Prep)

If you advance to the technical interview, the interviewers will dive deep into your architectures. Here are 5 tough questions they might ask about your projects, along with highly technical ways to answer them:

### 1. "How does your visual homoglyph and font mapping pipeline work under the hood? Isn't regex parsing slow for large-scale streaming data?"
*   **The Trap:** They want to see if your preprocessing pipeline will choke and cause latency bottlenecks in a real-time production setting.
*   **How to Answer:** 
    > *"To prevent bottlenecking during real-time inference, the visual homoglyph mapping uses a direct O(1) character-to-character lookup table compiled using Python's native translation mapping (`str.translate`). Instead of running multiple heavy regex operations sequentially, we consolidate the invisible character removal, mathematical font conversion, and visual lookalike translation into a single pass normalization step. Additionally, for the ~440K slang dictionary, we index the keys using a high-performance hash map (Python dict) which guarantees average-case O(1) search complexity. This ensures our Streamlit app and backend can preprocess raw text inputs in under 5 milliseconds."*

### 2. "Why did you choose a Hybrid CNN-BiLSTM model alongside IndoBERT? Why not just use IndoBERT for everything?"
*   **The Trap:** They want to test your understanding of architectural tradeoffs, compute costs, and production latency.
*   **How to Answer:**
    > *"While IndoBERT achieves state-of-the-art Macro F1 scores, its 110-million parameter Transformer architecture incurs substantial computational overhead, high inference latency, and requires expensive GPU resources in a production cluster. The Hybrid CNN-BiLSTM model offers an excellent resource-accuracy trade-off. The Conv1D layers extract local spatial features (n-gram word patterns) very fast, and the BiLSTM processes temporal sequential context with a fraction of the parameter count. By utilizing pre-trained FastText embeddings, we achieved near-Transformer classification performance with a model that runs efficiently on low-cost CPU clusters, which is highly beneficial for cost-effective scaling."*

### 3. "How did you handle the severe class imbalance in your UU ITE dataset?"
*   **The Trap:** Social media comments are mostly neutral (`Label 0`). Violations like Pornography or Online Gambling are highly sparse. A naive model will just predict `Neutral` and get 95% accuracy while failing completely at its actual task.
*   **How to Answer:**
    > *"Class imbalance was a major hurdle since 'Neutral' dominated our scraped dataset. To address this, we did not rely on standard accuracy. Instead, we optimized our training objectives using **Macro F1 Score** as our early stopping metric, which treats all 6 classes with equal weight regardless of sample size. Furthermore, we created multiple undersampling data distributions (10K, 20K, and 30K variants per class) to train our sequence models and fine-tune IndoBERT using Cross-Entropy and Sparse Categorical Cross-Entropy losses, ensuring the models learned high-quality decision boundaries for minority violation classes."*

### 4. "In your ARM project, how do you handle partial failures in your serverless pipeline? For example, what if the scraper fails or the Azure ML cluster times out?"
*   **The Trap:** In production, APIs fail constantly. They want to see if you design resilient, self-healing architectures.
*   **How to Answer:**
    > *"Our architecture is built on the principle of decoupled resiliency. If the serverless scraper in Azure Functions encounters an API limit or network error, it utilizes an exponential backoff retry mechanism with automated alerting. Because the data layer is decoupled, even if the ML pipeline or inference cluster is temporarily down, the raw scraped data is securely persisted in Azure Blob Storage. Once the compute cluster recovers, the batch pipeline can process the backlogged data from the storage layer without any loss of historical input. We also write integration tests via Pytest to validate that schema changes or network timeouts are gracefully caught and logged."*

### 5. "How did you manage the deployment and integration between the backend data storage and the Javascript dashboard?"
*   **The Trap:** Testing your knowledge of backend-frontend integration and CORS/security protocols.
*   **How to Answer:**
    > *"The Javascript dashboard is deployed on Azure Static Web Apps and is entirely decoupled from our analytical storage. It consumes processed, aggregated data from our secure storage layer using optimized, read-only JSON endpoints. To secure the endpoints, we configure strict Cross-Origin Resource Sharing (CORS) policies so that only our authenticated dashboard domain can request data. This decoupled pattern ensures that high frontend traffic does not interfere with our backend scraping and machine learning pipelines, maintaining extreme security and speed."*
