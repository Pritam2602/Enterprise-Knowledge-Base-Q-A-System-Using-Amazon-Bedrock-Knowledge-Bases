# 🧠 Enterprise Knowledge Base Q&A System

> **RAG-powered Q&A application using Amazon Bedrock Knowledge Bases**
>
> Ask natural language questions about your company documents and get accurate, citation-backed answers.

---

## 📌 Architecture

```
┌─────────────────┐     REST API      ┌─────────────────┐     boto3      ┌──────────────────────┐
│                 │  ──────────────►  │                 │  ──────────►  │   Amazon Bedrock      │
│   React + Vite  │                   │  FastAPI Server │               │   Knowledge Base      │
│   (Frontend)    │  ◄──────────────  │  (Backend)      │  ◄──────────  │   + Vector Store      │
│                 │     JSON          │                 │    Answer +   │   + Foundation Model   │
└─────────────────┘                   └─────────────────┘   Citations   └──────────────────────┘
                                                                               │
                                                                               ▼
                                                                        ┌──────────────┐
                                                                        │   S3 Bucket   │
                                                                        │  (Documents)  │
                                                                        └──────────────┘
```

## ✨ Features

| Feature | Description |
|---------|-------------|
| 💬 **Smart Q&A** | Ask questions in natural language and get grounded answers |
| 📎 **Source Citations** | Every answer includes expandable document citations with relevance scores |
| 🔍 **Semantic Search** | Toggle to pure search mode for browsing relevant document chunks |
| 🎨 **Premium Dark UI** | Glassmorphism design with gradient accents and micro-animations |
| ⚡ **Real-time Status** | Live backend connectivity indicator |
| 📊 **Session Stats** | Track query count and average response time |
| 🔄 **Multi-turn Chat** | Conversations maintain context via session IDs |
| 🛡️ **Error Handling** | User-friendly error messages with retry logic |

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Frontend** | React 18, Vite, Vanilla CSS |
| **Backend** | Python 3.11+, FastAPI, Uvicorn |
| **RAG Engine** | Amazon Bedrock Knowledge Bases |
| **LLM** | Amazon Nova lite |
| **Embeddings** | Amazon Titan Embeddings V2 |
| **Vector Store** | Amazon OpenSearch Serverless (managed) |
| **Documents** | Amazon S3 |
| **Deployment** | AWS EC2, Nginx |
| **Auth** | AWS IAM Roles |

---

## 🚀 Quick Start (Local Development)

### Prerequisites

- Python 3.10+
- Node.js 18+
- AWS CLI configured with Bedrock access
- A Bedrock Knowledge Base already created

### 1. Clone the Repository

```bash
git clone https://github.com/Pritam2602/Enterprise-Knowledge-Base-Q-A-System-Using-Amazon-Bedrock-Knowledge-Bases.git
cd Enterprise-Knowledge-Base-Q-A-System-Using-Amazon-Bedrock-Knowledge-Bases
```

### 2. Backend Setup

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env and add your KNOWLEDGE_BASE_ID
```

### 3. Frontend Setup

```bash
cd frontend
npm install
cd ..
```

### 4. Start Development Servers

**Terminal 1 — Backend:**
```bash
cd backend
uvicorn main:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend
node ./node_modules/vite/bin/vite.js dev
```

Open **http://localhost:5173** in your browser.

---

## ☁️ AWS Prerequisites

### 1. Enable Bedrock Model Access

1. Go to **AWS Console → Amazon Bedrock → Model Access**
2. Request access to:
   - **Anthropic Claude 3 Sonnet** (generation)
   - **Amazon Titan Embeddings V2** (embeddings)
3. Wait for access to be approved

### 2. Create a Knowledge Base

1. Go to **AWS Console → Amazon Bedrock → Knowledge Bases**
2. Click **Create Knowledge Base**
3. Choose S3 as the data source
4. Upload your documents to the S3 bucket
5. Select **Amazon Titan Embeddings V2** as the embedding model
6. Let Bedrock create the vector store (OpenSearch Serverless)
7. Sync the data source
8. Copy the **Knowledge Base ID** to your `.env` file

### 3. IAM Permissions

Your AWS credentials (or EC2 IAM role) need these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:Retrieve",
        "bedrock:RetrieveAndGenerate"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## 🖥️ EC2 Deployment

### 1. Launch an EC2 Instance

- **AMI:** Amazon Linux 2023 or Ubuntu 22.04
- **Instance Type:** t3.medium (minimum)
- **Security Group:** Allow inbound ports 22 (SSH) and 80 (HTTP)
- **IAM Role:** Attach a role with Bedrock permissions (see above)

### 2. Run the Deploy Script

```bash
# SSH into your EC2 instance
ssh -i your-key.pem ec2-user@<ec2-public-ip>

