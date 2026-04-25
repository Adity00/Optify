from unsloth import FastLanguageModel

def validate_model():
    print("Loading model Qwen/Qwen2.5-1.5B-Instruct...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name="Qwen/Qwen2.5-1.5B-Instruct",
        max_seq_length=2048,
        load_in_4bit=True,
    )
    
    print("Configuring LoRA...")
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
        use_gradient_checkpointing=True,
    )
    
    print("Model and LoRA loaded successfully!")
    print("Running inference test...")
    
    FastLanguageModel.for_inference(model)
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Return a JSON object with a 'status' key."}
    ]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    outputs = model.generate(**inputs, max_new_tokens=50)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    print("\nModel Output:")
    print(response)

if __name__ == "__main__":
    validate_model()
