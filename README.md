# kakao2notion

Convert KakaoTalk messages into organized Notion pages using intelligent clustering and LLM-powered categorization.

## Features

- **Message Parsing**: Support for JSON and text KakaoTalk exports
- **Smart Merging**: Semantically similar consecutive messages are automatically merged
- **KNN Clustering**: Automatically group messages into categories based on similarity
- **LLM Integration**: Generate human-readable category names using Codex or Claude
- **Notion Integration**: Create hierarchical page structure in Notion (categories → messages)
- **Multi-user**: Works with any KakaoTalk chat export
- **CLI Tool**: Easy-to-use command-line interface

## Installation

### Prerequisites

- Python 3.10+
- Notion API token
- (Optional) Codex CLI installed and authenticated, or Claude API key

### Via pip

```bash
pip install kakao2notion
```

### Via git

```bash
git clone https://github.com/leehogwang/kakao2notion.git
cd kakao2notion
pip install -e .
```

## Quick Start

### Interactive Mode (Recommended)

**Easiest way - just run:**

```bash
kakao2notion
```

This launches an interactive menu where you can:
1. Select operation (process/upload/configure)
2. Choose input file
3. Set clustering options with explanations
4. Preview settings before executing
5. Run the operation

**Example interaction:**
```
kakao2notion

🎯 kakao2notion
   KakaoTalk → Notion Converter

Choose option
1. 📊 Process messages (preview only)
2. 📤 Upload to Notion
3. ⚙️  Configure (API key, LLM)
4. 🧪 Test connection
5. ❌ Exit

> 1

📁 Enter path to KakaoTalk export file: chat_export.json

File format detection:
> auto

🤖 Automatically find optimal clusters? [Y/n]: y

Optimization methods:
1. Silhouette Score (default, recommended)
2. Davies-Bouldin Index
3. Calinski-Harabasz
4. Elbow Method
5. Ensemble Voting (all methods)

> 1

Settings Summary:
Input File          chat_export.json
Format              auto
Auto Clusters       ✓ Yes
Cluster Method      silhouette
Use LLM             ✓ Yes

✅ Proceed with these settings? [Y/n]: y
```

### Traditional CLI Mode (Advanced)

Still works as before if you prefer command-line:

```bash
# Configure once
kakao2notion configure

# Process messages
kakao2notion process input.json \
  --auto-clusters \
  --use-llm \
  --output results.json

# Upload to Notion
kakao2notion upload input.json \
  --database-id YOUR_DATABASE_ID \
  --auto-clusters
```

## Commands

### configure

Set up Notion API key and LLM provider.

```bash
kakao2notion configure [--api-key KEY] [--llm-provider {codex,claude}]
```

### process

Process KakaoTalk messages without uploading.

```bash
kakao2notion process INPUT [--format {json,txt,auto}] \
  [--n-clusters N] \
  [--auto-clusters] \
  [--cluster-method METHOD] \
  [--similarity-threshold T] \
  [--use-llm] \
  [--output FILE]
```

**Options:**
- `--format`: Input format (auto-detect by extension)
- `--n-clusters`: Number of categories (if omitted, auto-estimates)
- `--auto-clusters`: Automatically find optimal number of clusters
- `--cluster-method`: Algorithm for optimization
  - `silhouette` (default) - Best cluster cohesion/separation
  - `davies_bouldin` - Cluster distance ratio
  - `calinski` - Variance ratio
  - `elbow` - Inertia optimization
  - `ensemble` - Vote from all methods
- `--similarity-threshold`: Merge threshold 0-1 (default: 0.7)
- `--use-llm`: Use LLM for category names (requires config)
- `--output`: Save results as JSON

### upload

Process and upload to Notion in one step.

```bash
kakao2notion upload INPUT \
  --database-id ID \
  [--format {json,txt,auto}] \
  [--n-clusters N] \
  [--auto-clusters] \
  [--cluster-method METHOD] \
  [--use-llm]
```

**Options:**
- `--database-id`: Notion database ID (required)
- `--auto-clusters`: Automatically optimize cluster count
- `--cluster-method`: Algorithm choice (see `process` command)
- Other options same as `process`

### test

Test Notion API connection.

```bash
kakao2notion test
```

## Input Formats

### JSON Export

```json
{
  "chatName": "My Research Chat",
  "messages": [
    {
      "text": "Message content",
      "sender": "John",
      "time": "2024-01-01 12:00:00"
    },
    {
      "text": "Another message",
      "sender": "Jane",
      "time": "2024-01-01 12:01:00"
    }
  ]
}
```

### Text Export

```
[2024-01-01 12:00:00] John: Message content
[2024-01-01 12:01:00] Jane: Another message
```

## Configuration

Configuration file location: `~/.kakao2notion/config.json`

```json
{
  "notion_api_key": "your-token",
  "notion_database_id": "optional-default-db",
  "n_clusters": 5,
  "similarity_threshold": 0.7,
  "use_llm_for_categories": true,
  "llm_provider": "codex",
  "llm_model": null,
  "batch_size": 10,
  "max_workers": 4
}
```

Or use environment variables:
```bash
export NOTION_API_KEY="your-token"
export LLM_PROVIDER="claude"
export LLM_MODEL="claude-3-haiku-20240307"
```

## LLM Integration

### Using Codex

Requires Codex CLI installed and authenticated:

```bash
# Install Codex
npm install -g @anthropic-ai/codex

# Authenticate
codex login

# Use with kakao2notion
kakao2notion configure --llm-provider codex
```

**How it works:**
- kakao2notion calls the Codex CLI subprocess
- Codex inherits authentication from your saved credentials
- Similar to how AgentForge uses Codex

