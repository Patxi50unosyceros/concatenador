#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import hashlib
import datetime
from random import randint


def mi_entero_aleatorio_entre(a: int, b: int):
    if type(a) == int and type(b) == int:
        return randint(a, b)
    return None


def mi_existe_archivo(archivo):
    if type(archivo) == str and os.path.exists(archivo) and os.path.isfile(archivo):
        return True
    return False


def mi_get_dir_actual():
    return os.getcwd()


def mi_eliminar_archivo(archivo):
    ruta = os.path.join(mi_get_dir_actual(), archivo)
    if mi_existe_archivo(ruta):
        os.remove(ruta)
        if not mi_existe_archivo(ruta):
            return True
    return False


# aux de mi_hasheador
def aux_hash(lista_de_algoritmos_solicitados, archivo, texto_codificado_utf8, archivotruetextofalse):
    # establecemos las banderas...
    md5 = True if 'md5' in lista_de_algoritmos_solicitados else False
    sha1 = True if 'sha1' in lista_de_algoritmos_solicitados else False
    sha224 = True if 'sha224' in lista_de_algoritmos_solicitados else False
    sha256 = True if 'sha256' in lista_de_algoritmos_solicitados else False
    sha384 = True if 'sha384' in lista_de_algoritmos_solicitados else False
    sha512 = True if 'sha512' in lista_de_algoritmos_solicitados else False

    # cargando los motores que tengan bandera True motores...
    motor_md5 = hashlib.md5() if md5 else None
    motor_sha1 = hashlib.sha1() if sha1 else None
    motor_sha224 = hashlib.sha224() if sha224 else None
    motor_sha256 = hashlib.sha256() if sha256 else None
    motor_sha384 = hashlib.sha384() if sha384 else None
    motor_sha512 = hashlib.sha512() if sha512 else None

    if archivotruetextofalse:  # si archivo: lo leemos bloque a bloque de 4 KILOBYTES y aplicamos los motores activados
        try:
            with open(archivo, 'rb') as fuente_de_datos:
                while True:
                    datos_leidos = fuente_de_datos.read(4096)  # buffer de 4 Kilobytes
                    if not datos_leidos:
                        break
                    motor_md5.update(datos_leidos) if md5 else None
                    motor_sha1.update(datos_leidos) if sha1 else None
                    motor_sha224.update(datos_leidos) if sha224 else None
                    motor_sha256.update(datos_leidos) if sha256 else None
                    motor_sha384.update(datos_leidos) if sha384 else None
                    motor_sha512.update(datos_leidos) if sha512 else None
        except:
            return None
    else:  # si texto...
        motor_md5.update(texto_codificado_utf8) if md5 else None
        motor_sha1.update(texto_codificado_utf8) if sha1 else None
        motor_sha224.update(texto_codificado_utf8) if sha224 else None
        motor_sha256.update(texto_codificado_utf8) if sha256 else None
        motor_sha384.update(texto_codificado_utf8) if sha384 else None
        motor_sha512.update(texto_codificado_utf8) if sha512 else None

    # recopilamos los hashes obtenidos...
    recopilacion = {'md5': str(motor_md5.hexdigest()) if md5 else '',
                    'sha1': str(motor_sha1.hexdigest()) if sha1 else '',
                    'sha224': str(motor_sha224.hexdigest()) if sha224 else '',
                    'sha256': str(motor_sha256.hexdigest()) if sha256 else '',
                    'sha384': str(motor_sha384.hexdigest()) if sha384 else '',
                    'sha512': str(motor_sha512.hexdigest()) if sha512 else ''}

    # eliminamos las entradas con hash vacío y devolvemos la recopilación
    for clave in list(recopilacion.keys()):
        if recopilacion.get(clave) == '':
            del recopilacion[clave]
    return recopilacion


# recibe un texto o un archivo, un modo de trabajo ('t' Texto o, 'a' Archivo), y un texto, lista, o tupla
# que define los algoritmos que pueden ser: md5, sha1, sha224, sha256, sha384, sha512; y devuelve un diccionario
def mi_hasheador(datos, tipo_dato='t', algoritmo='*'):
    if type(algoritmo) in [str, tuple, list] and type(tipo_dato) == str and tipo_dato in ['t', 'a']:
        algoritmos_conocidos = ["md5", "sha1", "sha224", "sha256", "sha384", "sha512"]
        algoritmos_solicitados = []
        if type(algoritmo) == str:  # recibimos algoritmo en cadena de texto
            if algoritmo == '*':  # ................................... hemos pedido TODOS
                algoritmos_solicitados += algoritmos_conocidos
            elif algoritmo.lower() in algoritmos_conocidos:  # ........ hemos pedido alguno
                algoritmos_solicitados.append(algoritmo.lower())
            else:  # .................................................. hemos pedido uno desconocido
                return None
        else:  # ........................... recibimos algoritmo en una lista o tupla
            for algoritm in algoritmo:
                if type(algoritm) == str and algoritm.lower() in algoritmos_conocidos:
                    algoritmos_solicitados.append(algoritm.lower())  # .hemos pedido 1 o varios
        if len(algoritmos_solicitados) > 0:  # ............ tras filtrar, hemos acumulado algoritmos disponibles....
            if tipo_dato == 'a' and mi_existe_archivo(datos):  # ................. se pidió un archivo
                return aux_hash(tuple(algoritmos_solicitados), datos, '', True)
            elif tipo_dato == 't' and type(datos) == str:  # .............. se pidió un texto
                return aux_hash(tuple(algoritmos_solicitados), '', datos.encode('UTF-8'), False)
            else:
                return None
        else:
            return None
    return None


