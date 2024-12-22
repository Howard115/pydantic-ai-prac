import json
import random

def get_random_job():
    with open('jobs.json', 'r', encoding='utf-8') as file:
        jobs_data = json.load(file)
    
    category = random.choice(list(jobs_data.keys()))
    subcategory = random.choice(list(jobs_data[category].keys()))
    job_title = random.choice(jobs_data[category][subcategory])
    
    return {
        "category": category,
        "subcategory": subcategory,
        "job_title": job_title
    }

# Example usage
if __name__ == "__main__":
    random_job = get_random_job()
    print(random_job)