### Using Claude

Requires Claude API key:

```bash
export ANTHROPIC_API_KEY="your-key"

kakao2notion configure --llm-provider claude
```

## How It Works

```
1. Parse KakaoTalk Export
   ↓
2. Vectorize Messages (TF-IDF)
   ↓
3. Merge Similar Messages
   ↓
4. Cluster (K-means)
   ↓
5. Generate Category Names (LLM or fallback)
   ↓
6. Create Notion Hierarchy
   ├── Category Pages
   └── Message Sub-Pages
```

### Vectorization

Messages are converted to TF-IDF vectors for similarity comparison. You can optionally use sentence-transformers for better semantic understanding:

```bash
pip install sentence-transformers
```

Then use in code:
```python
from kakao2notion import Vectorizer
vectorizer = Vectorizer(model_type="sbert")
```

### Message Merging

Messages are merged if:
- They are consecutive
- Similarity score ≥ threshold (default 0.7)
- Result is a multi-line message in Notion

This handles cases like:
```
User 1: 프로그램 설치법
User 1: 라이트백에서 잡고있는 것을 확인한다
User 1: 대게 win11
User 1: nsm에서 서버관리에 들어간다
```

All become one merged message.

### Clustering

K-means clustering groups similar messages into categories. 

**Option 1: Automatic Optimization (Recommended)**

kakao2notion automatically finds the optimal number of clusters:

```bash
kakao2notion process input.json --auto-clusters
```

This uses **Silhouette Score** by default, which measures both:
- **Cohesion**: How close messages are within a cluster
- **Separation**: How far apart clusters are from each other

**Option 2: Choose Algorithm**

```bash
# Best overall performance
kakao2notion process input.json --auto-clusters --cluster-method silhouette

# Alternative methods:
kakao2notion process input.json --auto-clusters --cluster-method davies_bouldin
kakao2notion process input.json --auto-clusters --cluster-method calinski
kakao2notion process input.json --auto-clusters --cluster-method elbow

# Ensemble voting (consensus of all methods)
kakao2notion process input.json --auto-clusters --cluster-method ensemble
```

**Option 3: Manual Specification**

```bash
kakao2notion process input.json --n-clusters 10
```

**How It Works**

When `--auto-clusters` is used:
1. Tests different cluster counts (2 to sqrt(n_messages))
2. Evaluates each using the selected method
3. Selects the count with best score
4. Reports silhouette score (0-1):
   - > 0.7: Excellent clustering
   - > 0.5: Good clustering
   - > 0.25: Fair clustering
   - < 0.25: Poor clustering

### LLM Category Naming

The LLM is given 5 sample messages from each cluster and generates a category name in Korean.

For example, messages about "라이트백", "NSM", "자식 디스크" might be named "서버" (Server).

## API Usage

Use kakao2notion as a library:

```python
from kakao2notion import (
    parse_kakaotalk_messages,
    Vectorizer,
    MessageMerger,
    KNNClusterer,
    NotionClient,
)

# Parse
messages = parse_kakaotalk_messages("chat.json")

# Vectorize
vectorizer = Vectorizer()
vectors = vectorizer.fit_transform([m.content for m in messages])

# Merge
merger = MessageMerger(vectorizer, similarity_threshold=0.7)
merged = merger.merge_messages(messages)

# Cluster
clusterer = KNNClusterer(n_clusters=5)
clusterer.fit(vectors)

# Upload to Notion
notion = NotionClient(api_key="your-key")
categories = {
    "서버": [messages[0], messages[1]],
    "연구": [messages[2], messages[3]],
}
notion.create_hierarchy("database-id", categories)
```

## Troubleshooting

### Codex not found

```
Error: Codex CLI not found or not in PATH
```

**Solution:**
```bash
npm install -g @anthropic-ai/codex
export PATH="$HOME/.npm-global/bin:$PATH"
```

### Notion authentication failed

```
Error: Invalid API key
```

**Solution:**
1. Get token from https://www.notion.so/my-integrations
2. Create new integration
3. Copy token
4. Run: `kakao2notion configure`

### LLM generation too slow

LLM calls can take 10-30 seconds. To skip:

```bash
kakao2notion process input.json --no-use-llm
```

Will use fallback keyword extraction.

### Messages not merging correctly

Adjust similarity threshold:

```bash
kakao2notion process input.json --similarity-threshold 0.8
```

Lower threshold (e.g., 0.5) = more aggressive merging
Higher threshold (e.g., 0.9) = less merging

## Development

### Install dev dependencies

```bash
pip install -e ".[dev]"
```

### Run tests

```bash
pytest tests/
```

### Code style

```bash
black kakao2notion/
ruff check kakao2notion/
```

## License

MIT License - See LICENSE file

## Contributing

Contributions welcome! Please:

1. Fork the repo
2. Create feature branch
3. Add tests
4. Submit PR

## Author

Created by Lee Ho Gwang

## Acknowledgments

- Inspired by AgentForge's Codex integration pattern
- Uses scikit-learn for clustering
- Notion API integration via notion-client
- Sentence transformers for semantic similarity

## FAQ

**Q: Can I use this with group chats?**
A: Yes, just export the chat as JSON or text.

**Q: What if Codex is not installed?**
A: Use Claude API instead, or generate category names manually.

**Q: Can categories be manually edited after upload?**
A: Yes, edit directly in Notion.

**Q: Does it support other messaging apps?**
A: Currently KakaoTalk only. PRs welcome for other apps.

**Q: How many messages can it handle?**
A: Tested with 5000+ messages. Performance depends on similarity threshold.
