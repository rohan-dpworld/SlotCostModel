#Contains all the classes
class Config:
    def __init__(self, capacity=2500, forty_feet_percentage=75, frequency=7, eca_distance=827, teu_percent=75, slot_revenue=4348):
        self.Capacity= capacity
        self.FortyFeetPercentage= forty_feet_percentage*0.01
        self.Frequency= frequency
        self.ManeuverTime= 6.0
        self.WaitTime= 2.0
        self.BerthTime= 12.0
        self.ECADistance= eca_distance
        self.Speeds= [14, 16, 18, 21]
        self.CharterHires = [0, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 20000, 30000, 40000, 45000, 50000, 60000, 70000, 80000, 100000]
        self.TEUPercent = teu_percent * 0.01
        self.SlotRevenue= slot_revenue


class DO:

    def __init__(self, bunker_price=697):
        self.Speed = 10
        self.BunkerPrice= bunker_price
        self.BerthConsumptionPerDay = 4.0

class FO:

    def __init__(self, bunker_price=565):
        self.Speed = 21
        self.BunkerPrice= bunker_price
        self.ManeuverConsumptionPerDay= 8.0

class Costs:

    def __init__(self):
        self.Agency = 25000
        self.Miscellaneous = 107680



def get_initialized_variables(obj):
    """Retrieve all initialized variables and their values from the given object."""
    # Filter out methods and special attributes
    return {attr: getattr(obj, attr) for attr in dir(obj)
            if not callable(getattr(obj, attr)) and not attr.startswith("__")}