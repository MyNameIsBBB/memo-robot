import json
import os

class MedicineDataManager:
    
    def __init__(self, data_file="medicine_data.json"):
        self.data_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data",
            data_file
        )
        self.medicines = []
        self.load_medicines()
    
    def load_medicines(self):
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                self.medicines = json.load(f)
        except FileNotFoundError:
            self.medicines = []
            print(f"Warning: {self.data_path} not found. Starting with empty list.")
        except json.JSONDecodeError:
            self.medicines = []
            print(f"Warning: Invalid JSON in {self.data_path}. Starting with empty list.")
    
    def save_medicines(self):
        try:
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(self.medicines, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving medicines: {e}")
            return False
    
    def get_all_medicines(self):
        return self.medicines
    
    def get_medicine_by_id(self, medicine_id):
        for medicine in self.medicines:
            if medicine.get('id') == medicine_id:
                return medicine
        return None
    
    def get_medicine_by_name(self, name):
        for medicine in self.medicines:
            if medicine.get('name', '').lower() == name.lower():
                return medicine
        return None
    
    def get_medicines_by_time(self, time):
        return [m for m in self.medicines if m.get('taken_time') == time]
    
    def add_medicine(self, name, taken_time, dosage="", uses=None, side_effects=None):
        if not name or not taken_time:
            return False, "Name and time are required"
        
        if self.get_medicine_by_name(name):
            return False, f"Medicine '{name}' already exists"
        
        new_id = max([m.get('id', 0) for m in self.medicines], default=0) + 1
        
        new_medicine = {
            "id": new_id,
            "name": name,
            "taken_time": taken_time,
            "dosage": dosage,
            "uses": uses if uses else [],
            "side_effects": side_effects if side_effects else []
        }
        
        self.medicines.append(new_medicine)
        
        if self.save_medicines():
            return True, f"Medicine '{name}' added successfully"
        else:
            self.medicines.pop()
            return False, "Failed to save medicine data"
    
    def remove_medicine(self, medicine_id):
        medicine = self.get_medicine_by_id(medicine_id)
        if not medicine:
            return False, "Medicine not found"
        
        medicine_name = medicine.get('name', 'Unknown')
        
        self.medicines = [m for m in self.medicines if m.get('id') != medicine_id]
        
        if self.save_medicines():
            return True, f"Medicine '{medicine_name}' removed successfully"
        else:
            self.load_medicines()
            return False, "Failed to save changes"
    
    def update_medicine(self, medicine_id, **kwargs):
        medicine = self.get_medicine_by_id(medicine_id)
        if not medicine:
            return False, "Medicine not found"
        
        for key, value in kwargs.items():
            if key in medicine:
                medicine[key] = value
        
        if self.save_medicines():
            return True, "Medicine updated successfully"
        else:
            self.load_medicines()
            return False, "Failed to save changes"
    
    def get_sorted_medicines(self, sort_by='taken_time'):
        if sort_by == 'taken_time':
            return sorted(self.medicines, key=lambda x: x.get('taken_time', '00:00'))
        elif sort_by == 'name':
            return sorted(self.medicines, key=lambda x: x.get('name', '').lower())
        elif sort_by == 'id':
            return sorted(self.medicines, key=lambda x: x.get('id', 0))
        return self.medicines

_default_manager = None

def _get_manager():
    global _default_manager
    if _default_manager is None:
        _default_manager = MedicineDataManager()
    return _default_manager

def get_medicine_data():
    return _get_manager().get_all_medicines()

def get_medicine_by_name(name):
    return _get_manager().get_medicine_by_name(name)

