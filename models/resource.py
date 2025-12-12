class Resource:
    def __init__(self, resource_id, name, camp_id):
            self.resource_id = resource_id
            self.name = name
            self.camp_id = camp_id
    def to_dict(self):
         return {
              "resource_id": self.resource_id,
              "name": self.name,
              "camp_id": self.camp_id,
              "type": "Resource"


         }

class Equipment(Resource):
    def __init__(self, resource_id, name, camp_id, target_quantity: int, current_quantity: int, condition: str = "Good"):
        super().__init__(resource_id, name, camp_id)
        self.condition = condition
        self.current_quantity = current_quantity
        self.target_quantity = target_quantity

    
    @property
    def number_required(self): 
        return self.target_quantity - self.current_quantity
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            "type": "Equipment",
            "target_quantity": self.target_quantity,
            "current_quantity": self.current_quantity,
            "condition": self.condition
        })
        return data
    
    @classmethod
    def from_dict(cls, data):
         return cls(
              resource_id=data["resource_id"],
              name=data["name"],
              camp_id=data["camp_id"],
              target_quantity=data["target_quantity"],
              current_quantity=data["current_quantity"],
              condition=data.get("condition","Good")
         )
    
    