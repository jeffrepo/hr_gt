# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

class Contract(models.Model):
    _inherit = "hr.contract"

    bonificacion_incentivo = fields.Monetary('Bonificiación incentivo', digits=(16,2), track_visibility='onchange')
    hora_extra = fields.Float('Hora extra')
    jubilado = fields.Boolean('Jubilado')
    isr = fields.Float('isr')
    salario_total = fields.Monetary('Salario total', compute='calculo_total')

    def calculo_total(self):
        for record in self:
            record.salario_total = record.wage + record.bonificacion_incentivo
