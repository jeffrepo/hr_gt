# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import time
import base64
import xlsxwriter
import io
import logging
from datetime import date
import datetime
import dateutil.parser
from dateutil.relativedelta import relativedelta
from dateutil import relativedelta as rdelta
from odoo.fields import Date, Datetime

class planilla_wizard(models.TransientModel):
    _name = 'hr_gt.planilla.wizard'

    nomina_ids = fields.Many2many('hr.payslip.run', string='Planillas', required=True)
    formato_planilla_id = fields.Many2one('hr_gt.formato_planilla','Formato planilla', required=True)
    archivo = fields.Binary('Archivo')
    name =  fields.Char('File Name', size=32)
    columna_igss = fields.Boolean('Agregar columna IGSS')
    agrupar_departamento = fields.Boolean('Agrupar por departamento')
    agrupar_estructura = fields.Boolean('Agrupar por estructura')
    base_mensual = fields.Boolean('Incluir base mensual')
    fecha_inicio = fields.Date('Fecha inicio')
    fecha_fin = fields.Date('Fecha fin')
    ordenar_secuencia = fields.Boolean('Por sequencia')


    def busqueda_nominas(self, empleado_id,mes):
        nomina_ids = self.env['hr.payslip'].search([('employee_id','=',empleado_id.id)])
        nominas = []
        for nomina in nomina_ids:
            mes_nomina = int(datetime.datetime.strptime(str(nomina.date_to), '%Y-%m-%d').date().strftime('%m'))
            if empleado_id.id == nomina.employee_id.id and mes == mes_nomina:
                nominas.append(nomina)
        return nominas

    def generar_excel(self):
        for w in self:
            f = io.BytesIO()
            libro = xlsxwriter.Workbook(f)
            formato_fecha = libro.add_format({'num_format': 'dd/mm/yy'})
            hoja = libro.add_worksheet('Planilla')

            merge_format = libro.add_format({'align': 'center'})

            hoja.write(0, 0, 'Planilla')
            if len(w.nomina_ids) == 1:
                hoja.write(0, 1, w.nomina_ids[0].name)
            elif len(w.nomina_ids) > 1:
                lista_nominas = []
                for n in w.nomina_ids:
                    lista_nominas.append(n.name)

                hoja.write(0, 1, ', '.join(lista_nominas))
            else:
                hoja.write(0, 1, '')
            hoja.write(0, 2, 'Periodo')
            hoja.write(0, 3, w.fecha_inicio, formato_fecha)
            hoja.write(0, 4, w.fecha_fin, formato_fecha)
            #
            #
            {'1314': [5,10], '1516':[90,20]}
            datos = {}
            ingresos_lista = []
            egresos_lista = []
            if w.formato_planilla_id.ingreso_ids:
                ingresos_lista = [0]*len(w.formato_planilla_id.ingreso_ids)
            if w.formato_planilla_id.egreso_ids:
                egresos_lista = [0]*len(w.formato_planilla_id.egreso_ids)

            logging.warning(ingresos_lista)
            logging.warning(egresos_lista)
            if w.agrupar_estructura:
                if w.nomina_ids:
                    for lote in w.nomina_ids:
                        if lote.slip_ids:
                            for nomina in lote.slip_ids:
                                if nomina.line_ids and nomina.struct_id.id:
                                    if nomina.struct_id.id not in datos:
                                        totales_ingresos_lista = ingresos_lista
                                        totales_egresos_lista = egresos_lista

                                        datos[nomina.struct_id.id] ={'nombre_agrupado': nomina.struct_id.name,'empleados':{},'totales_ingresos': [0]*len(w.formato_planilla_id.ingreso_ids),'totales_egresos':  [0]*len(w.formato_planilla_id.egreso_ids) }

                                    if nomina.employee_id.id not in datos[nomina.struct_id.id]['empleados']:
                                        ingresos_lista_temporal = ingresos_lista
                                        egresos_lista_temporal = egresos_lista
                                        datos[nomina.struct_id.id]['empleados'][nomina.employee_id.id] = {'nombre_empleado':nomina.employee_id.name,'ingresos': [0]*len(w.formato_planilla_id.ingreso_ids),'egresos': [0]*len(w.formato_planilla_id.egreso_ids) }

                                    for linea in nomina.line_ids:
                                            if w.formato_planilla_id.ingreso_ids:
                                                for columna in w.formato_planilla_id.ingreso_ids:
                                                    if linea.salary_rule_id.id in columna.regla_ids.ids:
                                                    # logging.warning('POSICION')
                                                    # logging.warning(w.formato_planilla_id.ingreso_ids)
                                                    # logging.warning(w.formato_planilla_id.ingreso_ids.ids.index(columna.id))
                                                        posicion_ingreso_regla = w.formato_planilla_id.ingreso_ids.ids.index(columna.id)
                                                        if posicion_ingreso_regla >= 0:
                                                            datos[nomina.struct_id.id]['empleados'][nomina.employee_id.id]['ingresos'][posicion_ingreso_regla] = linea.total
                                                            datos[nomina.struct_id.id]['totales_ingresos'][posicion_ingreso_regla] += linea.total
                                            if w.formato_planilla_id.egreso_ids:
                                                for columna in w.formato_planilla_id.egreso_ids:
                                                    if linea.salary_rule_id.id in columna.regla_ids.ids:
                                                        logging.warning('S I ESTA EGRESO')
                                                        posicion_egreso_regla = w.formato_planilla_id.egreso_ids.ids.index(columna.id)
                                                        logging.warning(posicion_egreso_regla)
                                                        if posicion_egreso_regla >= 0:
                                                            logging.warning('agrega')
                                                            datos[nomina.struct_id.id]['empleados'][nomina.employee_id.id]['egresos'][posicion_egreso_regla] = linea.total
                                                            datos[nomina.struct_id.id]['totales_egresos'][posicion_egreso_regla] += linea.total
            if w.agrupar_departamento:
                if w.nomina_ids:
                    for lote in w.nomina_ids:
                        if lote.slip_ids:
                            for nomina in lote.slip_ids:
                                if nomina.line_ids and nomina.contract_id and nomina.contract_id.department_id:
                                    if nomina.contract_id.department_id.id not in datos:
                                        totales_ingresos_lista = ingresos_lista
                                        totales_egresos_lista = egresos_lista
                                        datos[nomina.contract_id.department_id.id] ={'nombre_agrupado': nomina.contract_id.department_id.name,'empleados':{},'totales_ingresos': [0]*len(w.formato_planilla_id.ingreso_ids),'totales_egresos':  [0]*len(w.formato_planilla_id.egreso_ids)}

                                    if nomina.employee_id.id not in datos[nomina.contract_id.department_id.id]['empleados']:
                                        ingresos_lista_temporal = ingresos_lista
                                        egresos_lista_temporal = egresos_lista
                                        datos[nomina.contract_id.department_id.id]['empleados'][nomina.employee_id.id] = {'nombre_empleado': nomina.employee_id.name,'ingresos': [0]*len(w.formato_planilla_id.ingreso_ids),'egresos':  [0]*len(w.formato_planilla_id.egreso_ids) }

                                    for linea in nomina.line_ids:
                                        if w.formato_planilla_id.ingreso_ids:
                                            for columna in w.formato_planilla_id.ingreso_ids:
                                                if linea.salary_rule_id.id in columna.regla_ids.ids:
                                                    logging.warning('POSICION')
                                                    logging.warning(w.formato_planilla_id.ingreso_ids)
                                                    logging.warning(w.formato_planilla_id.ingreso_ids.ids.index(columna.id))
                                                    posicion_ingreso_regla = w.formato_planilla_id.ingreso_ids.ids.index(columna.id)
                                                    if posicion_ingreso_regla >= 0:
                                                        datos[nomina.contract_id.department_id.id]['empleados'][nomina.employee_id.id]['ingresos'][posicion_ingreso_regla] = linea.total
                                                        datos[nomina.contract_id.department_id.id]['totales_ingresos'][posicion_ingreso_regla] += linea.total
                                        if w.formato_planilla_id.egreso_ids:
                                            for columna in w.formato_planilla_id.egreso_ids:
                                                if linea.salary_rule_id.id in columna.regla_ids.ids:
                                                    posicion_egreso_regla = w.formato_planilla_id.egreso_ids.ids.index(columna.id)
                                                    if posicion_egreso_regla >= 0:
                                                        datos[nomina.contract_id.department_id.id]['empleados'][nomina.employee_id.id]['egresos'][posicion_egreso_regla] = linea.total
                                                        datos[nomina.contract_id.department_id.id]['totales_egresos'][posicion_egreso_regla] += linea.total
            # else:

            logging.warning('DATOS')
            logging.warning(datos)
            total_general = 0
            cell_format_bold = libro.add_format({'bold': True})

            if datos:
                # hoja.write(2,0,'Nombre')
                fila = 2
                # columna = 0
                for dato in datos:
                    if datos[dato]['empleados']:
                        columna = 0
                        columna_encabezado = 1
                        fila += 1
                        hoja.write(fila,0,datos[dato]['nombre_agrupado'],cell_format_bold)
                        fila += 1
                        hoja.write(fila,0,'Nombre',formato_fecha)
                        if w.formato_planilla_id.ingreso_ids:
                            for columna_ingreso in w.formato_planilla_id.ingreso_ids:
                                hoja.write(fila,columna_encabezado,columna_ingreso.nombre,cell_format_bold)
                                columna_encabezado += 1

                        if w.formato_planilla_id.egreso_ids:
                            for columna_egreso in w.formato_planilla_id.egreso_ids:
                                hoja.write(fila,columna_encabezado,columna_egreso.nombre,cell_format_bold)
                                columna_encabezado += 1

                        hoja.write(fila,columna_encabezado,'Total',cell_format_bold)
                        empleados_info = datos[dato]['empleados']
                        fila += 1
                        for empleado in empleados_info:
                            # logging.warning(empleados_info[empleado])
                            columna_empleado = 0
                            hoja.write(fila,columna_empleado,str(empleados_info[empleado]['nombre_empleado']))
                            columna_empleado += 1
                            total_salario = 0
                            for valor in empleados_info[empleado]['ingresos']:
                                hoja.write(fila,columna_empleado,valor)
                                total_salario += valor
                                columna_empleado += 1
                            for valor in empleados_info[empleado]['egresos']:
                                hoja.write(fila,columna_empleado,valor)
                                total_salario += valor
                                columna_empleado += 1

                            hoja.write(fila,columna_empleado,total_salario)
                            fila += 1
                            columna += 1

                        columna_totales = 1
                        total_agrupado = 0
                        for valor in datos[dato]['totales_ingresos']:
                            hoja.write(fila,columna_totales,valor,cell_format_bold)
                            total_agrupado += valor
                            columna_totales += 1

                        for valor in datos[dato]['totales_egresos']:
                            hoja.write(fila,columna_totales,valor,cell_format_bold)
                            total_agrupado += valor
                            columna_totales += 1
                        hoja.write(fila,columna_totales,total_agrupado,cell_format_bold)
                        total_general += total_agrupado
                        fila += 1

                hoja.write(fila,0,'TOTAL SALARIOS',cell_format_bold)
                hoja.write(fila,1,total_general,cell_format_bold)
            # hoja.write(2,1,'IGSS')
            # hoja.write(2,2,'Puesto')
            # hoja.write(2,3,'Base mensual')
            # hoja.write(2,4,'Bonificacion')
            # hoja.write(2,5,'Dias trabajados')
            #
            # contador = 6
            # cantidad_ingreso = 6
            # numero_ingresos = 0
            # cantidad_deduccion = 0
            # total_total = 0
            # for linea_ingreso in w.formato_planilla_id.ingreso_ids:
            #     hoja.write(2,contador,linea_ingreso.nombre)

            libro.close()
            datos = base64.b64encode(f.getvalue())
            self.write({'archivo': datos, 'name':'planilla.xls'})
            return {
                'context': self.env.context,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'hr_gt.planilla.wizard',
                'res_id': self.id,
                'view_id': False,
                'type': 'ir.actions.act_window',
                'target': 'new',
            }

    def print_report(self):
        datas = {'ids': self.env.context.get('active_ids', [])}
        res = self.read(['nomina_id','formato_planilla_id'])
        res = res and res[0] or {}
        datas['form'] = res
        return self.env.ref('hr_gt.action_planilla').report_action([], data=datas)
