# -*- coding: utf-8 -*-

from odoo import models, fields, api
import datetime
import logging
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError, AccessError
from dateutil.relativedelta import *
import calendar

class hr_gt_formato_planilla(models.Model):
    _name = 'hr_gt.formato_planilla'
    _rec_name = 'nombre'

    nombre = fields.Char('Nombre planilla')
    salario = fields.Boolean('Incluir salario')
    ingreso_ids = fields.One2many('hr_gt.ingreso_columna','formato_id','Ingresos')
    egreso_ids = fields.One2many('hr_gt.egreso_columna','formato_id','Egresos')


class hr_gt_planilla_ingreso(models.Model):
    _name = 'hr_gt.ingreso_columna'
    _rec_name = 'nombre'

    formato_id = fields.Many2one('hr_gt.formato_planilla','Formato')
    nombre = fields.Char('Nombre')
    regla_ids = fields.Many2many('hr.salary.rule',string='Reglas')

class hr_planilla_egreso(models.Model):
    _name = 'hr_gt.egreso_columna'
    _rec_name = 'nombre'

    formato_id = fields.Many2one('hr_gt.formato_planilla','Formato')
    nombre = fields.Char('Nombre')
    regla_ids = fields.Many2many('hr.salary.rule',string='Reglas')
