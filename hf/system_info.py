import subprocess
import re
from typing import Optional, Dict, Tuple

def get_vram_info() -> Dict[str, any]:
    """Get VRAM information from the system."""
    try:
        # Try NVIDIA first
        nvidia_vram = get_nvidia_vram()
        if nvidia_vram:
            return {
                "total_vram_gb": nvidia_vram,
                "gpu_type": "NVIDIA",
                "status": "detected"
            }
        
        # Try AMD next
        amd_vram = get_amd_vram()
        if amd_vram:
            return {
                "total_vram_gb": amd_vram,
                "gpu_type": "AMD",
                "status": "detected"
            }
        
        # No GPU detected
        return {
            "total_vram_gb": 0,
            "gpu_type": "CPU Only",
            "status": "no_gpu"
        }
        
    except Exception as e:
        print(f"Error detecting VRAM: {e}")
        return {
            "total_vram_gb": 0,
            "gpu_type": "Unknown",
            "status": "error"
        }

def get_nvidia_vram() -> Optional[float]:
    """Get NVIDIA VRAM using nvidia-smi."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            vram_mb = int(result.stdout.strip())
            return vram_mb / 1024  # Convert MB to GB
        
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError, ValueError):
        pass
    
    return None

def get_amd_vram() -> Optional[float]:
    """Get AMD VRAM using system commands."""
    try:
        # Try Windows WMIC
        result = subprocess.run(
            ["wmic", "path", "win32_VideoController", "get", "AdapterRAM"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if line.strip() and line.strip() != "AdapterRAM":
                    try:
                        vram_bytes = int(line.strip())
                        if vram_bytes > 0:
                            return vram_bytes / (1024**3)  # Convert bytes to GB
                    except ValueError:
                        continue
                        
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    return None

def estimate_model_memory_gb(param_count: Optional[int], precision: str = "fp16") -> float:
    """Estimate model memory usage in GB for inference."""
    if not param_count:
        return 0.0
    
    # Bytes per parameter for different precisions
    precision_multipliers = {
        "fp32": 4,  # 32-bit float
        "fp16": 2,  # 16-bit float  
        "int8": 1,  # 8-bit quantized
        "int4": 0.5  # 4-bit quantized
    }
    
    bytes_per_param = precision_multipliers.get(precision, 2)
    
    # Model weights only (inference is more memory efficient than training)
    model_size_gb = (param_count * bytes_per_param) / (1024**3)
    
    # Add modest overhead for inference (KV cache + activations, ~15% for typical use)
    total_memory_gb = model_size_gb * 1.15
    
    return total_memory_gb

def get_compatibility_info(param_count: Optional[int], user_vram_gb: float) -> Dict[str, any]:
    """Get compatibility information for a model given user's VRAM."""
    if not param_count or param_count == 0:
        return {
            "status": "unknown",
            "message": "Unknown size",
            "color": "#888888",
            "icon": "❓"
        }
    
    # Estimate memory for different precisions
    fp16_memory = estimate_model_memory_gb(param_count, "fp16")
    int8_memory = estimate_model_memory_gb(param_count, "int8")
    int4_memory = estimate_model_memory_gb(param_count, "int4")
    
    if user_vram_gb == 0:
        return {
            "status": "cpu_only",
            "message": "CPU only (slow)",
            "color": "#888888",
            "icon": "🖥️"
        }
    
    # Check compatibility (use 90% of VRAM - more realistic for inference)
    available_vram = user_vram_gb * 0.9
    
    if fp16_memory <= available_vram:
        return {
            "status": "excellent",
            "message": f"Will run smoothly ({fp16_memory:.1f}GB)",
            "color": "#32cd32",
            "icon": "✅"
        }
    elif int8_memory <= available_vram:
        return {
            "status": "good",
            "message": f"Good with 8-bit ({int8_memory:.1f}GB)",
            "color": "#ffa500",
            "icon": "⚡"
        }
    elif int4_memory <= available_vram:
        return {
            "status": "fair",
            "message": f"OK with 4-bit ({int4_memory:.1f}GB)",
            "color": "#ff6b35",
            "icon": "⚠️"
        }
    else:
        return {
            "status": "too_large",
            "message": f"Too large ({fp16_memory:.1f}GB needed)",
            "color": "#ff0000",
            "icon": "❌"
        }

def get_system_summary(vram_info: Dict[str, any]) -> str:
    """Get a user-friendly system summary."""
    if vram_info["status"] == "detected":
        return f"🖥️ {vram_info['gpu_type']} GPU with {vram_info['total_vram_gb']:.1f}GB VRAM"
    elif vram_info["status"] == "no_gpu":
        return "🖥️ CPU only (no GPU detected)"
    else:
        return "🖥️ GPU detection failed" 