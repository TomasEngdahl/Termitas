#!/usr/bin/env python3
"""
PyTorch Model Downloader for Hugging Face models
"""

import os
import threading
import time
from pathlib import Path
from typing import List, Dict, Optional, Callable
from huggingface_hub import HfApi, snapshot_download
from database.models_db import get_db, get_models_dir

class DownloadProgress:
    """Tracks download progress for a model."""
    
    def __init__(self, model_id: str):
        self.model_id = model_id
        self.progress_percent = 0.0
        self.downloaded_bytes = 0
        self.total_bytes = 0
        self.download_speed = 0.0
        self.eta_seconds = None
        self.status = "pending"  # pending, downloading, paused, completed, error
        self.error_message = None

class PyTorchModelDownloader:
    """Downloads and manages PyTorch models from Hugging Face."""
    
    def __init__(self):
        self.models_dir = get_models_dir()
        self.api = HfApi()
        self.db = get_db()
        self.active_downloads = {}  # model_id -> DownloadProgress
        self.download_threads = {}  # model_id -> Thread
        self.download_locks = {}  # model_id -> Lock
    
    def search_pytorch_models(self, query: str = "text-generation", limit: int = 20) -> List[Dict]:
        """Search for PyTorch models on Hugging Face - OPTIMIZED VERSION."""
        try:
            from huggingface_hub import list_models, ModelInfo
            
            # Search for models with HF's built-in PyTorch filter
            models_generator = list_models(
                search=query,
                sort="downloads",
                direction=-1,
                limit=limit,
                filter="pytorch"  # Use HF's built-in PyTorch filter
            )
            models = list(models_generator)
            
            # Convert to our format
            pytorch_models = []
            for model in models:
                pytorch_models.append({
                    'modelId': model.modelId,
                    'downloads': model.downloads or 0,
                    'likes': model.likes or 0,
                    'tags': model.tags or [],
                    'pytorch_files': 1  # Assume PyTorch since we filtered for it
                })
            
            print(f"📊 Found {len(pytorch_models)} PyTorch models for '{query}'")
            return pytorch_models
            
        except Exception as e:
            print(f"❌ Error searching PyTorch models: {e}")
            return []
    
    def get_available_models(self) -> Dict:
        """Get a curated list of popular PyTorch models."""
        return {
            "coding_models": [
                {
                    "name": "Qwen2.5-7B-Instruct",
                    "modelId": "Qwen/Qwen2.5-7B-Instruct",
                    "description": "Excellent for coding and terminal tasks",
                    "size_gb": 14,
                    "tags": ["text-generation", "coding", "instruct"]
                },
                {
                    "name": "Mistral-7B-Instruct-v0.2",
                    "modelId": "mistralai/Mistral-7B-Instruct-v0.2",
                    "description": "Great for general tasks and coding",
                    "size_gb": 14,
                    "tags": ["text-generation", "instruct"]
                },
                {
                    "name": "CodeLlama-7B-Instruct",
                    "modelId": "codellama/CodeLlama-7B-Instruct-hf",
                    "description": "Specialized for code generation",
                    "size_gb": 14,
                    "tags": ["text-generation", "coding", "instruct"]
                },
                {
                    "name": "Phi-3-mini-4k-instruct",
                    "modelId": "microsoft/Phi-3-mini-4k-instruct",
                    "description": "Small but powerful for coding",
                    "size_gb": 2.5,
                    "tags": ["text-generation", "coding", "instruct"]
                },
                {
                    "name": "DeepSeek-Coder-6.7B-Instruct",
                    "modelId": "deepseek-ai/deepseek-coder-6.7b-instruct",
                    "description": "Excellent for programming tasks",
                    "size_gb": 13,
                    "tags": ["text-generation", "coding", "instruct"]
                }
            ],
            "general_models": [
                {
                    "name": "Llama-3-8B-Instruct",
                    "modelId": "meta-llama/Meta-Llama-3-8B-Instruct",
                    "description": "Good general purpose model",
                    "size_gb": 16,
                    "tags": ["text-generation", "instruct"]
                },
                {
                    "name": "Gemma-2-9B-Instruct",
                    "modelId": "google/gemma-2-9b-it",
                    "description": "Google's efficient model",
                    "size_gb": 18,
                    "tags": ["text-generation", "instruct"]
                }
            ]
        }
    
    def _download_with_progress(self, model_id: str, progress_callback: Optional[Callable] = None):
        """Download model in background thread with progress tracking."""
        try:
            print(f"🔄 Starting download of {model_id}")
            
            # Create model directory
            model_dir = os.path.join(self.models_dir, model_id.replace('/', '_'))
            os.makedirs(model_dir, exist_ok=True)
            
            # Initialize progress
            progress = self.active_downloads[model_id]
            progress.status = "downloading"
            progress.progress_percent = 0.0
            
            # Estimate total size first
            try:
                files = list_repo_files(model_id)
                total_size_bytes = 0
                pytorch_files = []
                
                for file in files:
                    if file.endswith(('.bin', '.safetensors', '.pth')):
                        pytorch_files.append(file)
                        # Rough estimate: assume average file size based on model type
                        if '7b' in model_id.lower():
                            total_size_bytes += 3.5 * 1024**3  # ~3.5GB per file
                        elif '13b' in model_id.lower():
                            total_size_bytes += 7.0 * 1024**3  # ~7GB per file
                        else:
                            total_size_bytes += 2.0 * 1024**3  # ~2GB per file
                
                progress.total_bytes = total_size_bytes
                print(f"📊 Estimated total size: {total_size_bytes / (1024**3):.1f} GB ({len(pytorch_files)} PyTorch files)")
                
            except Exception as e:
                print(f"⚠️ Could not estimate size: {e}")
                progress.total_bytes = 15 * 1024**3  # Default 15GB estimate
            
            # Improved progress simulation based on actual download time
            def update_progress_simulation():
                import time
                start_time = time.time()
                download_start_time = start_time
                
                # Wait a bit for actual download to start
                time.sleep(2)
                
                while progress.status == "downloading" and progress.progress_percent < 0.98:
                    time.sleep(1)
                    elapsed = time.time() - start_time
                    
                    # More realistic progress simulation
                    if elapsed < 30:  # First 30 seconds: slow start
                        progress.progress_percent = min(0.15, elapsed / 200.0)
                    elif elapsed < 300:  # Next 4.5 minutes: steady progress
                        progress.progress_percent = min(0.85, 0.15 + (elapsed - 30) / 600.0)
                    else:  # Final phase: slower progress
                        progress.progress_percent = min(0.98, 0.85 + (elapsed - 300) / 1200.0)
                    
                    # Calculate speed and ETA
                    if progress.total_bytes > 0:
                        downloaded_bytes = progress.progress_percent * progress.total_bytes
                        progress.downloaded_bytes = downloaded_bytes
                        
                        if elapsed > 10:  # Wait for stable speed calculation
                            progress.download_speed = downloaded_bytes / elapsed
                            remaining_bytes = progress.total_bytes - downloaded_bytes
                            if progress.download_speed > 0:
                                progress.eta_seconds = int(remaining_bytes / progress.download_speed)
                    
                    if progress_callback:
                        progress_callback(progress)
            
            # Start progress simulation in a separate thread
            import threading
            progress_thread = threading.Thread(target=update_progress_simulation, daemon=True)
            progress_thread.start()
            
            # Download model files
            snapshot_download(
                repo_id=model_id,
                local_dir=model_dir,
                local_dir_use_symlinks=False,
                resume_download=True
            )
            
            # Mark as completed
            progress.status = "completed"
            progress.progress_percent = 1.0
            
            # Calculate actual downloaded size
            actual_size = 0
            if os.path.exists(model_dir):
                for root, dirs, files in os.walk(model_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        actual_size += os.path.getsize(file_path)
            
            progress.downloaded_bytes = actual_size
            print(f"✅ Successfully downloaded {model_id}")
            print(f"📊 Actual downloaded size: {actual_size / (1024**3):.1f} GB")
            
            # Save to database (without status parameter)
            self.db.add_model(
                model_id=model_id,
                display_name=model_id.split('/')[-1],
                local_path=model_dir,
                model_type="pytorch",
                description=f"Downloaded PyTorch model: {model_id} ({actual_size / (1024**3):.1f} GB)"
            )
            
            # Call final progress callback
            if progress_callback:
                progress_callback(progress)
                
        except Exception as e:
            print(f"❌ Error downloading {model_id}: {e}")
            progress = self.active_downloads.get(model_id)
            if progress:
                progress.status = "error"
                progress.error_message = str(e)
                if progress_callback:
                    progress_callback(progress)
        finally:
            # Clean up
            if model_id in self.active_downloads:
                del self.active_downloads[model_id]
            if model_id in self.download_threads:
                del self.download_threads[model_id]
            if model_id in self.download_locks:
                del self.download_locks[model_id]
    
    def download_pytorch_model(self, model_id: str, progress_callback=None) -> bool:
        """Download a PyTorch model from Hugging Face."""
        try:
            # Initialize progress tracking
            progress = DownloadProgress(model_id)
            self.active_downloads[model_id] = progress
            self.download_locks[model_id] = threading.Lock()
            
            # Start download in background thread
            download_thread = threading.Thread(
                target=self._download_with_progress,
                args=(model_id, progress_callback),
                daemon=True
            )
            self.download_threads[model_id] = download_thread
            download_thread.start()
            
            return True
            
        except Exception as e:
            print(f"❌ Error starting download of {model_id}: {e}")
            return False
    
    def list_downloaded_models(self) -> List[str]:
        """List all downloaded models."""
        downloaded_models = []
        
        if os.path.exists(self.models_dir):
            for item in os.listdir(self.models_dir):
                item_path = os.path.join(self.models_dir, item)
                if os.path.isdir(item_path):
                    # Check if it's a valid model directory
                    if self._is_valid_model_directory(item_path):
                        downloaded_models.append(item)
        
        return downloaded_models
    
    def _is_valid_model_directory(self, directory_path: str) -> bool:
        """Check if a directory contains a valid model."""
        try:
            if not os.path.isdir(directory_path):
                return False
            
            # Check for common model files
            model_files = [
                'config.json',
                'tokenizer.json',
                'tokenizer_config.json'
            ]
            
            # Check for at least one model weight file
            weight_files = [
                'pytorch_model.bin',
                'model.safetensors',
                'model-00001-of-00002.safetensors',
                'pytorch_model-00001-of-00002.bin'
            ]
            
            files = os.listdir(directory_path)
            
            # Must have config.json and at least one weight file
            has_config = any(f in files for f in model_files)
            has_weights = any(f in files for f in weight_files)
            
            return has_config and has_weights
            
        except Exception:
            return False

    def get_model_path(self, model_name: str) -> Optional[str]:
        """Get the full path to a downloaded model."""
        model_path = os.path.join(self.models_dir, model_name)
        if os.path.exists(model_path):
            return model_path
        return None
    
    def delete_model(self, model_name: str) -> bool:
        """Delete a downloaded model."""
        try:
            model_path = os.path.join(self.models_dir, model_name)
            if os.path.exists(model_path):
                import shutil
                shutil.rmtree(model_path)
                print(f"✅ Deleted model: {model_name}")
                
                # Remove from database
                self.db.delete_model(model_name)
                return True
            return False
        except Exception as e:
            print(f"❌ Error deleting model {model_name}: {e}")
            return False
    
    def get_model_info(self, model_name: str) -> Optional[Dict]:
        """Get information about a model."""
        available_models = self.get_available_models()
        
        # Search in coding models
        for category in available_models.values():
            for model in category:
                if model['modelId'].replace('/', '_') == model_name:
                    return model
        
        return None
    
    def estimate_model_size(self, model_id: str) -> Optional[float]:
        """Estimate model size in GB."""
        try:
            files = list_repo_files(model_id)
            total_size = 0
            
            for file in files:
                if file.endswith(('.bin', '.safetensors', '.pth')):
                    # Rough estimate: assume average file size
                    total_size += 2.0  # GB per file
            
            return total_size if total_size > 0 else None
            
        except Exception as e:
            print(f"⚠️ Could not estimate size for {model_id}: {e}")
            return None

    def is_downloading(self, model_id: str) -> bool:
        """Check if a model is currently being downloaded."""
        return model_id in self.active_downloads and self.active_downloads[model_id].status == "downloading"
    
    def is_downloaded(self, model_id: str) -> bool:
        """Check if a model is already downloaded."""
        return self.db.is_model_downloaded(model_id)
    
    def get_download_progress(self, model_id: str) -> Optional[DownloadProgress]:
        """Get current download progress for a model."""
        return self.active_downloads.get(model_id)
    
    def start_download(self, model, progress_callback: Optional[Callable] = None) -> bool:
        """Start downloading a model."""
        # Handle both ModelInfo objects and dictionaries
        if hasattr(model, 'modelId'):
            # ModelInfo object from Hugging Face
            model_id = model.modelId
        elif isinstance(model, dict):
            # Dictionary format
            model_id = model.get('modelId', model.get('model_id', ''))
        else:
            print(f"❌ Unknown model format: {type(model)}")
            return False
        
        # Check if already downloading
        if self.is_downloading(model_id):
            print(f"⚠️ Model {model_id} is already being downloaded")
            return False
        
        # Check if already downloaded
        if self.is_downloaded(model_id):
            print(f"ℹ️ Model {model_id} is already downloaded")
            return False
        
        # Check if model directory already exists (partial download)
        model_dir = os.path.join(self.models_dir, model_id.replace('/', '_'))
        if os.path.exists(model_dir):
            print(f"⚠️ Model directory already exists: {model_dir}")
            print(f"ℹ️ This might be a partial download. The download will resume.")
        
        print(f"Started downloading {model_id}")
        
        # Start the download
        return self.download_pytorch_model(model_id, progress_callback)
    
    def pause_download(self, model_id: str) -> bool:
        """Pause a download."""
        if model_id in self.active_downloads:
            self.active_downloads[model_id].status = "paused"
            print(f"Paused download for {model_id}")
            return True
        return False
    
    def resume_download(self, model_id: str) -> bool:
        """Resume a download."""
        if model_id in self.active_downloads:
            self.active_downloads[model_id].status = "downloading"
            print(f"Resumed download for {model_id}")
            return True
        return False
    
    def cancel_download(self, model_id: str) -> bool:
        """Cancel a download."""
        if model_id in self.active_downloads:
            self.active_downloads[model_id].status = "cancelled"
            print(f"Cancelled download for {model_id}")
            return True
        return False

# Global instance
pytorch_model_downloader = PyTorchModelDownloader() 