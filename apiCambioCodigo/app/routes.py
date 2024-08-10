from flask import Blueprint, request, jsonify
from app.OrdenFabricacion.OrdenFabricacion import OrdenFabricacion
from app.Articulo.Articulo import Articulo

main_bp = Blueprint('main', __name__)

@main_bp.route('/autocomplete', methods=['GET'])
def autocomplete():
    search = request.args.get('search', '')
    if search:
        try:
            articulo = Articulo()
            result = articulo.autocomplete(search)
            return jsonify(result)
        except Exception as e:
            print("Error en la consulta de autocompletado: ", e)
            return jsonify([]), 500
    return jsonify([])

@main_bp.route('/recoding_articulo', methods=['POST'])
def update_articulo():
    data = request.json
    old_id_articulo = data.get('old_id_articulo')
    new_id_articulo = data.get('new_id_articulo')
    print(old_id_articulo)
    print(new_id_articulo)

    if not old_id_articulo or not new_id_articulo:
        return jsonify({"error": "old_id_articulo and new_id_articulo are required"}), 400

    articulo = Articulo()
    
    try:
        articulo.disable_all_foreign_keys()
        articulo.update_id_articulo(old_id_articulo, new_id_articulo)
        articulo.enable_all_foreign_keys()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route('/autocomplete2', methods=['GET'])
def autocomplete2():
    search = request.args.get('search', '')
    if search:
        try:
            articulo = Articulo()
            result = articulo.autocomplete2(search)
            return jsonify(result)
        except Exception as e:
            print("Error en la consulta de autocompletado: ", e)
            return jsonify([]), 500
    return jsonify([])

@main_bp.route('/articulos', methods=['GET'])
def obtener_articulos():
    listaIDs = request.args.get('listaID', '')
    print(listaIDs.split(','))
    try:
        articulo = Articulo()
        result = articulo.getArticulos(listaIDs.split(','))
        return jsonify(result)
    except Exception as e:
        print("Error obteniendo artículos: ", e)
        return jsonify([]), 500

@main_bp.route('/generarOF', methods=['POST'])
def generarOF():
    data = request.json
    listaIDs = data.get('listaID')
    articulo = Articulo()
    articulo.generate_of(listaIDs)
    return jsonify({"status": "success"}), 200
    # print(new_id_articulo)

    # if not old_id_articulo or not new_id_articulo:
    #     return jsonify({"error": "old_id_articulo and new_id_articulo are required"}), 400

    # articulo = Articulo()
    
    # try:
    #     articulo.disable_all_foreign_keys()
    #     articulo.update_id_articulo(old_id_articulo, new_id_articulo)
    #     articulo.enable_all_foreign_keys()
    #     return jsonify({"status": "success"}), 200
    # except Exception as e:
    #     return jsonify({"error": str(e)}), 500

# @main_bp.route('/execute_sql', methods=['POST'])
# def execute_sql():
#     data = request.json
#     script_id = data.get('script_id')
#     params = data.get('params', {})

#     if not script_id:
#         return jsonify({"error": "script_id is required"}), 400

#     sql_service = SQLService()
    
#     try:
#         result = sql_service.execute_script(script_id, params)
#         return jsonify({"status": "success", "result": result}), 200
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500
