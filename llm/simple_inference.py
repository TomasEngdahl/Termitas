#!/usr/bin/env python3
"""
Simple inference module for local LLM chat
"""

import torch
import torch.nn as nn
from typing import List, Dict
import os
from threading import Lock

class SimpleInference:
    """Simple inference engine for local LLM chat."""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.current_model_path = None
        
        # Auto-detect best device
        if torch.cuda.is_available():
            self.device = "cuda"
            print(f"🚀 GPU detected: {torch.cuda.get_device_name(0)}")
        else:
            self.device = "cpu"
            print("🚀 Using CPU (no GPU detected)")
        
        self.lock = Lock()
        
        # General AI assistant system prompt
        self.system_prompt = """
You are a helpful AI assistant that can engage in conversations and help users with various tasks.

**Your capabilities:**
- Answer questions and provide information
- Help with problem solving and analysis
- Explain complex topics in simple terms
- Assist with creative writing and brainstorming
- Provide technical support and guidance
- Help with learning and education

**Response style:**
- Be helpful, friendly, and engaging
- Provide clear and informative responses
- Ask clarifying questions when needed
- Offer multiple perspectives when appropriate
- Be honest about limitations

Be conversational and helpful in your responses.
"""
        
        print(f"🚀 SimpleInference initialized on device: {self.device}")
    
    def set_model(self, model_path: str) -> bool:
        """Load the real model with fallback to mock if needed."""
        try:
            with self.lock:
                print(f"🔄 Loading model: {model_path}")
                
                # Check if model directory exists
                if not os.path.exists(model_path):
                    print(f"❌ Model directory does not exist: {model_path}")
                    return False
                
                print(f"✅ Model directory found")
                
                # Try to load the real model
                try:
                    from transformers import AutoTokenizer, AutoModelForCausalLM
                    
                    print(f"🔄 Loading real tokenizer...")
                    self.tokenizer = AutoTokenizer.from_pretrained(model_path)
                    print(f"✅ Real tokenizer loaded successfully")
                    
                    print(f"🔄 Loading real model...")
                    
                    # Try loading with GPU first, then fallback to CPU
                    try:
                        print(f"🔄 Loading model with {self.device.upper()}...")
                        self.model = AutoModelForCausalLM.from_pretrained(
                            model_path,
                            torch_dtype=torch.float16,
                            trust_remote_code=True,
                            low_cpu_mem_usage=True,
                            device_map="auto" if self.device == "cuda" else "cpu"
                        )
                        print(f"✅ Real model loaded successfully on {self.device.upper()}")
                        self.current_model_path = model_path
                        return True
                    except Exception as e:
                        print(f"⚠️ {self.device.upper()} loading failed: {e}")
                        
                        # Check if it's an RTX 5090 compatibility issue
                        if "RTX 5090" in str(e) or "sm_120" in str(e):
                            print(f"💡 RTX 5090 detected - PyTorch 2.7.0 doesn't support sm_120")
                            print(f"💡 This is expected behavior, falling back to CPU")
                        
                        # Fallback to CPU if GPU failed
                        if self.device == "cuda":
                            print(f"🔄 Falling back to CPU...")
                            try:
                                self.device = "cpu"
                                self.model = AutoModelForCausalLM.from_pretrained(
                                    model_path,
                                    torch_dtype=torch.float16,
                                    trust_remote_code=True,
                                    low_cpu_mem_usage=True,
                                    device_map="cpu"
                                )
                                print(f"✅ Real model loaded successfully on CPU (fallback)")
                                self.current_model_path = model_path
                                return True
                            except Exception as cpu_e:
                                print(f"⚠️ CPU fallback also failed: {cpu_e}")
                                return False
                        else:
                            return False
                    
                except Exception as e:
                    print(f"⚠️ Real model loading failed: {e}")
                    return False
                
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return False
    
    def generate_response(self, messages: List[Dict], max_length: int = 512) -> str:
        """Generate a response using the real model or fallback to mock."""
        print(f"🔄 Generating response with {len(messages)} messages")
        print(f"🔄 Model loaded: {self.model is not None}")
        
        if not self.model:
            return "❌ No model loaded. Please select a model first."
        
        try:
            with self.lock:
                # Use real model
                print(f"🔄 Using real model for inference")
                return self._generate_real_response(messages, max_length)
                
        except Exception as e:
            print(f"❌ Error generating response: {e}")
            return f"❌ Error generating response: {str(e)}"
    
    def _generate_real_response(self, messages: List[Dict], max_length: int = 512) -> str:
        """Generate response using the real model."""
        try:
            # Convert messages to prompt format
            prompt = self._format_messages_to_prompt(messages)
            print(f"🔄 Generated prompt: {prompt[:200]}...")
            
            # Tokenize input
            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
            print(f"🔄 Input tokens shape: {inputs['input_ids'].shape}")
            
            # Move inputs to device
            if self.device == "cuda":
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=1024,  # Increased from max_length for longer responses
                    do_sample=True,
                    temperature=0.8,
                    top_p=0.95,
                    repetition_penalty=1.1,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    no_repeat_ngram_size=3,
                )
            
            # Decode response
            response = self.tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
            
            # Clean up response
            response = response.strip()
            if not response:
                # Try a simpler approach
                try:
                    # Generate with different parameters
                    outputs = self.model.generate(
                        **inputs,
                        max_new_tokens=100,
                        do_sample=True,
                        temperature=0.9,
                        top_p=0.9,
                        pad_token_id=self.tokenizer.eos_token_id,
                        eos_token_id=self.tokenizer.eos_token_id,
                    )
                    response = self.tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
                    response = response.strip()
                except:
                    response = "I'm sorry, I couldn't generate a response. Please try again."
            
            if not response:
                response = "I'm sorry, I couldn't generate a response. Please try again."
            
            print(f"✅ Generated real response: {len(response)} characters")
            return response
            
        except Exception as e:
            print(f"❌ Error with real model: {e}")
            return f"❌ Error with real model: {str(e)}"
    
    def _format_messages_to_prompt(self, messages: List[Dict]) -> str:
        """Format conversation messages into a prompt string."""
        prompt = ""
        
        # Add system prompt if not present
        has_system = any(msg.get('role') == 'system' for msg in messages)
        if not has_system:
            prompt += f"System: {self.system_prompt}\n\n"
        
        for message in messages:
            role = message.get('role', '')
            content = message.get('content', '')
            
            if role == 'user':
                prompt += f"User: {content}\n"
            elif role == 'assistant':
                prompt += f"Assistant: {content}\n"
            elif role == 'system':
                prompt += f"System: {content}\n"
        
        # Add assistant prefix for the response
        prompt += "Assistant: "
        
        return prompt
    

    

    
    def get_model_status(self) -> Dict:
        """Get current model status and device info."""
        return {
            "model_loaded": self.model is not None,
            "model_path": self.current_model_path,
            "device": self.device,
            "device_name": self.device,
            "platform": platform.system(),
            "memory_usage": {"device": "CPU"}
        }



# Global instance
simple_inference = SimpleInference() 