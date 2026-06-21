#!/usr/bin/env python3
"""Run comprehensive Hermes model optimization benchmark.

Tests all 13 OpenCode Go models across 70 tasks to determine
optimal model assignments for each Hermes agent role.
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from code_benchmark.config import Config
from code_benchmark.api_client import APIClient
from code_benchmark.task_loader import TaskLoader
from code_benchmark.reviewer import Reviewer
from code_benchmark.scorer import Scorer

# All 13 OpenCode Go models
ALL_MODELS = [
    # Reasoning Models (expensive)
    "deepseek-v4-pro",
    "mimo-v2.5-pro",
    "qwen3.7-max",
    
    # Balanced Models (medium cost)
    "qwen3.7-plus",
    "qwen3.6-plus",
    "kimi-k2.6",
    "kimi-k2.7",
    "glm-5.1",
    "glm-5.2",
    
    # Fast/Cheap Models
    "deepseek-v4-flash",
    "mimo-v2.5",
    "minimax-m2.7",
    "minimax-m3",
]

# Model pricing (per 1M tokens)
MODEL_PRICING = {
    "deepseek-v4-pro": {"input": 1.74, "output": 3.48, "cache_read": 0.0145},
    "mimo-v2.5-pro": {"input": 1.74, "output": 3.48, "cache_read": 0.0145},
    "qwen3.7-max": {"input": 2.50, "output": 7.50, "cache_read": 0.50},
    "qwen3.7-plus": {"input": 0.40, "output": 1.60, "cache_read": 0.04},
    "qwen3.6-plus": {"input": 0.50, "output": 3.00, "cache_read": 0.05},
    "kimi-k2.6": {"input": 0.95, "output": 4.00, "cache_read": 0.16},
    "kimi-k2.7": {"input": 0.95, "output": 4.00, "cache_read": 0.19},
    "glm-5.1": {"input": 1.40, "output": 4.40, "cache_read": 0.26},
    "glm-5.2": {"input": 1.40, "output": 4.40, "cache_read": 0.26},
    "deepseek-v4-flash": {"input": 0.14, "output": 0.28, "cache_read": 0.0028},
    "mimo-v2.5": {"input": 0.14, "output": 0.28, "cache_read": 0.0028},
    "minimax-m2.7": {"input": 0.30, "output": 1.20, "cache_read": 0.06},
    "minimax-m3": {"input": 0.30, "output": 1.20, "cache_read": 0.06},
}

async def run_benchmark():
    """Run comprehensive benchmark across all models and tasks."""
    config = Config.load()
    task_loader = TaskLoader(config.tasks_dir)
    scorer = Scorer(config.scoring.weights)
    
    # Load all tasks
    all_tasks = task_loader.load_all()
    print(f"Loaded {len(all_tasks)} tasks")
    
    # Initialize results
    results = {
        "timestamp": datetime.now().isoformat(),
        "total_tasks": len(all_tasks),
        "total_models": len(ALL_MODELS),
        "models": {},
        "categories": {},
    }
    
    # Test each model
    for model_idx, model in enumerate(ALL_MODELS, 1):
        print(f"\n{'='*60}")
        print(f"Testing model {model_idx}/{len(ALL_MODELS)}: {model}")
        print(f"{'='*60}")
        
        model_results = {
            "tasks": {},
            "category_scores": {},
            "total_score": 0.0,
            "total_time_ms": 0,
            "estimated_cost": 0.0,
        }
        
        async with APIClient(config) as client:
            reviewer = Reviewer(config, client)
            
            # Test each task
            for task_idx, task in enumerate(all_tasks, 1):
                print(f"  [{task_idx}/{len(all_tasks)}] {task.id}...", end=" ", flush=True)
                
                start_time = datetime.now()
                
                try:
                    # Get model response
                    response = await client.call_model(
                        model=model,
                        prompt=task.prompt,
                        system="You are a helpful AI assistant.",
                        temperature=0.7,
                        max_tokens=2048,
                    )
                    
                    # Review the response
                    review = await reviewer.review_code(
                        code=response,
                        task=task,
                        model=model,
                    )
                    
                    # Calculate scores
                    scores = scorer.calculate_scores(review)
                    total_score = scorer.calculate_total(scores)
                    
                    duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                    
                    # Estimate cost (rough approximation)
                    input_tokens = len(task.prompt) // 4  # rough estimate
                    output_tokens = len(response) // 4
                    pricing = MODEL_PRICING[model]
                    cost = (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000
                    
                    model_results["tasks"][task.id] = {
                        "score": total_score,
                        "dimension_scores": scores,
                        "duration_ms": duration_ms,
                        "estimated_cost": cost,
                        "response_length": len(response),
                    }
                    
                    model_results["total_time_ms"] += duration_ms
                    model_results["estimated_cost"] += cost
                    
                    print(f"✓ {total_score:.2f} ({duration_ms}ms)")
                    
                except Exception as e:
                    print(f"✗ Error: {e}")
                    model_results["tasks"][task.id] = {
                        "score": 0.0,
                        "error": str(e),
                        "duration_ms": 0,
                    }
        
        # Calculate category averages
        category_totals = {}
        category_counts = {}
        for task_id, task_result in model_results["tasks"].items():
            task = next(t for t in all_tasks if t.id == task_id)
            category = task.category
            
            if category not in category_totals:
                category_totals[category] = 0.0
                category_counts[category] = 0
            
            category_totals[category] += task_result["score"]
            category_counts[category] += 1
        
        for category in category_totals:
            model_results["category_scores"][category] = (
                category_totals[category] / category_counts[category]
            )
        
        # Calculate overall average
        valid_scores = [t["score"] for t in model_results["tasks"].values() if "score" in t]
        if valid_scores:
            model_results["total_score"] = sum(valid_scores) / len(valid_scores)
        
        results["models"][model] = model_results
        
        print(f"\n{model} Summary:")
        print(f"  Average Score: {model_results['total_score']:.3f}")
        print(f"  Total Time: {model_results['total_time_ms'] / 1000:.1f}s")
        print(f"  Estimated Cost: ${model_results['estimated_cost']:.4f}")
    
    # Calculate category rankings
    print(f"\n{'='*60}")
    print("Calculating category rankings...")
    print(f"{'='*60}")
    
    all_categories = set()
    for model_data in results["models"].values():
        all_categories.update(model_data["category_scores"].keys())
    
    for category in sorted(all_categories):
        category_ranking = []
        for model, model_data in results["models"].items():
            if category in model_data["category_scores"]:
                category_ranking.append({
                    "model": model,
                    "score": model_data["category_scores"][category],
                })
        
        category_ranking.sort(key=lambda x: x["score"], reverse=True)
        results["categories"][category] = category_ranking
        
        print(f"\n{category}:")
        for rank, entry in enumerate(category_ranking[:3], 1):
            print(f"  {rank}. {entry['model']}: {entry['score']:.3f}")
    
    # Save results
    results_file = Path("results/hermes_optimization.json")
    results_file.parent.mkdir(exist_ok=True)
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Results saved to {results_file}")
    
    # Generate optimization recommendations
    generate_recommendations(results)

def generate_recommendations(results: dict):
    """Generate model assignment recommendations based on benchmark results."""
    print(f"\n{'='*60}")
    print("HERMES MODEL OPTIMIZATION RECOMMENDATIONS")
    print(f"{'='*60}\n")
    
    # Define Hermes roles and their primary categories
    hermes_roles = {
        "Main Model (conversations)": ["hermes-instruction", "hermes-memory"],
        "Delegation (subagents)": ["hermes-planning", "hermes-tool-use"],
        "Auxiliary: Vision": ["hermes-memory"],
        "Auxiliary: Compression": ["hermes-memory"],
        "Auxiliary: Skills": ["hermes-instruction", "hermes-tool-use"],
        "Auxiliary: Reviewer": ["hermes-code-review"],
        "Auxiliary: Triage": ["hermes-planning"],
        "Auxiliary: Titles": ["hermes-memory"],
        "Error Recovery": ["hermes-error-recovery"],
    }
    
    recommendations = {}
    
    for role, categories in hermes_roles.items():
        # Calculate weighted score for each model across relevant categories
        model_scores = {}
        for model, model_data in results["models"].items():
            total = 0.0
            count = 0
            for category in categories:
                if category in model_data["category_scores"]:
                    total += model_data["category_scores"][category]
                    count += 1
            
            if count > 0:
                # Factor in cost efficiency
                avg_score = total / count
                cost = model_data["estimated_cost"]
                cost_efficiency = avg_score / (cost + 0.001)  # avoid division by zero
                
                model_scores[model] = {
                    "score": avg_score,
                    "cost": cost,
                    "efficiency": cost_efficiency,
                }
        
        # Rank by score (primary) and cost efficiency (secondary)
        ranked = sorted(
            model_scores.items(),
            key=lambda x: (x[1]["score"], x[1]["efficiency"]),
            reverse=True
        )
        
        if ranked:
            best_model = ranked[0][0]
            best_score = ranked[0][1]["score"]
            best_cost = ranked[0][1]["cost"]
            
            recommendations[role] = {
                "model": best_model,
                "score": best_score,
                "estimated_cost_per_task": best_cost / results["total_tasks"],
                "alternatives": [r[0] for r in ranked[1:3]],
            }
            
            print(f"{role}:")
            print(f"  Recommended: {best_model}")
            print(f"  Score: {best_score:.3f}")
            print(f"  Cost per task: ${best_cost / results['total_tasks']:.6f}")
            print(f"  Alternatives: {', '.join(recommendations[role]['alternatives'])}")
            print()
    
    # Save recommendations
    rec_file = Path("results/hermes_recommendations.json")
    with open(rec_file, "w") as f:
        json.dump(recommendations, f, indent=2)
    
    print(f"✓ Recommendations saved to {rec_file}")
    
    # Calculate potential savings
    print(f"\n{'='*60}")
    print("COST OPTIMIZATION ANALYSIS")
    print(f"{'='*60}\n")
    
    # Compare current config vs optimized
    current_models = {
        "main": "qwen3.7-plus",
        "delegation": "deepseek-v4-flash",
        "auxiliary": "deepseek-v4-flash",
    }
    
    print("Current Configuration:")
    for role, model in current_models.items():
        print(f"  {role}: {model}")
    
    print("\nOptimized Configuration:")
    for role, rec in recommendations.items():
        print(f"  {role}: {rec['model']}")
    
    # Estimate monthly savings (assuming 1000 tasks per role per month)
    tasks_per_month = 1000
    current_cost = sum(
        MODEL_PRICING[model]["input"] * 500 + MODEL_PRICING[model]["output"] * 200
        for model in current_models.values()
    ) * tasks_per_month / 1_000_000
    
    optimized_cost = sum(
        rec["estimated_cost_per_task"] * tasks_per_month
        for rec in recommendations.values()
    )
    
    savings = current_cost - optimized_cost
    savings_percent = (savings / current_cost * 100) if current_cost > 0 else 0
    
    print(f"\nEstimated Monthly Costs (1000 tasks per role):")
    print(f"  Current: ${current_cost:.2f}")
    print(f"  Optimized: ${optimized_cost:.2f}")
    print(f"  Savings: ${savings:.2f} ({savings_percent:.1f}%)")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
