# -*- encoding: utf-8 -*-

from odoo import api, models, fields
from datetime import date
import datetime
import time
import dateutil.parser
from dateutil.relativedelta import relativedelta
from dateutil import relativedelta as rdelta
from odoo.fields import Date, Datetime
import logging
# import odoo.addons.hr_gt.a_letras

class ReportIGSS(models.AbstractModel):
    _name = 'report.hr_gt.igss'

    def mes_letras(self,datos):
        nomina_id = self.env['hr.payslip.run'].search([('id','in',datos['nomina_ids'])])
        mes_nomina = int(datetime.datetime.strptime(str(nomina_id.date_start), '%Y-%m-%d').date().strftime('%m'))
        anio_nomina = int(datetime.datetime.strptime(str(nomina_id.date_start), '%Y-%m-%d').date().strftime('%Y'))
        anio_hoy =  int(datetime.datetime.strptime(str(date.today()), '%Y-%m-%d').date().strftime('%Y'))
        mes_hoy =  int(datetime.datetime.strptime(str(date.today()), '%Y-%m-%d').date().strftime('%m'))
        dia_hoy =  int(datetime.datetime.strptime(str(date.today()), '%Y-%m-%d').date().strftime('%d'))
        logging.warn(dia_hoy)
        mes =  ''
        if mes_nomina == 1:
            mes = 'ENERO'
        if mes_nomina == 2:
            mes = 'FEBRERO'
        if mes_nomina == 3:
            mes = 'MARZO'
        if mes_nomina == 4:
            mes = 'ABRIL'
        if mes_nomina == 5:
            mes = 'MAYO'
        if mes_nomina == 6:
            mes = 'JUNIO'
        if mes_nomina == 7:
            mes = 'JULIO'
        if mes_nomina == 8:
            mes = 'AGOSTO'
        if mes_nomina == 9:
            mes = 'SEPTIEMBRE'
        if mes_nomina == 10:
            mes = 'OCTUBRE'
        if mes_nomina == 11:
            mes = 'NOVIEMBRE'
        if mes_nomina == 12:
            mes = 'DICIEMBRE'
        return {'mes': mes, 'anio': anio_nomina, 'del':nomina_id.date_start ,'al':nomina_id.date_end,'anio_hoy': anio_hoy,'mes_hoy': mes,'dia_hoy': dia_hoy}

    def _get_recibos(self,datos):
        recibos_lista = []
        logging.warn(datos)
        nomina_id = self.env['hr.payslip.run'].search([('id','in',datos['nomina_ids'])])
        recibo_pago_id = self.env['hr_gt.recibo_pago'].search([('id','=',datos['formato_recibo_pago_id'][0])])
        for planilla in nomina_id.slip_ids:
            dic = {
                'empleado': planilla.employee_id,
                'recibo_pago': recibo_pago_id,
                'puesto': planilla.employee_id.job_id.name,
                'ingresos': {},
                'deducciones': {},
                'dias_trabajados': 0,
                'total_ingresos': 0,
                'total_deducciones': 0,
                'liquido_recibir': 0
            }

            if planilla.line_ids:
                for dias in planilla.worked_days_line_ids:
                    if dias.code == 'DIAS':
                        dic['dias_trabajados'] = dias.number_of_days


            if recibo_pago_id.ingreso_ids:
                for ingreso in recibo_pago_id.ingreso_ids:
                    if ingreso.id not in dic['ingresos']:
                        dic['ingresos'][ingreso.id] = {'nombre': ingreso.nombre, 'total': 0}

                    if planilla.line_ids:
                        for linea in planilla.line_ids:
                            if linea.salary_rule_id.id in ingreso.regla_ids.ids:
                                dic['ingresos'][ingreso.id]['total'] += linea.total
                                dic['total_ingresos'] += linea.total
                                dic['liquido_recibir'] += linea.total

            if recibo_pago_id.deduccion_ids:
                for deduccion in recibo_pago_id.deduccion_ids:
                    if deduccion.id not in dic['deducciones']:
                        dic['deducciones'][deduccion.id] = {'nombre': deduccion.nombre, 'total': 0}

                    if planilla.line_ids:
                        for linea in planilla.line_ids:
                            if linea.salary_rule_id.id in deduccion.regla_ids.ids:
                                if linea.total < 0:
                                    dic['deducciones'][deduccion.id]['total'] += (linea.total *-1)
                                    dic['total_deducciones'] += (linea.total*-1)
                                    dic['liquido_recibir'] -= (linea.total*-1)
                                else:
                                    dic['deducciones'][deduccion.id]['total'] += (linea.total)
                                    dic['total_deducciones'] += (linea.total)
                                    dic['liquido_recibir'] -= (linea.total)

            recibos_lista.append(dic)

        logging.warn(recibos_lista)
        return recibos_lista


    def fecha_hoy(self):
        return date.today().strftime("%d/%m/%Y")
    # def pagos_deducciones(self,o):
    #     ingresos = 0
    #     descuentos = 0
    #     datos = {'ordinario': 0, 'extra_ordinario':0,'bonificacion':0}
    #     for linea in o.linea_ids:
    #         if linea.salary_rule_id.id in o.company_id.ordinario_ids.ids:
    #             datos['ordinario'] += linea.total
    #         elif linea.salary_rule_id.id in o.company_id.extra_ordinario_ids.ids:
    #             datos['extra_ordinario'] += linea.total
    #         elif linea.salary_rule_id.id in o.company_id.bonificacion_ids.ids:
    #             datos['bonificacion'] += linea.total
    #     return True

    # @api.model
    # def _get_report_values(self, docids, data=None):
    #     return self.get_report_values(docids, data)


# {'context': {'tz': False, 'uid': 1, 'params':
# {'action': 473}, 'active_model': 'hr_gt.recibo_pago.wizard', 'active_id': 5, 'active_ids': [5], 'search_disable_custom_filters': True}, 'ids': [], 'model': 'hr_gt.recibo_pago.wizard', 'form': {'id': 5, 'nomina_ids': [17], 'formato_recibo_pago_id': [1, 'RECIBO DE PAGO PLANILLA'], 'fecha_inicio': False, 'fecha_fin': False, 'create_uid': [1, 'Administrator'], 'create_date': '2020-06-22 01:42:19', 'write_uid': [1, 'Administrator'], 'write_date': '2020-06-22 01:42:19', 'display_name': 'hr_gt.recibo_pago.wizard,5', '__last_update': '2020-06-22 01:42:19'}}

    @api.model
    def get_report_values(self, docids, data=None):
        self.model = 'hr.payslip.run'
        docs = self.env[self.model].browse(docids)
        logging.warn(data)
        return {
            'doc_ids': docids,
            'doc_model': self.model,
            'docs': docs,
            '_get_recibos': self._get_recibos,
            'data': data['form'],
            'mes_letras': self.mes_letras,
            # 'mes_letras': self.mes_letras,
            # 'fecha_hoy': self.fecha_hoy,
            # 'a_letras': odoo.addons.hr_gt.a_letras,
            # 'datos_recibo': self.datos_recibo,
            # 'lineas': self.lineas,
            # 'horas_extras': self.horas_extras,
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
