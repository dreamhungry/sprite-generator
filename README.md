# Sprite Generator

An AI-powered automated pipeline for 2D game assets. Generates character sprites, frame-by-frame animations, and tile-based maps from text prompts or reference images. Streamlining the workflow from concept to game-ready assets.

## Features

- **Multi-modal Input**: Text prompts and/or reference images
- **Multiple AI Providers**: OpenAI (gpt-image-1), Google Gemini — extensible to more
- **Full Post-Processing Pipeline**:
  - Magenta chroma-key background removal (flood-fill edge diffusion)
  - Sprite sheet grid splitting
  - Connected component analysis
  - Frame alignment and uniform scaling
  - Transparent sprite sheet composition
  - Animated GIF export with transparency
- **Gradio Web UI**: Simple interface with input panel and result preview

## Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API key and/or Google Gemini API key

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd sprite-generator

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate
# Activate (Linux/Mac)
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your API keys
# OPENAI_API_KEY=sk-...
# GEMINI_API_KEY=...
```

### Run

```bash
python -m src.app
```

The Gradio web interface will open at `http://localhost:7860`.

## Usage

1. **Enter a subject** — describe what you want to generate (e.g., "fire dragon", "knight warrior")
2. **Choose settings** — select provider, asset type, animation mode, grid layout, and style
3. **Optionally upload a reference image** — for guided generation
4. **Click Generate** — wait for the AI to generate and post-process
5. **Preview results** — browse raw output, processed sheet, individual frames, and animation

## Project Structure

```
sprite-generator/
├── src/
│   ├── app.py              # Main entry point
│   ├── config.py           # Configuration and defaults
│   ├── controller.py       # Pipeline orchestration
│   ├── prompt_builder.py   # Prompt template construction
│   ├── providers/          # Image generation providers
│   │   ├── base.py         # Abstract provider interface
│   │   ├── openai_provider.py
│   │   └── gemini_provider.py
│   ├── processing/         # Post-processing pipeline
│   │   ├── background.py   # Background removal
│   │   ├── grid.py         # Grid splitting & components
│   │   ├── alignment.py    # Frame alignment & scaling
│   │   └── export.py       # Sheet/GIF/frame export
│   └── ui/
│       └── interface.py    # Gradio interface
├── output/                 # Generated assets (gitignored)
├── requirements.txt
├── .env.example
└── .gitignore
```

## Adding a New Provider

1. Create `src/providers/your_provider.py`
2. Implement the `ImageProvider` abstract class (see `base.py`)
3. Register in `src/providers/__init__.py`

## License

MIT
