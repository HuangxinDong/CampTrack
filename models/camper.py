import uuid

class Camper:
    def __init__(self, name: str, age: int, contact: str = None, medical_info: str = None):
        self.camper_id = str(uuid.uuid4())
        self.name = name
        self.age = age
        self.contact = contact
        self.medical_info = medical_info

    def to_dict(self):
        return {
            "camper_id": self.camper_id,
            "name": self.name,
            "age": self.age,
            "contact": self.contact,
            "medical_info": self.medical_info,
        }

    @classmethod
    def from_dict(cls, data):
        camper = cls(
            name=data.get("name"),
            age=data.get("age"),
            contact=data.get("contact"),
            medical_info=data.get("medical_info"),
        )
        camper.camper_id = data.get("camper_id", camper.camper_id)
        return camper