# si recibe una ruta, devuelve True si verifica que es una carpeta
def mi_existe_directorio(directorio):
    if type(directorio) == str and os.path.exists(directorio):
        if os.path.isdir(directorio) and not os.path.islink(directorio):
            return True
    return False


# devuelve un diccionario de archivos o directorios o ambos (xdefecto), del directorio pedido o del actual (xdefecto)
def mi_listar_directorio(modo0todo_modo1dir_modo2arch=0, directorio='', hashear=''):
    elhash = ''
    if type(hashear) == str and hashear.lower() in ["md5", "sha1", "sha224", "sha256", "sha384", "sha512"]:
        elhash += hashear.lower()
    if type(modo0todo_modo1dir_modo2arch) == int and type(directorio) == str:
        directorio_analizado = mi_get_dir_actual() if directorio == '' else directorio
        if mi_existe_directorio(directorio_analizado):
            lista_de_archivos = []
            lista_de_subdirectorios = []
            modo = modo0todo_modo1dir_modo2arch
            for elemento in os.listdir(directorio_analizado):
                ruta_elemento = os.path.join(directorio_analizado, elemento)
                if modo < 2 and mi_existe_directorio(ruta_elemento):
                    pack_datos = {'n': elemento}
                    lista_de_subdirectorios.append(pack_datos)
                if modo != 1 and mi_existe_archivo(ruta_elemento):
                    # fecha ultima modificacion = flotante os.stat(ruta_elemento).st_mtime
                    # fecha ultima modificacion = flotante os.path.getmtime(ruta_elemento)
                    obj_ltm = datetime.datetime.fromtimestamp(os.stat(ruta_elemento).st_mtime)
                    timelastmod = str(obj_ltm.year) + '/' + str(obj_ltm.month).rjust(2, '0') + '/'
                    timelastmod += str(obj_ltm.day).rjust(2, '0') + ' ' + str(obj_ltm.hour).rjust(2, '0') + ':'
                    timelastmod += str(obj_ltm.minute).rjust(2, '0') + ':' + str(obj_ltm.second).rjust(2, '0')
                    pack_datos = {'n': elemento, 'tambytes': os.path.getsize(ruta_elemento),
                                  'timelastmod': timelastmod}
                    if elhash != '':
                        pack_de_hashes = mi_hasheador(ruta_elemento, tipo_dato='a', algoritmo=elhash)
                        pack_datos['zhash'] = pack_de_hashes.get(elhash)
                    lista_de_archivos.append(pack_datos)
            return {"sd": lista_de_subdirectorios, "ar": lista_de_archivos, "rt": directorio_analizado}
    return None


def crear_nombre_archivo_temporal(extension: str):
    """Crea un nombre de archivo nuevo de una extensión concreta

    Notas:
        ENTRADA: str de la extensión final

        TRABAJO: crea nuevo nombre de archivo

        SALIDA: string con nombre del archivo inventado
    """
    lista_archivos_en_directorio = mi_listar_directorio(0)
    nuevo = mi_hasheador(str(mi_entero_aleatorio_entre(0, 9999)), 't', 'md5').get('md5')[0:8] + '.' + extension
    while nuevo in lista_archivos_en_directorio:
        nuevo = mi_hasheador(str(mi_entero_aleatorio_entre(0, 9999)), 't', 'md5').get('md5')[0:8] + '.' + extension
    return nuevo


class FalloConsultandoPaginasArchivoConPyMuPDF(Exception):
    pass


class FalloEnConvertirPaginasPdfAImagenes(Exception):
    pass


class FalloUniendoMinipdfsEnMiniPdf(Exception):
    pass


class FalloEnConvertirImagenesAPdf(Exception):
    pass


class FalloAlExtraerPaginasPdfAMiniPdf(Exception):
    pass


class FalloCapturandoPaginasDePdfAMiniPdf(Exception):
    pass


class PeticionDeTrabajoNoValida(Exception):
    pass


class ArchivoPdfVacioONoexiste(Exception):
    pass


class FalloValidandoYProcesandoSolicitud(Exception):
    pass
