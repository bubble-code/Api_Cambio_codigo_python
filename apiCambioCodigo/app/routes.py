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

@main_bp.route('/generarOF', methods=['GET'])
def generarOF():
    try:
        # data = request.json
        # lista_ids = data.get('listaID')
        # print("Lista desde el front: ", lista_ids)
        articulo_service = Articulo()
        # resultado = articulo_service.generate_of(lista_ids)
        resultado = articulo_service.generate_of()
        if resultado.get("status") == "error":
            return jsonify(resultado), 400  # HTTP 400 para errores de procesamiento específicos

        return jsonify(resultado),200
    
    except Exception as e:
        print(f"Error en endpoint generarOF: {e}")
        return jsonify({"status": "error", "message": "Internal Server Error"}), 500
    # print(new_id_articulo)

@main_bp.route("/getOrdenes", methods=["GET"])
def getOrdenes():
    try:
        articulo = Articulo()
        result = articulo.getOrdenes()
        return jsonify(result),200
    except Exception as e:
        print("Error al obtener las ordenes: " + str(e))
        return jsonify({"estatus": "error", "message":"Error al obtener las ordenes"}),500

@main_bp.route("/getSeccion", methods=["GET"])
def getSeccion():
    try:
        articulo = Articulo()
        resultado = articulo.getSeccion()
        return jsonify(resultado)
    except Exception as e:
        print("Error al obtener las ordenes: " + str(e))
        return jsonify({"estatus": "error", "message":"Error al obtener las ordenes"}),500
    
@main_bp.route("/getCapacidadTD", methods=["POST"])
def getCapacidadTD():
    try:
        data = request.json
        start_date = data.get('startDate')
        end_date = data.get('endDate')
        articulo = Articulo()
        resultado = articulo.procesarCapacidadTeorica(start_date,end_date)
        return jsonify(resultado)
    except Exception as e:
        print("Error al procesar ordenes: " + str(e))
        return jsonify({"estatus": "error", "message":"Error al obtener las ordenes"}),500
    
@main_bp.route("/getOFFromCentro", methods=["POST"])
def getOFFromCentro():
    try:
        data = request.json
        centro = data.get("centro")
        articulo= Articulo()
        resultado = articulo.getOFFromCentro(centro)
        return jsonify(resultado)
    except Exception as e:
        print("Error al obtener las ordenes: " + str(e))
        return jsonify({"estatus": "error", "message":"Error al obtener las ordenes"}),500