import flask
from flask import request, jsonify
from utils import create_qr
import os
from Interface import showfile

blueprint = flask.Blueprint(
    'users_api',
    __name__
)


def edit_file(show, text=''):
    file = open(showfile, mode='w')
    file.write(str(show) + '\n' + f'{text}')
    file.close()


@blueprint.route('/', methods=['POST'])
def generate_qr():
    from Interface import main
    if 'ShowMessage' in request.json:
        if request.json['ShowMessage']:
            if 'picture.png' in os.listdir():
                os.remove('picture.png')
            if 'QR' in request.json:
                if request.json['QR'].strip() != '':
                    create_qr(request.json['QR'])
                else:
                    try:
                        if request.json['TextMessage'].strip() == '':
                            edit_file(False)
                            return jsonify({'error': 'send info'})
                    except KeyError:
                        edit_file(False)
                        return jsonify({'error': 'send info'})
                if 'TextMessage' in request.json:
                    if request.json['TextMessage'].strip() != '':
                        edit_file(True, request.json['TextMessage'])
                    else:
                        edit_file(True)
                else:
                    edit_file(True)
                return jsonify({'success': 'Showing QR'})
            else:
                if 'TextMessage' in request.json:
                    if request.json['TextMessage'] != '':
                        edit_file(True, request.json['TextMessage'])
                        return jsonify({'success': 'Showing message'})
                    edit_file(False)
                    return jsonify({'error': 'send info'})
                edit_file(False)
                return jsonify({'error': 'send info'})
        else:
            edit_file(False)
        return jsonify({'success': 'turning to wait mode'})
    return jsonify({'mistake': 'try to put some right info into request'})
