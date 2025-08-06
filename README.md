# Termitas - Local LLM Chat

A modern AI-powered chat application that runs powerful language models locally using PyTorch.

## 🚀 Features

- **🤖 Local AI Models** - Run powerful language models locally with PyTorch
- **💬 Intelligent Chat** - Natural conversations with AI assistants
- **🔍 Model Browser** - Search and download models from Hugging Face
- **⚡ GPU Acceleration** - Automatic CUDA/MPS detection with fallback to CPU
- **🔧 GPU Settings** - Built-in PyTorch installation and configuration
- **📦 Easy Packaging** - Create standalone executables for distribution
- **💾 Chat History** - Save and manage conversation sessions
- **🎨 Modern UI** - Clean, responsive interface built with CustomTkinter

## 🎯 What It Does

Termitas is your local AI chat companion that can:
- **Answer questions** and provide information on any topic
- **Help with problem solving** and analysis
- **Explain complex topics** in simple terms
- **Assist with creative writing** and brainstorming
- **Provide technical support** and guidance
- **Help with learning** and education

## 🏗️ Architecture

- **UI Framework**: CustomTkinter for modern, responsive interface
- **AI Engine**: PyTorch with transformers for local model inference
- **Model Management**: Hugging Face Hub integration
- **Storage**: SQLite for model metadata and chat history
- **Optimization**: CPU-optimized loading with memory efficiency

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- 8GB+ RAM (16GB+ recommended)
- NVIDIA GPU with 8GB+ VRAM (optional but recommended)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/termitas.git
   cd termitas
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```

3. **Run the application:**
   ```bash
   uv run main.py
   ```

## 📦 Model Management

### Finding Models

1. **Search Bar** - Enter model names or keywords
2. **Quick Tags** - Click popular model families (Qwen, Mistral, Llama, etc.)
3. **Popular Models** - Browse trending models
4. **PyTorch Filter** - Only shows compatible PyTorch models

### Downloading Models

1. **Select a model** from the search results
2. **Click "Download"** to start downloading
3. **Monitor progress** with real-time progress bars
4. **Pause/Resume** downloads as needed

### Recommended Models

**For Terminal Tasks:**
- `Qwen/Qwen2.5-7B-Instruct` - Excellent for coding and terminal tasks
- `mistralai/Mistral-7B-Instruct-v0.2` - Great general purpose model
- `codellama/CodeLlama-7B-Instruct-hf` - Specialized for code generation
- `microsoft/Phi-3-mini-4k-instruct` - Small but powerful

## 💬 Using the Chat

### Starting a Conversation

1. **Select a model** from the "Active Model" section
2. **Type your message** in the chat input
3. **Press Enter** to send your message
4. **Get AI responses** in real-time

### Example Interactions

```
You: "What is machine learning?"

AI: Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed. It involves algorithms that can identify patterns in data and make predictions or decisions based on that data.

The main types of machine learning include:
- Supervised learning (using labeled data)
- Unsupervised learning (finding patterns in unlabeled data)
- Reinforcement learning (learning through trial and error)
```

```
You: "Help me write a Python function"

AI: I'd be happy to help you write a Python function! Here's a simple example:

```python
def greet_user(name):
    """A simple function that greets a user."""
    return f"Hello, {name}! Welcome to our program."
```

What specific function would you like to create?
```

## 🔧 Configuration

### GPU Support

The application includes built-in GPU support with automatic detection:

#### **Automatic GPU Detection**
- **NVIDIA CUDA** - For NVIDIA GPUs (RTX, GTX, etc.)
- **Apple MPS** - For Apple Silicon Macs
- **CPU Fallback** - Automatic fallback when GPU is unavailable

#### **GPU Settings Dialog**
Access via the "⚙️ GPU Settings" button in the options panel:
- **GPU Status Check** - View your GPU and PyTorch configuration
- **One-Click Installation** - Install PyTorch with CUDA support
- **Nightly Builds** - For latest GPUs like RTX 5090
- **CPU-Only Option** - For systems without GPU

#### **Supported GPUs**
- **RTX 40 Series** - Full support with CUDA
- **RTX 30 Series** - Full support with CUDA
- **RTX 5090** - Requires nightly PyTorch build
- **GTX Series** - Limited support (older models)
- **Apple Silicon** - MPS acceleration

### Memory Optimization

- **Smart Device Mapping** - Automatic GPU/CPU allocation
- **Low Memory Usage** - Optimized for desktop systems
- **Fallback System** - Graceful degradation to CPU

## 📦 Building Executables

### Using PyInstaller

```bash
python build_exe.py
```

This creates a standalone executable with:
- All dependencies included
- GPU support preserved
- Optimized for distribution

### Package Features

- **Small Size** - Optimized PyTorch packaging
- **GPU Support** - CUDA/MPS included
- **No Installation** - Runs on any compatible system
- **Offline Capable** - Works without internet after setup

## 🛠️ Development

### Project Structure

```
termitas/
├── main.py                 # Application entry point
├── config.py              # Configuration settings
├── ui/                    # User interface components
│   ├── core/             # Main UI windows
│   └── models/           # Model management UI
├── llm/                  # AI inference engine
│   ├── simple_inference.py  # PyTorch inference
│   └── model_downloader.py  # Model management
├── hf/                   # Hugging Face integration
└── database/             # SQLite database layer
```

### Key Components

- **SimpleInference** - PyTorch-based AI engine
- **PyTorchModelDownloader** - Model download and management
- **ChatWindow** - Main chat interface
- **ListModels** - Model browser and downloader

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Hugging Face** - For the model ecosystem
- **PyTorch Team** - For the excellent ML framework
- **CustomTkinter** - For the beautiful UI framework

---

**Ready to supercharge your terminal workflow?** 🚀

Start Termitas and let AI handle your command-line tasks!
