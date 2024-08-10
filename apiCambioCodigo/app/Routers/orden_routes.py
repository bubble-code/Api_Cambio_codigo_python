from flask import Blueprint, request, jsonify
from app.OrdenFabricacion.OrdenFabricacion import OrdenFabricacion

orden_bp = Blueprint('orden', __name__)

@orden_bp.route('/ordenf', methods=['GET'])
def autocomplete2():
    search = request.args.get('search', '')
    print(search)
    if search:
        try:
            ordenF = OrdenFabricacion()
            result = ordenF.autocomplete(search)
            return jsonify(result)
        except Exception as e:
            print("Error en la consulta de autocompletado: ", e)
            return jsonify([]), 500
    return jsonify([])
