from trl import GRPOConfig, GRPOTrainer
from unsloth import FastLanguageModel
import torch
from .dataset import build_dataset
from ..reward.correctness import calculate_correctness_reward
from ..reward.efficiency import calculate_efficiency_reward
from ..reward.cleanliness import calculate_cleanliness_reward

def main():
    max_seq_length = 2048
    lora_rank = 16

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name="Qwen/Qwen2.5-1.5B-Instruct",
        max_seq_length=max_seq_length,
        dtype=None,
        load_in_4bit=True,
    )

    model = FastLanguageModel.get_peft_model(
        model,
        r=lora_rank,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_alpha=lora_rank,
        use_gradient_checkpointing="unsloth", 
        random_state=3407,
    )

    dataset = build_dataset()

    def correctness_reward(prompts, completions, **kwargs):
        # Extract code and evaluate via codeforge_env
        rewards = []
        for completion in completions:
            # Placeholder for actual environment interaction
            rewards.append(1.0 if "def" in completion else 0.0)
        return rewards

    def cleanliness_reward(prompts, completions, **kwargs):
        rewards = []
        for completion in completions:
            rewards.append(calculate_cleanliness_reward(completion))
        return rewards

    training_args = GRPOConfig(
        output_dir="outputs",
        learning_rate=2e-5,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        max_prompt_length=512,
        max_completion_length=1536,
        num_train_epochs=1,
        save_steps=100,
        max_grad_norm=0.1,
        report_to="none",
    )

    trainer = GRPOTrainer(
        model=model,
        reward_funcs=[correctness_reward, cleanliness_reward],
        args=training_args,
        train_dataset=dataset,
    )

    trainer.train()

if __name__ == "__main__":
    main()
