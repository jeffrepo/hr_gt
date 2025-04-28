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

class recibo_pago_wizard(models.TransientModel):
    _name = 'hr_gt.recibo_pago.wizard'

    lote_id = fields.Many2one('hr.payslip.run', string='Lote', required=True)
    formato_recibo_pago_id = fields.Many2one('hr_gt.recibo_pago','Formato recibo pago', required=True)
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

    def print_report(self):
        data = {
             'ids': [],
             'model': 'hr_gt.recibo_pago.wizard',
             'form': self.read()[0]
        }
        logging.warning(data)
        return self.env.ref('hr_gt.action_recibo_pago').report_action(self, data=data)