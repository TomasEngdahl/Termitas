import threading
import time
import os
from pathlib import Path
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass
from huggingface_hub import snapshot_download, ModelInfo
from huggingface_hub.utils import HfHubHTTPError, RepositoryNotFoundError
from database.models_db import get_db, get_models_dir

@dataclass
class DownloadProgress:
    """Data class for download progress information."""
    model_id: str
    progress_percent: float = 0.0
    downloaded_bytes: int = 0
    total_bytes: int = 0
    download_speed: float = 0.0  # bytes per second
    eta_seconds: Optional[int] = None
    status: str = 'starting'  # 'starting', 'downloading', 'paused', 'completed', 'failed'
    error_message: Optional[str] = None

class ModelDownloader:
    """Handles downloading models from Hugging Face with progress tracking and pause/resume."""
    
    def __init__(self):
        self.db = get_db()
        self.active_downloads: Dict[str, Dict] = {}  # model_id -> download_info
        self.progress_callbacks: Dict[str, Callable] = {}  # model_id -> callback function
        
    def is_downloading(self, model_id: str) -> bool:
        """Check if a model is currently being downloaded."""
        return model_id in self.active_downloads
    
    def is_downloaded(self, model_id: str) -> bool:
        """Check if a model is already downloaded."""
        return self.db.is_model_downloaded(model_id)
    
    def get_download_progress(self, model_id: str) -> Optional[DownloadProgress]:
        """Get current download progress for a model."""
        if model_id not in self.active_downloads:
            return None
        
        download_info = self.active_downloads[model_id]
        return download_info.get('progress')
    
    def start_download(self, model: ModelInfo, progress_callback: Optional[Callable] = None) -> bool:
        """Start downloading a model."""
        model_id = model.modelId
        
        # Check if already downloading
        if self.is_downloading(model_id):
            print(f"Model {model_id} is already being downloaded")
            return False
        
        # Check if already downloaded
        if self.is_downloaded(model_id):
            print(f"Model {model_id} is already downloaded")
            return False
        
        # Setup download tracking
        download_id = self.db.start_download(model_id)
        if download_id == -1:
            return False
        
        # Create download directory
        model_dir = get_models_dir() / model_id.replace('/', '_')
        model_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize progress tracking
        progress = DownloadProgress(model_id=model_id, status='starting')
        
        download_info = {
            'download_id': download_id,
            'model': model,
            'local_path': model_dir,
            'progress': progress,
            'thread': None,
            'stop_event': threading.Event(),
            'pause_event': threading.Event(),
            'start_time': time.time(),
            'last_update': time.time()
        }
        
        self.active_downloads[model_id] = download_info
        
        if progress_callback:
            self.progress_callbacks[model_id] = progress_callback
        
        # Start download in background thread
        download_thread = threading.Thread(
            target=self._download_worker,
            args=(model_id,),
            daemon=True
        )
        download_info['thread'] = download_thread
        download_thread.start()
        
        return True
    
    def pause_download(self, model_id: str) -> bool:
        """Pause an active download."""
        if model_id not in self.active_downloads:
            return False
        
        download_info = self.active_downloads[model_id]
        download_info['pause_event'].set()
        download_info['progress'].status = 'paused'
        
        # Update database
        self.db.pause_download(download_info['download_id'])
        
        # Notify UI
        self._notify_progress(model_id)
        
        return True
    
    def resume_download(self, model_id: str) -> bool:
        """Resume a paused download."""
        if model_id not in self.active_downloads:
            return False
        
        download_info = self.active_downloads[model_id]
        download_info['pause_event'].clear()
        download_info['progress'].status = 'downloading'
        
        # Update database
        self.db.resume_download(download_info['download_id'])
        
        # Notify UI
        self._notify_progress(model_id)
        
        return True
    
    def cancel_download(self, model_id: str) -> bool:
        """Cancel an active download."""
        if model_id not in self.active_downloads:
            return False
        
        download_info = self.active_downloads[model_id]
        download_info['stop_event'].set()
        download_info['progress'].status = 'cancelled'
        
        # Mark as failed in database
        self.db.complete_download(
            download_info['download_id'], 
            success=False, 
            error_message="Download cancelled by user"
        )
        
        # Clean up
        self._cleanup_download(model_id)
        
        return True
    
    def _download_worker(self, model_id: str):
        """Background worker that handles the actual download."""
        download_info = self.active_downloads[model_id]
        model = download_info['model']
        local_path = download_info['local_path']
        progress = download_info['progress']
        stop_event = download_info['stop_event']
        pause_event = download_info['pause_event']
        
        try:
            progress.status = 'downloading'
            self._notify_progress(model_id)
            
            # Custom progress tracking for huggingface_hub
            def progress_hook(downloaded: int, total: int):
                if stop_event.is_set():
                    raise InterruptedError("Download cancelled")
                
                # Handle pause
                while pause_event.is_set() and not stop_event.is_set():
                    time.sleep(0.1)
                
                if stop_event.is_set():
                    raise InterruptedError("Download cancelled")
                
                # Update progress
                current_time = time.time()
                elapsed = current_time - download_info['last_update']
                
                if elapsed >= 0.5:  # Update every 500ms
                    progress.downloaded_bytes = downloaded
                    progress.total_bytes = total
                    progress.progress_percent = (downloaded / total) * 100 if total > 0 else 0
                    
                    # Calculate speed
                    if elapsed > 0:
                        bytes_since_last = downloaded - getattr(progress, '_last_downloaded', 0)
                        progress.download_speed = bytes_since_last / elapsed
                        progress._last_downloaded = downloaded
                    
                    # Calculate ETA
                    if progress.download_speed > 0 and total > downloaded:
                        remaining_bytes = total - downloaded
                        progress.eta_seconds = int(remaining_bytes / progress.download_speed)
                    
                    # Update database
                    self.db.update_download_progress(
                        download_info['download_id'],
                        progress.progress_percent,
                        progress.downloaded_bytes,
                        progress.total_bytes,
                        progress.download_speed,
                        progress.eta_seconds
                    )
                    
                    # Notify UI
                    self._notify_progress(model_id)
                    download_info['last_update'] = current_time
            
            # Download the model using huggingface_hub
            # Start progress monitoring in parallel
            print(f"Starting download of {model_id} to {local_path}")
            
            # Start progress monitoring thread
            monitor_thread = threading.Thread(
                target=self._monitor_download_progress,
                args=(model_id, local_path),
                daemon=True
            )
            monitor_thread.start()
            
            # Start the actual download
            downloaded_path = snapshot_download(
                repo_id=model_id,
                local_dir=local_path,
                local_dir_use_symlinks=False,
                resume_download=True
            )
            
            print(f"snapshot_download completed for {model_id}")
            
            # Stop progress monitoring
            stop_event.set()
            monitor_thread.join(timeout=5)  # Wait for monitor to finish with longer timeout
            
            print(f"Progress monitoring stopped for {model_id}")
            
            # Download completed successfully
            progress.status = 'completed'
            progress.progress_percent = 100.0
            
            # Calculate final size
            total_size = self._calculate_directory_size(local_path)
            progress.downloaded_bytes = total_size
            progress.total_bytes = total_size  # Update total to actual size
            
            # Final progress update
            self._notify_progress(model_id)
            
            # Add model to database with size information
            self.db.add_model(
                model_id=model_id,
                display_name=model_id.split('/')[-1],
                local_path=str(local_path),
                parameter_count=self._extract_param_count(model),
                model_type=getattr(model, 'pipeline_tag', 'text-generation'),
                description=self._get_model_description(model),
                downloads_count=getattr(model, 'downloads', 0),
                likes_count=getattr(model, 'likes', 0),
                metadata={
                    'total_size_bytes': total_size,
                    'download_duration': time.time() - download_info['start_time'],
                    'huggingface_model_id': model_id
                }
            )
            
            # Update the database model record with the actual size
            try:
                with self.db.get_connection() as conn:
                    conn.execute(
                        'UPDATE models SET size_bytes = ? WHERE model_id = ?',
                        (total_size, model_id)
                    )
                    conn.commit()
            except Exception as e:
                print(f"Error updating model size in database: {e}")
            
            # Mark download as completed
            self.db.complete_download(download_info['download_id'], success=True)
            
            print(f"Successfully downloaded {model_id}")
            
        except InterruptedError:
            print(f"Download of {model_id} was cancelled")
            progress.status = 'cancelled'
            
        except (HfHubHTTPError, RepositoryNotFoundError) as e:
            error_msg = f"Hugging Face error: {str(e)}"
            print(f"Download of {model_id} failed: {error_msg}")
            progress.status = 'failed'
            progress.error_message = error_msg
            self.db.complete_download(download_info['download_id'], success=False, error_message=error_msg)
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"Download of {model_id} failed: {error_msg}")
            progress.status = 'failed'
            progress.error_message = error_msg
            self.db.complete_download(download_info['download_id'], success=False, error_message=error_msg)
        
        finally:
            # Final progress notification
            self._notify_progress(model_id)
            
            # Clean up
            self._cleanup_download(model_id)
    
    def _monitor_download_progress(self, model_id: str, local_path: Path):
        """Monitor download progress by checking directory size."""
        download_info = self.active_downloads.get(model_id)
        if not download_info:
            return
        
        progress = download_info['progress']
        stop_event = download_info['stop_event']
        pause_event = download_info['pause_event']
        
        last_size = 0
        last_time = time.time()
        stable_count = 0
        speed_samples = []  # For smoother speed calculation
        
        # Get initial estimate of model size
        estimated_size = self._estimate_model_size(download_info['model'])
        if progress.total_bytes == 0:
            progress.total_bytes = estimated_size
        
        print(f"Monitoring download progress for {model_id}...")
        
        while not stop_event.is_set() and progress.status in ['downloading', 'starting']:
            time.sleep(0.5)  # More frequent updates
            
            # Handle pause
            while pause_event.is_set() and not stop_event.is_set():
                time.sleep(0.1)
                continue
            
            if stop_event.is_set():
                print(f"Stop event set - ending monitoring for {model_id}")
                break
            
            current_size = self._calculate_directory_size(local_path)
            current_time = time.time()
            
            if current_size > last_size:
                # Update progress
                progress.downloaded_bytes = current_size
                
                # Calculate progress percentage
                if progress.total_bytes > 0:
                    # If current size exceeds our estimate, update total_bytes
                    if current_size > progress.total_bytes:
                        progress.total_bytes = current_size + (current_size * 0.1)  # Add 10% buffer
                        print(f"Updated total size estimate to {progress.total_bytes/(1024*1024):.1f}MB")
                    
                    progress.progress_percent = (current_size / progress.total_bytes) * 100
                else:
                    # If we don't know total size, show relative progress
                    progress.progress_percent = min(current_size / (100 * 1024 * 1024) * 100, 95.0)  # Show progress up to 100MB, cap at 95%
                
                # Calculate speed (smoothed over last few samples)
                elapsed = current_time - last_time
                if elapsed > 0:
                    speed = (current_size - last_size) / elapsed
                    speed_samples.append(speed)
                    if len(speed_samples) > 5:
                        speed_samples.pop(0)  # Keep only last 5 samples
                    progress.download_speed = sum(speed_samples) / len(speed_samples)
                
                # Calculate ETA
                if progress.download_speed > 0 and progress.total_bytes > current_size:
                    remaining_bytes = progress.total_bytes - current_size
                    progress.eta_seconds = int(remaining_bytes / progress.download_speed)
                
                # Update database and UI
                self.db.update_download_progress(
                    download_info['download_id'],
                    progress.progress_percent,
                    progress.downloaded_bytes,
                    progress.total_bytes,
                    progress.download_speed,
                    progress.eta_seconds
                )
                
                self._notify_progress(model_id)
                
                last_size = current_size
                last_time = current_time
                stable_count = 0
                
                print(f"Progress: {progress.progress_percent:.1f}% - {current_size/(1024*1024):.1f}MB - {progress.download_speed/(1024*1024):.1f} MB/s")
            else:
                stable_count += 1
                # If size hasn't changed for 10 seconds and we have substantial data, likely complete
                if stable_count >= 20 and current_size > (50 * 1024 * 1024):  # 50MB minimum
                    print(f"Download appears complete (stable for {stable_count/2:.1f} seconds, size: {current_size/(1024*1024):.1f}MB)")
                    # Set progress to 100% and mark complete
                    progress.progress_percent = 100.0
                    progress.total_bytes = current_size  # Final size is actual size
                    progress.status = 'completed'
                    self._notify_progress(model_id)
                    break
        
        print(f"Progress monitoring ended for {model_id}")
    
    def _calculate_directory_size(self, path: Path) -> int:
        """Calculate total size of directory in bytes."""
        try:
            total_size = 0
            for file_path in path.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            return total_size
        except Exception:
            return 0
    
    def _estimate_model_size(self, model: ModelInfo) -> int:
        """Estimate model size in bytes."""
        try:
            # Try to get from safetensors metadata
            safetensors_data = getattr(model, 'safetensors', None)
            if safetensors_data and isinstance(safetensors_data, dict):
                total_params = safetensors_data.get('total', 0)
                if total_params:
                    # Rough estimate: 2 bytes per parameter (FP16)
                    return total_params * 2
            
            # Fallback: estimate from model name
            model_name = model.modelId.lower()
            if '70b' in model_name or '72b' in model_name:
                return 140_000_000_000  # ~140GB
            elif '33b' in model_name or '34b' in model_name:
                return 68_000_000_000   # ~68GB
            elif '13b' in model_name:
                return 26_000_000_000   # ~26GB
            elif '7b' in model_name:
                return 14_000_000_000   # ~14GB
            elif '3b' in model_name:
                return 6_000_000_000    # ~6GB
            else:
                return 10_000_000_000   # ~10GB default
                
        except Exception:
            return 10_000_000_000  # Default to ~10GB
    
    def _extract_param_count(self, model: ModelInfo) -> Optional[int]:
        """Extract parameter count from model."""
        try:
            safetensors_data = getattr(model, 'safetensors', None)
            if safetensors_data and isinstance(safetensors_data, dict):
                return safetensors_data.get('total', None)
            return None
        except Exception:
            return None
    
    def _get_model_description(self, model: ModelInfo) -> str:
        """Get model description."""
        try:
            from hf.list import get_model_description
            return get_model_description(model)
        except Exception:
            return "AI Model"
    
    def _notify_progress(self, model_id: str):
        """Notify UI of progress update."""
        if model_id in self.progress_callbacks:
            try:
                callback = self.progress_callbacks[model_id]
                progress = self.active_downloads[model_id]['progress']
                callback(progress)
            except Exception as e:
                print(f"Error in progress callback: {e}")
    
    def _cleanup_download(self, model_id: str):
        """Clean up download tracking."""
        if model_id in self.active_downloads:
            del self.active_downloads[model_id]
        
        if model_id in self.progress_callbacks:
            del self.progress_callbacks[model_id]

# Global downloader instance
_downloader_instance = None

def get_downloader() -> ModelDownloader:
    """Get the global downloader instance."""
    global _downloader_instance
    if _downloader_instance is None:
        _downloader_instance = ModelDownloader()
    return _downloader_instance