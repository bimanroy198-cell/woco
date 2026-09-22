import random
from datetime import datetime, timedelta
import uuid
from database import workers_collection, contractors_collection, jobs_collection, applications_collection

def seed_database():
    print("Clearing old dummy data...")
    # Clear only existing dummy data based on a flag if needed, or clear all for testing.
    # To be safe, we will just delete everything and seed fresh since this is early development.
    # If the user wants to keep real data, we could filter by "is_dummy". Let's use "is_dummy": True.
    workers_collection.delete_many({"is_dummy": True})
    contractors_collection.delete_many({"is_dummy": True})
    jobs_collection.delete_many({"is_dummy": True})
    applications_collection.delete_many({"is_dummy": True})

    # Names for dummy generation
    first_names = ["Amit", "Rahul", "Vikram", "Sunil", "Rajesh", "Pooja", "Neha", "Anita", "Suresh", "Ramesh", "Deepak", "Manish", "Kavita", "Sanjay", "Vijay"]
    last_names = ["Sharma", "Verma", "Kumar", "Singh", "Gupta", "Patel", "Das", "Yadav", "Chauhan", "Bhat"]
    locations = ["Delhi", "Mumbai", "Bangalore", "Pune", "Noida", "Gurgaon", "Chennai", "Kolkata", "Hyderabad", "Ahmedabad"]
    categories_list = ["Electrician", "Plumber", "Carpenter", "Painter", "Mason", "Welder", "Labour", "Helper", "Tile Fixer", "AC Mechanic"]

    def generate_phone():
        return "9" + "".join([str(random.randint(0, 9)) for _ in range(9)])

    now = datetime.utcnow()

    # Generate 10 Contractors
    print("Generating 10 Contractors...")
    contractors = []
    for i in range(10):
        phone = generate_phone()
        contractor = {
            "phone_number": phone,
            "role": "contractor",
            "name": f"{random.choice(first_names)} {random.choice(last_names)}",
            "categories": random.sample(categories_list, k=random.randint(1, 3)),
            "location": random.choice(locations),
            "about": "I am a professional contractor with many years of experience handling large scale construction and renovation projects.",
            "experience": f"{random.randint(5, 20)} Years",
            "profile_completed": True,
            "is_blocked": False,
            "is_deleted": False,
            "profile_photo_url": None, # Will show placeholder in app
            "created_at": (now - timedelta(days=random.randint(1, 30))).isoformat(),
            "last_login": now.isoformat(),
            "updated_at": now.isoformat(),
            "is_dummy": True
        }
        contractors.append(contractor)
    contractors_collection.insert_many(contractors)

    # Generate 20 Workers
    print("Generating 20 Workers...")
    workers = []
    for i in range(20):
        phone = generate_phone()
        worker = {
            "phone_number": phone,
            "role": "worker",
            "name": f"{random.choice(first_names)} {random.choice(last_names)}",
            "categories": random.sample(categories_list, k=random.randint(1, 4)),
            "location": random.choice(locations),
            "about": "Hardworking and skilled worker looking for daily wage or contract based jobs.",
            "experience": f"{random.randint(1, 15)} Years",
            "profile_completed": True,
            "is_blocked": False,
            "is_deleted": False,
            "profile_photo_url": None,
            "created_at": (now - timedelta(days=random.randint(1, 30))).isoformat(),
            "last_login": now.isoformat(),
            "updated_at": now.isoformat(),
            "is_dummy": True
        }
        workers.append(worker)
    workers_collection.insert_many(workers)

    # Generate 10 Jobs from the dummy contractors
    print("Generating 10 Jobs...")
    jobs = []
    job_titles = ["Need Plumbers for new building", "Electrician required urgently", "Painter for 3BHK flat", "Mason for wall construction", "Looking for AC Mechanic", "Helpers for construction site", "Tile fixer needed", "Carpenter for modular kitchen"]
    
    for i in range(10):
        contractor = random.choice(contractors)
        job_id = str(uuid.uuid4())
        job = {
            "job_id": job_id,
            "contractor_phone": contractor["phone_number"],
            "title": random.choice(job_titles),
            "description": "We need experienced people for this job. Immediate joining required. Good pay will be provided.",
            "budget": f"₹{random.randint(500, 2000)} per day",
            "location": random.choice(locations),
            "categories": random.sample(categories_list, k=random.randint(1, 2)),
            "status": "active", # active, closed, hired, cancelled
            "created_at": (now - timedelta(hours=random.randint(1, 72))).isoformat(),
            "updated_at": now.isoformat(),
            "is_dummy": True
        }
        jobs.append(job)
    jobs_collection.insert_many(jobs)

    print("Dummy data seeded successfully!")
    print(f"Contractors: {contractors_collection.count_documents({'is_dummy': True})}")
    print(f"Workers: {workers_collection.count_documents({'is_dummy': True})}")
    print(f"Jobs: {jobs_collection.count_documents({'is_dummy': True})}")

if __name__ == "__main__":
    seed_database()
