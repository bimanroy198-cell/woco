from datetime import datetime

class WorkerModel:

    @staticmethod
    def create_worker(data):

        worker = {

            "phone_number":
                data["phone_number"],

            "role":
                data["role"],

            "name":
                data["name"],

            "profile_photo_url":
                data["profile_photo_url"],

            "categories":
                data["categories"],

            "profile_completed":
                True,

            "created_at":
                datetime.utcnow(),

            "updated_at":
                datetime.utcnow()
        }

        return worker