import difflib
import random

def calculate_similarity(text1, text2):
    return difflib.SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

def run_experiment():
    print("Running Synthetic Plagiarism Evaluation (n=60)...")
    
    # --- 1. Generate Positive Cases (Simulated Plagiarism) ---
    base_texts = [
        "The mitochondria is the powerhouse of the cell.",
        "Python is an interpreted high-level general-purpose programming language.",
        "Newton's second law states that Force equals mass times acceleration.",
        "Photosynthesis is the process used by plants to convert light energy into chemical energy.",
        "Artificial Intelligence is intelligence demonstrated by machines, as opposed to natural intelligence."
    ] * 6 
    
    positive_pairs = []
    
    for i, text in enumerate(base_texts):
        if i % 3 == 0: # Direct Copy
            positive_pairs.append((text, text))
        elif i % 3 == 1: # Minor Edits
            modified = text.replace(" is ", " ").replace(" the ", " ")
            positive_pairs.append((text, modified))
        else: # Word Shuffle (Partial)
            words = text.split()
            random.shuffle(words)
            modified = " ".join(words)
            positive_pairs.append((text, modified))

    # --- 2. Generate Negative Cases (Distinct Topics) ---
    # Using clearly distinct texts to simulate different student answers
    distinct_topics_A = [
        "The French Revolution began in 1789.",
        "Java is strictly typed.",
        "Mitochondria generate ATP.",
        "Shakespeare wrote Hamlet.",
        "The derivative of x squared is 2x."
    ] * 6
    
    distinct_topics_B = [
        "Quantum physics deals with probabilities.",
        "React uses a virtual DOM.",
        "The capital of France is Paris.",
        "E=mc^2 is the mass-energy equivalence.",
        "HTML stands for HyperText Markup Language."
    ] * 6
    
    negative_pairs = list(zip(distinct_topics_A, distinct_topics_B))

    # --- 3. Evaluate ---
    # Raising threshold slightly to be realistic
    threshold = 0.45 
    true_positives = 0
    false_positives = 0
    false_negatives = 0
    true_negatives = 0

    print(f"\nEvaluating with Threshold: {threshold}")
    
    for t1, t2 in positive_pairs:
        score = calculate_similarity(t1, t2)
        if score >= threshold:
            true_positives += 1
        else:
            false_negatives += 1
            
    for t1, t2 in negative_pairs:
        score = calculate_similarity(t1, t2)
        if score >= threshold:
            false_positives += 1
        else:
            true_negatives += 1

    # --- 4. Calculate Metrics ---
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    print("\n--- RESULTS ---")
    print(f"Precision: {precision:.3f}")
    print(f"Recall:    {recall:.3f}")
    print(f"F1-Score:  {f1:.3f}")

if __name__ == "__main__":
    run_experiment()
