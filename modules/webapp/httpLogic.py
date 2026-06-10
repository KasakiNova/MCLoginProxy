# coding=utf-8
"""Flask routes for the MCLoginProxy Yggdrasil server.

Endpoints:
- ``/`` — index (status) page
- ``/minecraftservices/publickeys`` — cached public keys
- ``/sessionserver/session/minecraft/hasJoined`` — player profile proxy
"""
import json
import os.path

from flask import Flask, jsonify, request, Response

import modules.globalVariables as gVar
from modules.services.hasJoinedService import HasJoinedService

app = Flask(__name__)


@app.route(rule='/', methods=['GET'])
def index():
    """Return the static ``index.json``."""
    index_path = os.path.join(gVar.webDir, 'index.json')
    with open(index_path, 'r') as f:
        return jsonify(json.load(f))


@app.route(rule='/minecraftservices/publickeys', methods=['GET'])
def publickeys():
    """Return the cached Minecraft publickeys."""
    return jsonify(gVar.publickey)


@app.route(rule='/sessionserver/session/minecraft/hasJoined',
           methods=['GET'])
def has_joined():
    """Proxy the ``hasJoined`` request to configured auth servers."""
    server_id = request.args.get("serverId")
    username = request.args.get("username")
    has_joined_service = HasJoinedService()
    profile = has_joined_service.get_profile(
        username=username, server_id=server_id
    )
    return Response(status=204) if profile is None else (jsonify(profile), 200)
