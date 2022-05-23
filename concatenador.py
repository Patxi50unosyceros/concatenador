#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Para que esta aplicación funcione, se requiere:            toWiNexe: pyinstaller concatenador.py --onefile
- tener PYTHON instalado
- tener los archivos concatenador.py y moduloaux.py
- y además:
  + pip install FPDF
  + pip install PyMuPDF
  + pip install pdf2image
  + y para que pdf2image funcione en Windows requiere que tengamos POPPLER:
        esta particularidad es la que nos permitirá capturar páginas PDF como PNG en Windows
        1º descargamos:
            o: https://blog.alivate.com.au/poppler-windows/ -> Latest binary : poppler-0.68.0_x86.7z
            o: https://github.com/oschwartz10612/poppler-windows/releases/ -> Release-22.04.0-0.zip
        2º abrimos el archivo comprimido, y en él localizaremos una carpeta llamada BIN
            que contiene DLLs y EXEs como por ejemplo pdftoppm.exe
        3º en el mismo directorio donde tengamos los archivos concatenador.py y moduloaux.py tendremos
            que poner una copia de esta carpeta BIN renombrada a 'mirender' para que funcione pdf2image

Esta herramienta se creó para agilizar una tarea del trabajo del autor. Esta primera versión tiene
212 líneas en moduloaux.py y 574 líneas en concatenador.py ; espero que sea de utilidad
"""

import sys
from moduloaux import *  # contiene las funciones auxiliares y las excepciones
from pdf2image.exceptions import PDFPopplerTimeoutError  # agregar tras hacer un pip install PDF2IMAGE
from pdf2image import convert_from_path  # agregar tras hacer un pip install PDF2IMAGE
from fpdf import FPDF  # agregar tras hacer un pip install FPDF
from fitz import fitz  # agregar tras hacer un pip install PyMuPDF

CALIDAD_DPI = 200  # define la calidad de puntos por pulgada de resolución de las páginas renderizadas
ruta_local = os.path.dirname(os.path.abspath(sys.argv[0]))  # recupera la ruta de ejecución
RUTA_POPPLER = os.path.join(ruta_local, 'mirender')  # calcula [ruta de ejecución]\mirender


def consultar_paginas_pdf(archivo):
    """Consulta la cantidad de páginas que contiene un archivo PDF, devolviendo un ERROR si hubo problemas"""
    try:
        lector_pdf = fitz.Document(archivo)
        paginas_en_pdf = int(str(lector_pdf.page_count))
        del lector_pdf
        return paginas_en_pdf
    except:
        print(f'ERROR tratando de consultar páginas en {archivo} [PyMuPDF]')
        raise FalloConsultandoPaginasArchivoConPyMuPDF


class Pack:
    """
    La clase Pack recibe sus variables de entrada y empaqueta trabajos; únicamente se llama al constructor
    de Pack desde el método 'construir_lista_de_trabajos'; los datos le llegan con los datos ya validados
    """

    def __init__(self, el_archivo: str, prim_pagina: int, ult_pagina: int, segundos: int, firmado: bool):
        self.archivo = el_archivo
        self.ini = prim_pagina  # ....................................... primera pagina
        self.fin = ult_pagina  # ........................................ ultima pagina
        self.tiempo = segundos  # ....................................... segundos maximos antes de matar el proceso
        self.confirma = True if firmado else False  # ................... True si hay firma digital => captura


class Core:
    """
    La clase Core contiene los métodos estáticos fundamentales de la aplicación
    """

    @staticmethod
    def convertir_paginas_de_pdf_a_imagenes(pack: Pack):
        """Convierte un rango de páginas firmadas de PDF como PNG con POPPLER
        y devuelve la lista de archivos PNGs; los datos le llegan validados
        o devuelve lista de PNGs o devuelve un ERROR

        Notas:
            ENTRADA: Pack(archivo, p_ini, p_fin, [firmadas], tiempo, firmado)

            TRABAJO: crea un archivo PDF con nombre nuevo

            SALIDA: string con nombre del PDF creado
        """
        if mi_existe_archivo(pack.archivo):
            lista_paginas_png = []
            try:
                pack_de_paginas = convert_from_path(pack.archivo, CALIDAD_DPI, poppler_path=RUTA_POPPLER,
                                                    first_page=pack.ini, last_page=pack.fin, timeout=pack.tiempo)
                for i, imagen in enumerate(pack_de_paginas):
                    nombre_imagen_pagina = crear_nombre_archivo_temporal('png')
                    imagen.save(nombre_imagen_pagina, 'PNG')
                    lista_paginas_png.append([i + pack.ini, nombre_imagen_pagina])
                    print(f'    - capturando página {i + pack.ini} de {pack.archivo} como {nombre_imagen_pagina}')
                    if pack.ini == pack.fin:
                        break
                return lista_paginas_png
            except PDFPopplerTimeoutError:
                print(f'ERROR tipo <PDFPopplerTimeoutError> con {pack.archivo} en [pdf2image]')
                raise FalloEnConvertirPaginasPdfAImagenes
            except:
                print(f'ERROR desconocido con {pack.archivo} en [convertir_paginas_de_pdf_a_imagenes] [pdf2image]')
                raise FalloEnConvertirPaginasPdfAImagenes
        else:
            print(f'ERROR archivo {pack.archivo} no existe, en [convertir_paginas_de_pdf_a_imagenes]')
            raise FalloEnConvertirPaginasPdfAImagenes

    @staticmethod
    def convertir_varias_imagenes_a_un_pdf(imagenes: list):
        """Incrusta una colección de imagen en un nuevo PDF
        o devuelve archivo PDF resultante, o devuelve ERROR.

        Notas:
            ENTRADA: lista de imágenes

            TRABAJO: crea un archivo PDF con nombre nuevo

            SALIDA: string con nombre del PDF creado
        """
        archivo_actual = ''
        existen_todas_las_imagenes = True
        for imagen in imagenes:
            if not mi_existe_archivo(imagen):
                existen_todas_las_imagenes = False
                archivo_actual = str(imagen)
        if existen_todas_las_imagenes:
            try:
                nuevo_documento = FPDF(orientation='P', unit='mm', format='A4')
                for imagen in imagenes:
                    archivo_actual = str(imagen)
                    nuevo_documento.add_page()
                    nuevo_documento.image(imagen, x=10, y=14, w=190, h=269)
                nombre_archivo_pdf = f'{crear_nombre_archivo_temporal("pdf")}'
                nuevo_documento.output(nombre_archivo_pdf)
                for imagen in imagenes:
                    mi_eliminar_archivo(imagen)
                return nombre_archivo_pdf
            except:
                print(f'ERROR desconocido con {archivo_actual} en [convertir_varias_imagenes_a_un_pdf] [fpdf]')
                raise FalloEnConvertirImagenesAPdf
        else:
            print(f'ERROR archivo {archivo_actual} no existe [convertir_varias_imagenes_a_un_pdf]')
            raise FalloEnConvertirImagenesAPdf

    @staticmethod
    def extraer_rango_de_paginas_de_pdf_a_mini_pdf(pack: Pack):
        """Copia rango de páginas de un PDF sin firmar a un nuevo PDF; los datos le llegan validados;
        o devuelve archivo PDF resultante, o devuelve ERROR.

        Notas:
            ENTRADA: Pack(archivo, p_ini, p_fin, [firmadas], tiempo, firmado)

            TRABAJO: crea un archivo PDF con nombre nuevo

            SALIDA: string con nombre del PDF creado
        """
        try:
            lector_pdf = fitz.Document(pack.archivo)
            primera_pagina = pack.ini
            ultima_pagina = pack.fin
            nuevo_pdf = fitz.Document()
            nuevo_pdf.insert_pdf(lector_pdf, from_page=primera_pagina - 1, to_page=ultima_pagina - 1)
            nombre_archivo_pdf = f'{crear_nombre_archivo_temporal("pdf")}'
            nuevo_pdf.save(nombre_archivo_pdf, garbage=4, clean=True, deflate=True)
            print(f'    - copiando de página {pack.ini} a {pack.fin} de {pack.archivo} como {nombre_archivo_pdf}')
            return nombre_archivo_pdf
        except:
            print(f'ERROR desconocido con {pack.archivo} en [extraer_rango_de_paginas_de_pdf_a_mini_pdf] [PyMuPDF]')
            raise FalloAlExtraerPaginasPdfAMiniPdf

    @staticmethod
    def unir_mini_pdfs_en_mini_pdf(lista_archivos_pdf_separados: list, eliminar=True):
        """Concatena una colección de PDFs NO firmados
        o devuelve archivo PDF resultante, o devuelve ERROR.

        Notas:
            ENTRADA: lista de archivos a concatenar, bool de eliminación

            TRABAJO: crea un archivo PDF con nombre nuevo

            SALIDA: string con nombre del PDF creado
        """
        print(f'    > concatenando los anteriores PDFs:')
        lista_unificada = []
        for n in lista_archivos_pdf_separados:
            if type(n) == list:
                lista_unificada += n
            else:  # n = str
                lista_unificada.append(n)
        try:
            nuevo_pdf = fitz.Document()  # creamos archivo nuevo
            docus_fitz = []
            for archivo in lista_unificada:
                docu_fitz = fitz.Document(archivo)  # creamos un apuntador al mini archivo pdf actual
                nuevo_pdf.insert_pdf(docu_fitz)  # insertamos contenido de mini pdf actual en pdf creado nuevo
                docus_fitz.append(docu_fitz)  # agregamos nombre de mini pdf actual
                print(f'    - {archivo} concatenado...')
            nombre_archivo_pdf = f'{crear_nombre_archivo_temporal("pdf")}'  # creamos nombre de nuevo pdf en disco
            nuevo_pdf.save(nombre_archivo_pdf, garbage=4, clean=True, deflate=True)  # guardamos nuevo pdf en disco
            print(f'    > > guardada la concatenación en {nombre_archivo_pdf}')

            if eliminar:  # aquí se entra si hay que eliminar los trozos concatenados
                try:
                    while len(docus_fitz) > 0:
                        docu_fitz = docus_fitz.pop()
                        del docu_fitz  # eliminamos apuntadores creados en FOR anterior ligados a los archivos mini pdf
                    for archivo_pdf_parcial in lista_unificada:
                        mi_eliminar_archivo(archivo_pdf_parcial)  # eliminamos ahora los archivos mini pdf desvinculados
                    print('      > eliminados todos los pdfs concatenados')
                except:
                    print(f'ERROR desconocido tratando de eliminar los pdf concatenados [unir_mini_pdfs_en_mini_pdf]')
                    raise FalloUniendoMinipdfsEnMiniPdf
            return nombre_archivo_pdf
        except:
            print(f'ERROR desconocido al recibir lista de archivos [unir_mini_pdfs_en_mini_pdf] [PyMuPDF]')
            raise FalloUniendoMinipdfsEnMiniPdf

    @staticmethod
    def capturar_paginas_de_pdf_a_minipdf(pack: Pack):
        """
        Captura varias páginas de un PDF como imagen PNG, para devolver un PDF;
        únicamente llama a esta función: 'trocear_archivo';
        o devuelve archivo PDF resultante, o devuelve ERROR.

        Notas:
            ENTRADA: Pack(archivo, p_ini, p_fin, [firmadas], tiempo, firmado)

            TRABAJO: convertir_paginas_de_pdf_a_imagenes + convertir_varias_imagenes_a_un_pdf

            SALIDA: nombre del archivo PDF
        """
        try:
            lista_paginas_png = Core.convertir_paginas_de_pdf_a_imagenes(pack)  # recibe [ [ numpag, 'nombr arch.png']
            nombre_archivo_pdf = Core.convertir_varias_imagenes_a_un_pdf([pagina[1] for pagina in lista_paginas_png])
            print(f'    + creado trocito: {nombre_archivo_pdf}  (y eliminadas las capturas anteriores)')
            return nombre_archivo_pdf

        except FalloEnConvertirPaginasPdfAImagenes:
            print(f'ERROR con {pack.archivo} en [capturar_paginas_de_pdf_a_minipdf]')
            raise FalloCapturandoPaginasDePdfAMiniPdf

        except FalloEnConvertirImagenesAPdf:
            print(f'ERROR con {pack.archivo} en [capturar_paginas_de_pdf_a_minipdf]')
            raise FalloCapturandoPaginasDePdfAMiniPdf

    @staticmethod
    def construir_lista_de_trabajos(i, f, lf, archivo, t):
        """
        Construye la lista de Packs necesaria para copiar un PDF,
        únicamente llama a esta función: 'validar_y_procesar_peticion';
        recibe datos validados y devuelve lista de Packs.

        Notas:
            ENTRADA: pagina inicial, pagina final, lista de páginas firmadas, nombre de archivo, tiempo límite

            TRABAJO: construye una lista de PACKS en base a la información de entrada

            SALIDA: lista de PACKS
        """
        paginas = list(range(i, f + 1))
        bloques_de_trabajo = []
        bloque_actual = Pack(archivo, i, i, t, True) if i in lf else Pack(archivo, i, i, t, False)
        paginas.pop(0)
        for pagina in paginas:
            if pagina in lf:  # ........................................... la pagina apuntada es firmada
                if bloque_actual.confirma:  # ................................. bloque actual es firmado
                    bloque_actual.fin = pagina  # ................................. editamos ultima página del bloque
                else:  # ...................................................... bloque actual es no firmado
                    bloques_de_trabajo.append(bloque_actual)  # ................... incorporamos bloque a hechos
                    bloque_actual = Pack(archivo, pagina, pagina, t, True)  # ..... creamos nuevo ultimo bloque
            else:  # ...................................................... la pagina apuntada es no firmada
                if bloque_actual.confirma:  # ................................. bloque actual es firmado
                    bloques_de_trabajo.append(bloque_actual)  # ................... incorporamos bloque a hechos
                    bloque_actual = Pack(archivo, pagina, pagina, t, False)  # .... creamos nuevo ultimo bloque
                else:  # ...................................................... bloque actual es no firmado
                    bloque_actual.fin = pagina  # ................................. editamos ultima página del bloque
        bloques_de_trabajo.append(bloque_actual)  # ....................... agregamos ultimo bloque leido
        return bloques_de_trabajo

    @staticmethod
    def segs_limit_archv(archivo):
        # bytes_de_archivo = os.path.getsize(archivo)
        return 15  # todo CALCULAR TIEMPO POR ARCHIVO

    @staticmethod
    def validar_y_procesar_solicitud(inicio, fin, lista_p_firmadas, archivo):
        """
        Valida que una petición sea correcta y consistente; en caso negativo
        devuelve un ERROR, pero en caso positivo devuelve una LISTA DE PACKS.

        Notas:
            ENTRADA: pagina inicial, pagina final, lista de páginas firmadas, nombre de archivo

            TRABAJO: construye una lista de PACKS en base a la información de entrada

            SALIDA: lista de PACKS
        """
        str_firmadas = ''
        if len(lista_p_firmadas) > 0:
            str_firmadas += '.'.join([str(num) for num in lista_p_firmadas])
        try:
            i = int(inicio)
            f = int(fin)
            lf = [] + lista_p_firmadas
            t = consultar_paginas_pdf(archivo)
            peticion = f'ERROR: se ha pedido <{archivo}> [{inicio}-{fin}]/{t} *F:{str_firmadas}'
            bytes_de_archivo = os.path.getsize(archivo)
            if bytes_de_archivo is not None:
                if f < i:
                    print(f'{peticion}\n\t  ...y: pagina final < pagina inicio')
                    raise PeticionDeTrabajoNoValida
                else:
                    if f > t:
                        print(f'{peticion}\n\t  ...y: pagina final > paginas totales')
                        raise PeticionDeTrabajoNoValida
                    else:
                        if len(lf) > 0 and (max(lf) > f or min(lf) < i):
                            print(f'{peticion}\n\t  ...y: pagina firmada fuera del rango')
                            raise PeticionDeTrabajoNoValida
                        return Core.construir_lista_de_trabajos(i, f, lf, archivo, Core.segs_limit_archv(archivo))
            else:
                print(f'{peticion}\n\t  ...y: el archivo <{archivo}> está vacío o no existe')
                raise ArchivoPdfVacioONoexiste
        except PeticionDeTrabajoNoValida:
            print(f'ERROR: fallo en [validar_y_procesar_solicitud]')
            raise FalloValidandoYProcesandoSolicitud
        except ArchivoPdfVacioONoexiste:
            print(f'ERROR: fallo en [validar_y_procesar_solicitud]')
            raise FalloValidandoYProcesandoSolicitud
        except FalloConsultandoPaginasArchivoConPyMuPDF:
            print(f'ERROR: fallo en [validar_y_procesar_solicitud]')
            raise FalloValidandoYProcesandoSolicitud
        except:
            peticion = f'ERROR: se ha pedido <{archivo}> [{inicio}-{fin}] *F:{str_firmadas}'
            print(f'ERROR: fallo desconocido al tratar de procesar en [validar_y_procesar_solicitud]')
            print(f'       la petición : {peticion}')
            raise FalloValidandoYProcesandoSolicitud

    @staticmethod
    def trocear_archivo(inicio, fin, lista_paginas_firmadas, archivo):
        """
        Recibe un rango de páginas a copiar de un PDF, seguido de la lista de páginas que requieren
        ser capturadas/renderizadas dado que contienen firmas digitales, y por último el nombre del
        archivo pdf que contiene los datos. Devuelve una lista de mini-pdfs que concatenados suponen
        la zona de archivo deseada. Digamos que es la función final de trabajo de la aplicación.
        """
        try:
            lista_de_trabajos = Core.validar_y_procesar_solicitud(inicio, fin, lista_paginas_firmadas, archivo)
            lista_mini_pdfs = []
            for trabajo in lista_de_trabajos:
                if trabajo.confirma:
                    # PDF -> PDF.páginas -> PNG -> páginas(png) -> pdf -> PDF
                    lista_mini_pdfs.append(Core.capturar_paginas_de_pdf_a_minipdf(trabajo))
                else:
                    # PDF -> PDF.páginas -> PDF
                    lista_mini_pdfs.append(Core.extraer_rango_de_paginas_de_pdf_a_mini_pdf(trabajo))
            return lista_mini_pdfs
        except FalloValidandoYProcesandoSolicitud:
            print(f'ERROR: fallo en [validar_y_procesar_solicitud] llamando desde [trocear_archivo]')
            exit()
        except FalloCapturandoPaginasDePdfAMiniPdf:
            print(f'ERROR: fallo en [capturar_paginas_de_pdf_a_minipdf] llamando desde [trocear_archivo]')
            exit()
        except FalloAlExtraerPaginasPdfAMiniPdf:
            print(f'ERROR: fallo en [extraer_rango_de_paginas_de_pdf_a_mini_pdf] llamando desde [trocear_archivo]')
            exit()
        except:
            print(f'ERROR: desconocido en [trocear_archivo]')
            exit()


class Indice:
    """
    La clase INDICE contiene los métodos estáticos que permiten construir las primeras
    páginas de nuestro documento final. El índice indicando las páginas de cada documento.
    """

    @staticmethod
    def conversor_a_lineas(frase, anchura_maxima_caracteres_por_linea):
        palabras = frase.split(' ')
        actual = ''
        lineas = []
        for palabra in palabras:
            if len(palabra) + len(actual) <= anchura_maxima_caracteres_por_linea:
                actual += f'{palabra} '
            else:
                lineas.append(actual)
                actual = f'{palabra} '
        lineas.append(actual)
        return lineas

    @staticmethod
    def definir_distribucion_del_indice(lista_docus, anchura, interlineado, primera_linea, ultima_linea):
        lista_docus_2 = []
        for i, docu in zip(range(len(lista_docus)), lista_docus):
            lista = list(docu.items())
            paginas_totales_del_documento = lista[0][0]
            texto_en_una_linea = lista[0][1]
            texto_descriptivo_multiline = Indice.conversor_a_lineas(texto_en_una_linea, anchura)
            lista_docus_2.append([paginas_totales_del_documento, texto_descriptivo_multiline, i + 1])
        paginas_del_indice = []
        pagina_actual = []
        altura_linea = 0 + primera_linea
        for docu in lista_docus_2:
            tmp = altura_linea + 0
            altura_linea += interlineado
            for linea in docu[1]:
                altura_linea += interlineado
            altura_linea += 4  # separación entre párrafos ......................................................
            if altura_linea < ultima_linea:
                pagina_actual.append(docu)
            else:
                paginas_del_indice.append([] + pagina_actual)
                pagina_actual.clear()
                pagina_actual.append(docu)
                altura_linea = (altura_linea - tmp) + primera_linea
        paginas_del_indice.append([] + pagina_actual)
        return paginas_del_indice

    @staticmethod
    def crear_indice(lista_docus: list, anchura_maxima=52, interlineado=7, primera_linea=45, ultima_linea=290):
        # LISTA_DOCUS [ {numero_de_paginas: 'texto libre del usuario'},...]
        indice = Indice.definir_distribucion_del_indice(lista_docus, anchura_maxima, interlineado,
                                                        primera_linea, ultima_linea)
        # INDICE = [ pagina1, pagina2, pagina3 ]
        #    donde pagina = [bloque1, bloque2, bloque3, bloque4]
        #           donde bloque = [paginas_totales_docu:int, texto_descriptivo: list str, num_doc: int].
        paginas_del_indice = len(indice)
        paginas_hasta_ahora = paginas_del_indice + 0
        nuevo_pdf = FPDF(orientation='P', unit='mm', format='A4')  # creamos PDF en memoria
        for i, pagina_de_indice in zip(range(len(indice)), indice):
            nuevo_pdf.add_page()  # creamos una página en blanco
            nuevo_pdf.set_font('Courier', 'BI', 24)  # establecemos FUENTE, ESTILO (bold, italic, underline), y TAMAÑO
            nuevo_pdf.text(x=20, y=30, txt='INDICE')  # establecemos margen y texto
            nuevo_pdf.set_font('Courier', 'BI', 16)
            nuevo_pdf.text(x=125, y=29, txt=f'< {len(lista_docus)} documentos >')
            altura_de_linea = 0 + primera_linea
            for bloque in pagina_de_indice:
                # [paginas_totales_docu:int, texto_descriptivo: list str, num_doc: int]
                inicial = paginas_hasta_ahora + 1
                final = paginas_hasta_ahora + bloque[0]
                paginas_hasta_ahora = final
                subtitulo1 = f'Documento {bloque[2]} '
                subtitulo2 = f'({bloque[0]} páginas) de {inicial} a {final}'
                numero_de_puntos = int((anchura_maxima - (len(subtitulo1) + len(subtitulo2))) / 2) + 1
                subtitulo = f'{subtitulo1}{". " * numero_de_puntos}{subtitulo2}'
                nuevo_pdf.set_font('Courier', 'B', 14)
                nuevo_pdf.text(x=30, y=altura_de_linea, txt=subtitulo)
                altura_de_linea += interlineado
                nuevo_pdf.set_font('Courier', '', 14)
                for linea in bloque[1]:
                    nuevo_pdf.text(x=40, y=altura_de_linea, txt=linea)
                    altura_de_linea += interlineado
                altura_de_linea += 4  # separador entre párrafos
        archivo_salida_pdf = crear_nombre_archivo_temporal('pdf')
        nuevo_pdf.output(archivo_salida_pdf)
        return archivo_salida_pdf


class TrabajoDeArchivo:
    """
    Esta clase hace de mediadora entre la clase MIAPP y la clase CORE
    """

    def __init__(self, prim_pag, ult_pag, list_firm, archivo_pdf, descripcion_para_indice,):
        self.primera_pagina = prim_pag
        self.ultima_pagina = ult_pag
        self.lista_firmadas = list_firm
        self.nombre_archivo = archivo_pdf
        self.des = descripcion_para_indice

    def datos_para_indice(self):
        n = (self.ultima_pagina - self.primera_pagina) + 1
        s = str(self.des)
        return {n: s}

    def crear_trocitos(self):
        return Core.trocear_archivo(self.primera_pagina, self.ultima_pagina, self.lista_firmadas, self.nombre_archivo)


class MiApp:
    """
    Esta clase hace de mediadora entre el usuario y el resto de la aplicación;
    pide datos y gestiona, interactuando con las clases INDICE y CORE.
    """

    def __init__(self):
        self.contenedor_de_trabajos_de_archivos = []

    def agregar(self, trabajo: TrabajoDeArchivo):
        self.contenedor_de_trabajos_de_archivos.append(trabajo)

    def construir_indice(self):
        """
        recorre los datos facilitados por el usuario,
        coge lo necesario, y construye el índice
        """
        lista_datos_para_indice_por_documento = []
        for trabajo in self.contenedor_de_trabajos_de_archivos:
            lista_datos_para_indice_por_documento.append(trabajo.datos_para_indice())
        return Indice.crear_indice(lista_datos_para_indice_por_documento)

    def construir_nuevo_documento(self):
        """
        recorre los datos facilitados por el usuario,
        construye el índice, y los trocitos de documento;
        para finalmente unir los trozos en el resultado.
        """
        if len(self.contenedor_de_trabajos_de_archivos) == 0:
            return '<< NINGUNO >> ya que no se recibió ningún documento'
        else:
            print(f'\n*** Empezando a leer los {len(self.contenedor_de_trabajos_de_archivos)} documentos')
            archivo_indice = self.construir_indice()
            print(f'    > construido documento índice: {archivo_indice}')
            pack_pdfs = [archivo_indice]
            for trabajo in self.contenedor_de_trabajos_de_archivos:
                pack_pdfs += trabajo.crear_trocitos()
            return Core.unir_mini_pdfs_en_mini_pdf(pack_pdfs)

    def pedir_nuevo_trabajo(self):
        archivo = input('\n + Introduzca nombre de archivo (pulse enter para finalizar): ')
        if not mi_existe_archivo(archivo):
            if archivo == '':
                print(f'    --> Recogida de nuevos trabajos finalizada')
            else:
                print(f'    --> El archivo {archivo} No Existe')
            return None
        else:
            paginas_totales = consultar_paginas_pdf(archivo)
            p_i = 0
            p_f = 0
            rango = input(f'   -> Rango de las {paginas_totales} páginas (ej: 8  5,6  EN_BLANCO para todas): ')
            if rango == '':
                p_i += 1
                p_f += paginas_totales
            else:
                paginas = rango.replace(' ', ',').replace('-', ',').replace('.', ',').split(',')
                if len(paginas) == 1:
                    p_i += int(paginas[0])
                    p_f += int(paginas[0])
                else:
                    p_i += int(paginas[0])
                    p_f += int(paginas[1])
            if (0 < p_i <= paginas_totales) and (p_i <= p_f <= paginas_totales):
                p_l = []
                firmadas = input(f'   -> Lista de páginas firmadas (ej: 8  5,6  EN_BLANCO para ninguna): ')
                if firmadas != '':
                    lista = firmadas.replace(' ', ',').replace('-', ',').replace('.', ',').split(',')
                    p_l += [int(num) for num in lista]
                    if max(p_l) > p_f or min(p_l) < p_i:
                        print(f'    --> Páginas firmadas fuera del RangoVálido: {p_i} a {p_f}')
                        return None
                p_d = input(f'   -> Texto descriptivo para el índice (sin límite, pero en un párrafo todo): ')
                if p_d == '':
                    print(f'    --> Texto para índice es obligatorio...')
                    return None
                else:
                    trabajo = TrabajoDeArchivo(p_i, p_f, p_l, archivo, p_d)
                    self.agregar(trabajo)
                    return trabajo
            else:
                print(f'    --> Rango No Válido: {p_i} a {p_f} de {paginas_totales}')
                return None

    def main(self):
        print('\n*** Concatenador de documentos PDF, que agrega un índice ***')
        print('** v.1.0  de Patxi50unosyceros  unosycerospatxi@gmail.com **')
        trabajo = self.pedir_nuevo_trabajo()
        while trabajo is not None:
            print(f'\tAceptado trabajo con archivo: {trabajo.nombre_archivo}')
            trabajo = self.pedir_nuevo_trabajo()
        print(f'\n*** Archivo resultante {self.construir_nuevo_documento()} ***\n')
        os.system('pause')


app = MiApp()  # creamos un objeto de clase Aplicación
app.main()   # llamamos
