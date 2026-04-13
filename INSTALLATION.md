# Installation Guide

Complete guide to installing and setting up kakao2notion.

## System Requirements

- Python 3.10 or higher
- pip package manager
- ~100MB disk space for dependencies

## Step-by-Step Installation

### Option 1: Install from PyPI (Recommended)

Once published on PyPI:

```bash
pip install kakao2notion
```

### Option 2: Install from GitHub

```bash
git clone https://github.com/leehogwang/kakao2notion.git
cd kakao2notion
pip install -e .
```

The `-e` flag installs in editable mode, allowing you to modify code.

### Option 3: Manual Installation

1. Clone the repository:
```bash
git clone https://github.com/leehogwang/kakao2notion.git
cd kakao2notion
```

2. Create virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install the package:
```bash
pip install -e .
```

## Verify Installation

Check if kakao2notion is installed:

```bash
kakao2notion --version
```

You should see: `kakao2notion, version 0.1.0`

## Setup Notion API

1. Go to https://www.notion.so/my-integrations
2. Click "Create new integration"
3. Give it a name (e.g., "kakao2notion")
4. Click "Submit"
5. Copy the "Internal Integration Token"

## Setup LLM Provider

### For Codex Users

Install Codex CLI:

```bash
npm install -g @anthropic-ai/codex
```

Authenticate with Codex:

```bash
codex login
# Follow the prompts to authenticate
```

Verify installation:

```bash
codex --version
```

### For Claude Users

1. Get API key from https://console.anthropic.com/
2. Set environment variable:
```bash
export ANTHROPIC_API_KEY="your-api-key"
```

Or create `.env` file in your working directory:
```
ANTHROPIC_API_KEY=your-api-key
```

## Configure kakao2notion

Initialize configuration:

```bash
kakao2notion configure
```

You'll be prompted for:
- **Notion API Key**: Paste the token from Notion
- **LLM Provider**: Choose `codex` or `claude`

Configuration is saved to `~/.kakao2notion/config.json`

## Verify Setup

Test Notion connection:

```bash
kakao2notion test
```

Expected output:
```
✓ Connection successful
```

## Optional: Install Additional Packages

For better semantic understanding:

```bash
pip install sentence-transformers
```

For development/testing:

```bash
pip install pytest pytest-cov black ruff
```

## Troubleshooting

### Command not found: kakao2notion

**Solution:**
- Verify installation: `pip list | grep kakao2notion`
- Check PATH is correct: `which kakao2notion`
- Try reinstalling: `pip install --force-reinstall kakao2notion`

### Module import errors

**Solution:**
```bash
pip install --upgrade --force-reinstall kakao2notion
```

### Notion authentication fails

**Solution:**
1. Verify API key is correct
2. Test at: https://developers.notion.com/reference
3. Make sure integration has database access (share database with integration)

### Codex not found

**Solution:**
```bash
# Check npm installation
npm list -g @anthropic-ai/codex

# Verify codex in PATH
which codex

# If not found, add npm bin to PATH
export PATH="$HOME/.npm-global/bin:$PATH"
```

### Claude API errors

**Solution:**
1. Verify API key: `echo $ANTHROPIC_API_KEY`
2. Check account has API access at console.anthropic.com
3. Verify no typos in .env file

## Next Steps

After installation and setup:

1. Try the quick start: See README.md
2. Process your first KakaoTalk export: `kakao2notion process input.json`
3. Upload to Notion: `kakao2notion upload input.json --database-id YOUR_ID`

## Getting Help

- Check the README.md for usage examples
- See examples/ directory for sample files
- Run `kakao2notion --help` for command help
- Report issues on GitHub

## Uninstall

To remove kakao2notion:

```bash
pip uninstall kakao2notion
```

To also remove configuration:

```bash
rm -rf ~/.kakao2notion
```
