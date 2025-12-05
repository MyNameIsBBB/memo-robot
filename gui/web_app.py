from flask import Flask, render_template, jsonify, request
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from scripts.medicine_manager import MedicineDataManager

app = Flask(__name__)
medicine_manager = MedicineDataManager()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/medicines', methods=['GET'])
def get_medicines():
    medicines = medicine_manager.get_sorted_medicines(sort_by='taken_time')
    return jsonify({'success': True, 'medicines': medicines})

@app.route('/api/medicines', methods=['POST'])
def add_medicine():
    data = request.json
    success, message = medicine_manager.add_medicine(
        name=data.get('name'),
        taken_time=data.get('taken_time'),
        dosage=data.get('dosage', ''),
        uses=data.get('uses', []),
        side_effects=data.get('side_effects', [])
    )
    return jsonify({'success': success, 'message': message})

@app.route('/api/medicines/<int:medicine_id>', methods=['PUT'])
def update_medicine(medicine_id):
    data = request.json
    success, message = medicine_manager.update_medicine(
        medicine_id=medicine_id,
        name=data.get('name'),
        taken_time=data.get('taken_time'),
        dosage=data.get('dosage', ''),
        uses=data.get('uses', []),
        side_effects=data.get('side_effects', [])
    )
    return jsonify({'success': success, 'message': message})

@app.route('/api/medicines/<int:medicine_id>', methods=['DELETE'])
def delete_medicine(medicine_id):
    success, message = medicine_manager.remove_medicine(medicine_id)
    return jsonify({'success': success, 'message': message})

@app.route('/api/medicines/search', methods=['GET'])
def search_medicines():
    query = request.args.get('q', '').lower()
    all_medicines = medicine_manager.get_all_medicines()
    filtered = [m for m in all_medicines if query in m['name'].lower()]
    return jsonify({'success': True, 'medicines': filtered})

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
