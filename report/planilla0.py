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
    formato_planilla_id = fields.Many2one('hr_gt.planilla','Formato planilla', required=True)
    archivo = fields.Binary('Archivo')
    name =  fields.Char('File Name', size=32)
    columna_igss = fields.Boolean('Agregar columna IGSS')
    agrupar_departamento = fields.Boolean('Agrupa por departamento')
    fecha_inicio = fields.Date('Fecha inicio')
    fecha_fin = fields.Date('Fecha fin')


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
            hoja.write(0, 1, '')
            hoja.write(0, 2, 'Periodo')
            hoja.write(0, 3, w.fecha_inicio, formato_fecha)
            hoja.write(0, 4, w.fecha_fin, formato_fecha)
            #
            #
            hoja.write(2,0,'Nombre')
            hoja.write(2,1,'IGSS')
            hoja.write(2,2,'Puesto')
            hoja.write(2,3,'Base mensual')
            hoja.write(2,4,'Bonificacion')
            hoja.write(2,5,'Dias trabajados')
            #
            contador = 6
            cantidad_ingreso = 6
            numero_ingresos = 0
            cantidad_deduccion = 0
            total_total = 0
            for linea_ingreso in w.formato_planilla_id.ingreso_ids:
                hoja.write(2,contador,linea_ingreso.nombre)
                cantidad_ingreso += 1
                contador += 1
                numero_ingresos += 1

            hoja.merge_range(1, 6, 1, cantidad_ingreso-1, 'INGRESOS', merge_format)

            columna_total_ingreso = cantidad_ingreso
            hoja.write(2,cantidad_ingreso,'TOTAL INGRESOS')

            cantidad_deduccion = cantidad_ingreso+1
            for linea_descuento in w.formato_planilla_id.deduccion_ids:
                hoja.write(2,cantidad_ingreso+1,linea_descuento.nombre)
                cantidad_deduccion += 1
            #
            hoja.merge_range(1, cantidad_ingreso+1, 1, cantidad_deduccion-1, 'DESCUENTOS', merge_format)

            columna_total_descuento = cantidad_deduccion
            hoja.write(2,cantidad_deduccion,'TOTAL DESCUENTOS')

            hoja.write(2,cantidad_deduccion+1,'TOTAL LIQUIDO A RECIBIR')

            fila = 3
            contador_columna = 0
            monto_total_ingreso = 0
            monto_total_descuento = 0
            totales = {}

            nominas_lista = {}
            for nomina in w.nomina_ids:
                for slip in nomina.slip_ids:
                    if slip.employee_id.id not in nominas_lista:
                        nominas_lista[slip.employee_id.id] = {'nominas': [], 'empleado': slip.employee_id}
                    nominas_lista[slip.employee_id.id]['nominas'].append(slip)

            logging.warn(nominas_lista)

            for nomina in nominas_lista:
                logging.warn(nomina)
                hoja.write(fila,0,nominas_lista[nomina]['nominas'][0].employee_id.name)
                hoja.write(fila,1,'')
                hoja.write(fila,2,nominas_lista[nomina]['nominas'][0].employee_id.department_id.name)
                hoja.write(fila,3,nominas_lista[nomina]['nominas'][0].contract_id.wage)
                hoja.write(fila,4,nominas_lista[nomina]['nominas'][0].contract_id.bonificacion_incentivo)
            #
                dias_trabajados = 0
                for payslip in nominas_lista[nomina]['nominas']:
                    for linea_trabajo in payslip.worked_days_line_ids:
                        if linea_trabajo.code == 'DIAS':
                            dias_trabajados += linea_trabajo.number_of_days

                hoja.write(fila,5,dias_trabajados)
            #
                contador_columna = 6
                total_ingreso = 0
                tamanio_ingreso = 1
                logging.warn(len(w.formato_planilla_id.ingreso_ids))
                for linea_ingreso in w.formato_planilla_id.ingreso_ids:
                    dato = 0
                    for payslip in nominas_lista[nomina]['nominas']:
                        for regla in payslip.line_ids:
                            if regla.salary_rule_id.id in linea_ingreso.regla_ids.ids:
                                dato += regla.total
            #
            #
                    hoja.write(fila,contador_columna, dato)
            #
            #
                    tamanio_ingreso += 1
            #
                    if contador_columna not in totales:
                        totales[contador_columna] = {'columna': contador_columna, 'total': 0}
                    totales[contador_columna]['total'] += dato
                    total_ingreso += dato

                    contador_columna += 1
            #
            #     logging.warn(total_ingreso)
                hoja.write(fila,columna_total_ingreso,total_ingreso)
                monto_total_ingreso += total_ingreso

                contador_columna+= 1
                total_descuento = 0
                for linea_deduccion in w.formato_planilla_id.deduccion_ids:
                    dato = 0
                    for payslip in nominas_lista[nomina]['nominas']:
                        for regla in payslip.line_ids:
                            if regla.salary_rule_id.id in linea_deduccion.regla_ids.ids:
                                if regla.total > 0:

                                    dato += (regla.total * -1)
                                else:
                                    dato += regla.total
            #
            #
                    hoja.write(fila,contador_columna, dato)
                    if contador_columna not in totales:
                        totales[contador_columna] = {'columna': contador_columna, 'total': 0}
                    totales[contador_columna]['total'] += dato

                    total_descuento += dato
                    contador_columna += 1
            #
            #
                hoja.write(fila,contador_columna,total_descuento)
                monto_total_descuento += total_descuento

                total_liquido = total_ingreso + total_descuento
                contador_columna += 1
                hoja.write(fila,contador_columna,total_liquido)
                total_total += total_liquido
                fila += 1
            #
            for llave in totales:
                hoja.write(fila,totales[llave]['columna'],totales[llave]['total'])
            hoja.write(fila,columna_total_ingreso,monto_total_ingreso)
            hoja.write(fila,columna_total_descuento,monto_total_descuento)
            hoja.write(fila,contador_columna, total_total)
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

    @api.multi
    def print_report(self):
        datas = {'ids': self.env.context.get('active_ids', [])}
        res = self.read(['nomina_id','formato_planilla_id'])
        res = res and res[0] or {}
        datas['form'] = res
        return self.env.ref('hr_gt.action_planilla').report_action([], data=datas)
