# RTX 5090 Compatibility Guide

## 🚨 Important: RTX 5090 and PyTorch Compatibility

### The Issue

Your **NVIDIA GeForce RTX 5090** has **CUDA capability sm_120**, but **PyTorch 2.7.0** only supports up to **sm_90**. This is a known compatibility issue.

### What This Means

- ✅ **GPU Detection**: Your RTX 5090 is properly detected
- ✅ **Basic Operations**: Simple GPU operations work
- ❌ **Model Loading**: Large language models fail to load on GPU
- ✅ **CPU Fallback**: The app automatically falls back to CPU

### Current Status

**This is expected behavior** - your RTX 5090 is too new for the current PyTorch release.

## 🔧 Solutions

### Option 1: Use CPU Fallback (Recommended)
The app automatically detects the issue and falls back to CPU:
- ✅ **Works immediately**
- ✅ **No installation needed**
- ✅ **Stable and reliable**
- ⚠️ **Slower than GPU**

### Option 2: Wait for PyTorch 2.8+
- **Expected**: PyTorch 2.8+ will support sm_120
- **Timeline**: Likely in Q1 2025
- **Status**: Under development

### Option 3: Try Nightly Builds
```bash
pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu121
```
- ⚠️ **Unstable**
- ⚠️ **May break**
- ⚠️ **Not recommended for production**

## 🎯 Current Recommendation

**Use the CPU fallback** - it's the most reliable option right now:

1. **Start the app normally**
2. **The app will detect RTX 5090**
3. **It will automatically fall back to CPU**
4. **You'll get working LLM chat**

## 📊 Performance Comparison

| Device | Speed | Memory | Stability |
|--------|-------|--------|-----------|
| RTX 5090 (GPU) | ❌ Not supported | ❌ Not supported | ❌ Not supported |
| CPU Fallback | ⚠️ Slower | ✅ Good | ✅ Excellent |
| Future PyTorch 2.8+ | ✅ Fast | ✅ Good | ✅ Expected |

## 🔍 Technical Details

### CUDA Capability Support

| PyTorch Version | Max CUDA Capability | RTX 5090 Support |
|-----------------|-------------------|------------------|
| 2.7.0 | sm_90 | ❌ No |
| 2.8.0+ (expected) | sm_120 | ✅ Yes |

### Error Messages You'll See

```
NVIDIA GeForce RTX 5090 with CUDA capability sm_120 is not compatible with the current PyTorch installation.
The current PyTorch install supports CUDA capabilities sm_50 sm_60 sm_61 sm_70 sm_75 sm_80 sm_86 sm_90.
```

**This is normal and expected.**

## 🛠️ GPU Settings Dialog

Use the **"⚙️ GPU Settings"** button in the app to:
- Check your GPU status
- See compatibility information
- Install different PyTorch versions
- Get detailed error information

## 📝 Summary

Your RTX 5090 is a powerful GPU, but it's too new for the current PyTorch release. The app handles this gracefully by falling back to CPU, ensuring you still get a working local LLM chat experience.

**The CPU fallback works well and is the recommended approach until PyTorch 2.8+ is released.** 