# Clone and deploy
git clone https://github.com/Pritam2602/Enterprise-Knowledge-Base-Q-A-System-Using-Amazon-Bedrock-Knowledge-Bases.git
cd Enterprise-Knowledge-Base-Q-A-System-Using-Amazon-Bedrock-Knowledge-Bases

# Edit your config
cp backend/.env.example backend/.env
nano backend/.env  # Add your KNOWLEDGE_BASE_ID

# Run deployment
chmod +x deployment/deploy.sh
./deployment/deploy.sh
```

### 3. Access Your Application

Open `http://<ec2-public-ip>` in your browser.

---

## 📁 Project Structure

```
├── backend/                    # FastAPI backend
│   ├── main.py                 # API endpoints (query, search, health)
│   ├── bedrock_client.py       # Bedrock KB API wrapper with retry logic
│   ├── config.py               # Environment config management
│   ├── utils.py                # Citation parsing, response formatting
│   ├── requirements.txt        # Python dependencies
│   └── .env.example            # Environment variable template
│
├── frontend/                   # React + Vite frontend
│   ├── src/
│   │   ├── App.jsx             # Root component
│   │   ├── index.css           # Design system (CSS variables, animations)
│   │   ├── api/bedrockApi.js   # API client
│   │   ├── hooks/useChat.js    # Chat state management hook
│   │   └── components/         # UI components
│   │       ├── Header.jsx      # App header with status indicator
│   │       ├── Sidebar.jsx     # Settings, stats, and info panel
│   │       ├── ChatWindow.jsx  # Message list with welcome screen
│   │       ├── MessageBubble.jsx # Message with citations
│   │       ├── ChatInput.jsx   # Auto-resizing input
│   │       ├── CitationCard.jsx # Expandable source card
│   │       └── LoadingIndicator.jsx # Animated loader
│   └── vite.config.js          # Vite config with API proxy
│
├── data/sample_docs/           # Sample enterprise documents
├── deployment/                 # EC2 deployment files
│   ├── deploy.sh               # Automated deployment script
│   └── nginx.conf              # Nginx reverse proxy config
│
├── .gitignore
└── README.md
```

## 🔧 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/query` | RAG query → answer + citations |
| `POST` | `/api/search` | Semantic search → document chunks |
| `GET`  | `/api/health` | Backend + Bedrock connectivity check |
| `GET`  | `/api/config` | Public config (region, model, KB ID) |

### Example: Query Request

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the leave policy?", "num_results": 5}'
```

### Example: Response

```json
{
  "answer": "According to the TechCorp Leave Policy, employees receive PTO based on their length of service...",
  "citations": [
    {
      "documentName": "leave_policy.txt",
      "text": "PTO accrual is based on length of service: 0-2 years: 18 days...",
      "s3Uri": "s3://my-bucket/leave_policy.txt",
      "score": 0.92
    }
  ],
  "sessionId": "abc-123",
  "responseTime": 3.45
}
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| `AccessDeniedException` | Enable model access in Bedrock console and check IAM permissions |
| `ResourceNotFoundException` | Verify `KNOWLEDGE_BASE_ID` in `.env` matches your KB |
| Frontend shows "Disconnected" | Ensure backend is running on port 8000 |
| Slow responses | Normal for RAG (2-5 seconds). Check Bedrock service health |
| Empty citations | Sync your Knowledge Base data source after uploading documents |

---

## 💰 Cost Estimation

| Service | Estimated Cost |
|---------|---------------|
| Bedrock (Claude 3 Sonnet) | ~$0.003-0.015 per query |
| Bedrock (Titan Embeddings) | ~$0.0001 per 1K tokens |
| OpenSearch Serverless | ~$0.24/OCU/hour (min 2 OCUs) |
| S3 Storage | ~$0.023/GB/month |
| EC2 (t3.medium) | ~$0.0416/hour |

---

## 👤 Author

**Pritam** — [GitHub](https://github.com/Pritam2602)

## 📄 License

This project is built for educational purposes as part of a learning program.
