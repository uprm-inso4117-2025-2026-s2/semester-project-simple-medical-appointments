from flask import Blueprint, request, jsonify
from datetime import datetime
from ..services.closure_service import (
    create_closure,
    list_closures,
    get_closure,
    delete_closure,
    is_blocked,
)

closures_bp = Blueprint("closures", __name__)


@closures_bp.route("/", methods=["POST"])
def create():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON."}), 400

    try:
        closure = create_closure(data)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify(closure.to_dict()), 201

@closures_bp.route("/", methods=["GET"])
def list_all():
    closure_type = request.args.get("type")
    doctor_id_raw = request.args.get("doctor_id")

    doctor_id = None
    if doctor_id_raw is not None:
        try:
            doctor_id = int(doctor_id_raw)
        except ValueError:
            return jsonify({"error": "'doctor_id' must be a number."}), 400

    closures = list_closures(closure_type=closure_type, doctor_id=doctor_id)
    return jsonify([c.to_dict() for c in closures]), 200


@closures_bp.route("/<int:closure_id>", methods=["GET"])
def retrieve(closure_id):
    closure = get_closure(closure_id)
    if closure is None:
        return jsonify({"error": "Closure not found."}), 404
    return jsonify(closure.to_dict()), 200


@closures_bp.route("/<int:closure_id>", methods=["DELETE"])
def remove(closure_id):
    deleted = delete_closure(closure_id)
    if not deleted:
        return jsonify({"error": "Closure not found."}), 404
    return jsonify({"message": "Closure deleted."}), 200


@closures_bp.route("/check", methods=["POST"])
def check():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON."}), 400

    try:
        start_dt  = datetime.fromisoformat(data["start_datetime"])
        end_dt    = datetime.fromisoformat(data["end_datetime"])
        doctor_id = int(data["doctor_id"])
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "Required fields: 'start_datetime', 'end_datetime', 'doctor_id'."}), 400

    blocked, reason = is_blocked(start_dt, end_dt, doctor_id)

    response = {"blocked": blocked}
    if reason:
        response["reason"] = reason
    return jsonify(response), 200