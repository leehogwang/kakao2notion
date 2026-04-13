# Quick Start Guide

Get kakao2notion up and running in 5 minutes.

## 1. Install (2 minutes)

```bash
# Clone the repository
git clone https://github.com/leehogwang/kakao2notion.git
cd kakao2notion

# Install
pip install -e .
```

## 2. Setup Notion (2 minutes)

1. Go to https://www.notion.so/my-integrations
2. Create new integration → copy token

## 3. Export KakaoTalk

1. Open KakaoTalk
2. Open the chat you want to organize
3. Export as JSON or text
4. Save to `chat_export.json`

## 4. Run kakao2notion (1 minute)

```bash
# Just run this - interactive menu appears!
kakao2notion
```

Menu-driven interface guides you through:
- ✅ Configuration (API key, LLM provider)
- ✅ File selection and format detection
- ✅ Clustering settings (auto-optimize or manual)
- ✅ LLM options
- ✅ Preview before execution

## Alternative: Traditional CLI (if you prefer)

```bash
# Configure once
kakao2notion configure

# Process with auto-optimization
kakao2notion process chat_export.json \
  --auto-clusters \
  --use-llm

# Upload to Notion
kakao2notion upload chat_export.json \
  --database-id YOUR_DATABASE_ID \
  --auto-clusters
```

That's it! Your KakaoTalk messages are now organized in Notion.

## Tips

- **Optimal clustering?** Use `--auto-clusters` (automatically finds best cluster count)
  ```bash
  kakao2notion process chat.json --auto-clusters
  ```
  
- **Different optimization methods?** Try ensemble voting
  ```bash
  kakao2notion process chat.json --auto-clusters --cluster-method ensemble
  ```

- **No LLM?** Remove `--use-llm` to use simple keyword extraction

- **Want specific clusters?** Use `--n-clusters N` to override auto-optimization
  ```bash
  kakao2notion process chat.json --n-clusters 10
  ```

- **Preview before upload?** Use `process` command first with `--output`
  ```bash
  kakao2notion process chat.json --auto-clusters --output results.json
  ```

## Example Output

Input: 100 KakaoTalk messages
↓
Merged to: 80 messages (20 merged)
↓
Clustered into: 5 categories
- 서버 (Server): 15 messages
- 연구 (Research): 25 messages
- 실습실 (Lab): 20 messages
- 프로그래밍 (Programming): 12 messages
- 기타 (Other): 8 messages
↓
Each becomes a Notion page hierarchy:
```
Database
├── 서버
│   ├── 라이트백 설정
│   ├── NSM 마이그레이션
│   └── ...
├── 연구
│   ├── Transformer 논문
│   ├── PyTorch 설치법
│   └── ...
```

## Troubleshooting

**Command not found**
```bash
pip install -e .
```

**Notion connection fails**
- Verify API key: `kakao2notion test`
- Check integration exists in Notion
- Ensure integration has database access

**LLM not working**
- Codex: Install and authenticate `codex login`
- Claude: Set `export ANTHROPIC_API_KEY="..."`

**Need help?**
- See INSTALLATION.md for detailed setup
- See README.md for all commands
- Check examples/ for sample files

## Next Steps

1. Try with your real KakaoTalk export
2. Adjust `--n-clusters` as needed
3. Review results in Notion
4. Manually refine categories if desired

Happy organizing! 🎉
