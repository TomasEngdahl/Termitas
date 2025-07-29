from huggingface_hub import list_models, ModelInfo
from typing import List

def list_models_hf(limit: int = 20, filter_for_coding: bool = False, search_term: str = "") -> List[ModelInfo]:
    """List models from Hugging Face Hub with flexible search options."""
    try:
        if search_term:
            # Direct search with user's term
            try:
                models_generator = list_models(
                    search=search_term,
                    sort="downloads", 
                    direction=-1,
                    limit=limit * 2
                )
                models = list(models_generator)
                return models[:limit]
            except Exception as e:
                print(f"Search failed: {e}")
                return []
                
        elif filter_for_coding:
            # Legacy coding filter (keeping for compatibility)
            try:
                models_generator = list_models(
                    task="text-generation",
                    search="qwen OR mistral OR llama OR code OR coding OR instruct OR chat",
                    sort="downloads", 
                    direction=-1,
                    limit=limit * 2
                )
                models = list(models_generator)
            except:
                # Fallback to general search if specific search fails
                models_generator = list_models(
                    sort="downloads", 
                    direction=-1,
                    limit=limit * 3
                )
                models = list(models_generator)
                
            # Filter the results (more inclusive now)
            filtered_models = []
            for model in models:
                if is_coding_model(model):
                    filtered_models.append(model)
                if len(filtered_models) >= limit:
                    break
            
            # If we still don't have enough, be less strict
            if len(filtered_models) < 5:
                for model in models:
                    if is_popular_model(model) and model not in filtered_models:
                        filtered_models.append(model)
                    if len(filtered_models) >= limit:
                        break
                        
            return filtered_models
        else:
            # General popular models
            models_generator = list_models(
                sort="downloads", 
                direction=-1,
                limit=limit * 2
            )
            models = list(models_generator)
            return models[:limit]
        
    except ImportError as e:
        print(f"Import Error - huggingface_hub not installed properly: {e}")
        return []
    except Exception as e:
        print(f"Error listing models: {e}")
        return []

def is_coding_model(model: ModelInfo) -> bool:
    """Check if a model is suitable for coding/terminal tasks."""
    try:
        model_name = model.modelId.lower()
        tags = [tag.lower() for tag in (model.tags or [])]
        
        # Popular coding model names
        popular_coding_models = {
            'qwen', 'mistral', 'llama', 'codellama', 'starcoder', 'magicoder',
            'deepseek', 'wizardcoder', 'phind', 'dolphin', 'openchat',
            'nous', 'mixtral', 'gemma', 'phi'
        }
        
        # Coding-related keywords  
        coding_keywords = {
            'code', 'coder', 'coding', 'programmer', 'terminal', 'bash', 'shell', 
            'cli', 'command', 'linux', 'unix', 'python', 'javascript', 'instruct',
            'chat', 'assistant', 'wizard'
        }
        
        # Check for popular coding model names
        if any(model in model_name for model in popular_coding_models):
            return True
            
        # Check for coding keywords in model name
        if any(keyword in model_name for keyword in coding_keywords):
            return True
        
        # Check tags
        if any(keyword in tag for tag in tags for keyword in coding_keywords):
            return True
        
        return False
    except:
        return False

def is_popular_model(model: ModelInfo) -> bool:
    """Check if this is a popular/well-known model that's likely good for coding."""
    try:
        model_name = model.modelId.lower()
        
        # Well-known model families
        popular_families = {
            'qwen', 'mistral', 'llama', 'mixtral', 'gemma', 'phi', 'deepseek',
            'nous', 'dolphin', 'openchat', 'wizardlm', 'vicuna', 'alpaca'
        }
        
        # Check if model contains any popular family name
        return any(family in model_name for family in popular_families)
    except:
        return False

def format_model_size(param_count) -> str:
    """Format parameter count in a human-readable way."""
    try:
        if param_count is None:
            return "Unknown size"
        
        if param_count >= 1_000_000_000:
            return f"{param_count / 1_000_000_000:.1f}B"
        elif param_count >= 1_000_000:
            return f"{param_count / 1_000_000:.0f}M"
        elif param_count >= 1_000:
            return f"{param_count / 1_000:.0f}K"
        else:
            return str(param_count)
    except:
        return "Unknown size"

def format_downloads(downloads) -> str:
    """Format download count in a human-readable way."""
    try:
        if downloads is None:
            return "0"
        
        if downloads >= 1_000_000:
            return f"{downloads / 1_000_000:.1f}M"
        elif downloads >= 1_000:
            return f"{downloads / 1_000:.0f}K"
        else:
            return str(downloads)
    except:
        return "0"

def get_model_description(model: ModelInfo) -> str:
    """Extract a short description from model tags or card."""
    try:
        model_name = model.modelId.lower()
        
        # Specific model descriptions
        if 'qwen' in model_name:
            return "Chat & Code Assistant • Alibaba's Qwen"
        elif 'mistral' in model_name or 'mixtral' in model_name:
            return "Chat & Code Assistant • Mistral AI"
        elif 'llama' in model_name:
            return "Chat & Code Assistant • Meta's Llama"
        elif 'gemma' in model_name:
            return "Chat & Code Assistant • Google's Gemma"
        elif 'phi' in model_name:
            return "Chat & Code Assistant • Microsoft's Phi"
        elif 'deepseek' in model_name:
            return "Code Specialist • DeepSeek"
        elif 'starcoder' in model_name:
            return "Code Generation • StarCoder"
        elif 'magicoder' in model_name:
            return "Code Generation • MagiCoder"
        
        # Get primary task from pipeline_tag
        task_descriptions = {
            'text-generation': 'Text & Code Generation',
            'text-to-text-generation': 'Text Processing',
            'conversational': 'Chat Assistant',
            'question-answering': 'Question Answering',
            'fill-mask': 'Text Completion'
        }
        
        primary_task = task_descriptions.get(getattr(model, 'pipeline_tag', None), 'General Model')
        
        # Add coding specialty if detected
        if is_coding_model(model):
            return f"{primary_task} • Coding Capable"
        
        return primary_task
    except:
        return "General Model"

def test_hf_connection():
    """Quick test function to check if HF API works"""
    try:
        models = list(list_models(limit=2))
        return len(models) > 0
    except Exception:
        return False

# Test connection when module is imported
if __name__ != "__main__":
    test_hf_connection()

