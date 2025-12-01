class Resource:
    def __init__(self, resource_id, name, camp_id):
            self.resource_id = resource_id
            self.name = name
            self.camp_id = camp_id

class Equipment(Resource):
    def __init__(self, resource_id, name, camp_id, target_quantity: int, current_quantity: int, condition: str = "Good"):
        super.__init__(resource_id, name, camp_id)
        self.condition = condition
        self.current_quantity = current_quantity
        self.target_quantity = target_quantity

    
    @property
    def number_required(self): 
        return self.target_quantity - self.current_quantity