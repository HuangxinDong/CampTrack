import uuid

class Camper:
    def __init__(self, name: str, age: int, medical_info: str):
        self.camper_id = str(uuid.uuid4())
        self.name = name
        self.age = age
        self.medical_info = medical_info

    def to_dict(self):
        return {
            "camper_id": self.camper_id,
            "name": self.name,
            "age": self.age,
            "medical_info": self.medical_info,
        }

    @classmethod
    def from_dict(cls, data):
        camper = cls(
            name=data["name"],
            age=data["age"],
            medical_info=data["medical_info"]
        )
        camper.camper_id = data["camper_id"]
        return camper
