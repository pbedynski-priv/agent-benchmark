#!/usr/bin/env python3
"""Quick test run with 3 models and 5 tasks to validate the benchmark."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from code_benchmark.config import Config
from code_benchmark.api_client import APIClient
from code_benchmark.task_loader import TaskLoader
from code_benchmark.reviewer import Reviewer
from code_benchmark.scorer import Scorer

async def quick_test():
    """Quick test with 3 models and 5 tasks."""
    config = Config.load()
    task_loader = TaskLoader(config.tasks_dir)
    scorer = Scorer(config.scoring.weights)
    
    # Load just 5 tasks (mix of categories)
    all_tasks = task_loader.load_all()
    test_tasks = [
        next(t for t in all_tasks if t.id == "tool-terminal-basic"),
        next(t for t in all_tasks if t.id == "instruction-multistep"),
        next(t for t in all_tasks if t.id == "memory-extract-facts"),
        next(t for t in all_tasks if t.id == "planning-webapp"),
        next(t for t in all_tasks if t.id == "review-find-bugs"),
    ]
    
    # Test 3 models (one from each tier)
    test_models = [
        "qwen3.7-plus",      # Balanced
        "deepseek-v4-flash", # Fast/Cheap
        "deepseek-v4-pro",   # Reasoning
    ]
    
    print(f"Quick Test: {len(test_models)} models × {len(test_tasks)} tasks = {len(test_models) * len(test_tasks)} API calls\n")
    
    for model in test_models:
        print(f"\n{'='*60}")
        print(f"Testing: {model}")
        print(f"{'='*60}")
        
        async with APIClient(config) as client:
            reviewer = Reviewer(config, client)
            
            for task in test_tasks:
                print(f"  {task.id}...", end=" ", flush=True)
                
                try:
                    response = await client.call_model(
                        model=model,
                        prompt=task.prompt,
                        system="You are a helpful AI assistant.",
                        temperature=0.7,
                        max_tokens=2048,
                    )
                    
                    review = await reviewer.review_code(
                        code=response,
                        task=task,
                        model=model,
                    )
                    
                    scores = scorer.calculate_scores(review)
                    total_score = scorer.calculate_total(scores)
                    
                    print(f"✓ {total_score:.2f}")
                    
                except Exception as e:
                    print(f"✗ Error: {str(e)[:50]}")
    
    print(f"\n✓ Quick test complete!")

if __name__ == "__main__":
    asyncio.run(quick_test())
