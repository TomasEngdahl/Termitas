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

- Python 3.12+
- 8GB+ RAM (16GB+ recommended)
- NVIDIA GPU with 8GB+ VRAM (optional but recommended)

### Installation

**Option 1: Using uv (if you have uv installed)**
```bash
# 1. Install dependencies
uv sync

# 2. Install CUDA PyTorch for GPU acceleration
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128 --force-reinstall

# 3. Run the application
python main.py
```

**Option 2: Using pip/venv (Recommended)**
```bash
# 1. Create virtual environment
python -m venv .venv

# 2. Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -e .

# 4. Install CUDA PyTorch for GPU acceleration
python install_cuda_pytorch.py

# 5. Run the application
python main.py
```

## 🔧 GPU Acceleration Setup

**For RTX 5090 and other modern NVIDIA GPUs:**

### **✅ Working Workflow:**

1. **Install base dependencies:**
   ```bash
   pip install -e .
   ```

2. **Install CUDA PyTorch:**
   ```bash
   python install_cuda_pytorch.py
   ```

3. **Run the application:**
   ```bash
   python main.py
   ```

### **⚠️ Troubleshooting:**

**If GPU is not detected:**
```bash
# Reinstall CUDA PyTorch
python install_cuda_pytorch.py

# Verify installation
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"None\"}')"
```

**If you're using uv and it reinstalls CPU version:**
```bash
# After uv run, reinstall CUDA version
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128 --force-reinstall
```

### **🎯 Why This Works:**

- **✅ Direct pip installation** - No dependency resolution conflicts
- **✅ CUDA index** - Gets PyTorch 2.8.0+cu128 for RTX 5090
- **✅ Helper script** - Automatically verifies GPU detection
- **✅ Simple workflow** - Easy to remember and use

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
```

## 🔧 Configuration

### GPU Settings

Access GPU settings through the application menu to:
- **Check GPU status** and PyTorch version
- **Install CUDA PyTorch** for GPU acceleration
- **Verify GPU detection** and compatibility

### Model Settings

- **Model selection** - Choose from downloaded models
- **Memory management** - Optimize for your hardware
- **Performance tuning** - Adjust for speed vs. quality

## 🚀 Performance Tips

### For GPU Users:
- **Use CUDA PyTorch** - Install with `python install_cuda_pytorch.py`
- **Monitor VRAM** - Keep an eye on GPU memory usage
- **Choose appropriate models** - Balance size vs. performance

### For CPU Users:
- **Use smaller models** - 3B-7B parameter models work well
- **Close other applications** - Free up RAM for model loading
- **Be patient** - CPU inference is slower but still functional

## 🐛 Troubleshooting

### Common Issues

**GPU not detected:**
```bash
python install_cuda_pytorch.py
```

**Model loading fails:**
- Check available RAM/VRAM
- Try a smaller model
- Restart the application

**Slow performance:**
- Use GPU acceleration if available
- Close other applications
- Choose smaller models

### Getting Help

1. **Check the logs** - Look for error messages in the console
2. **Verify GPU drivers** - Ensure NVIDIA drivers are up to date
3. **Test PyTorch installation** - Run the verification script
4. **Check system requirements** - Ensure sufficient RAM/VRAM

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Support

If you encounter any issues:
1. Check the troubleshooting section above
2. Verify your system meets the requirements
3. Try the GPU setup workflow
4. Open an issue with detailed error information
