# -*- coding: utf-8 -*-

from odoo import models, fields, api
import datetime
import logging
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError, AccessError
from dateutil.relativedelta import *
import calendar


class hr_gt_recibo_pago(models.Model):
    _name = 'hr_gt.recibo_pago'
     _description = "Recibo de pago"

    name = fields.Char('Nombre planilla')
    ingreso_ids = fields.Many2many("hr.salary.rule", "ingreo_ids_rel", string="Ingresos")
    ingreso_regla_ids = fields.One2many("hr_gt.ingreso", "recibo_id", string="Ingreso")
    deduccion_regla_ids = fields.One2many("hr_gt.deduccion", "recibo_id", string="Deduccion")
    deduccion_ids = fields.Many2many("hr.salary.rule", "deduccion_ids_rel", string="Deducciones")

class hr_gt_ingreso(models.Model):
    _name = 'hr_gt.ingreso'
    _rec_name = "regla_id"
    _description = "Reglas para ingresos"
    _order = 'sequence'

    sequence = fields.Integer(string='Sequence', default=10)
    recibo_id = fields.Many2one("hr_gt.recibo_pago", string="Recibo")
    regla_id = fields.Many2one("hr.salary.rule", string="regla")

class hr_gt_deduccion(models.Model):
    _name = 'hr_gt.deduccion'
    _rec_name = "regla_id"
    _description = "Reglas para deducciones"
    _order = 'sequence'

    sequence = fields.Integer(string='Sequence', default=10)
    recibo_id = fields.Many2one("hr_gt.recibo_pago", string="Recibo")
    regla_id = fields.Many2one("hr.salary.rule", string="regla")

class hr_gt_formato_planilla(models.Model):
    _name = 'hr_gt.formato_planilla'

    name = fields.Char('Nombre planilla')
    salario = fields.Boolean('Incluir salario')
    ingreso_ids = fields.One2many('hr_gt.ingreso_columna','formato_id','Ingresos')
    egreso_ids = fields.One2many('hr_gt.egreso_columna','formato_id','Egresos')
    regla_ids = fields.Many2many('hr.salary.rule', string="Reglas")

class hr_gt_planilla_ingreso(models.Model):
    _name = 'hr_gt.ingreso_columna'

    formato_id = fields.Many2one('hr_gt.formato_planilla','Formato')
    name = fields.Char('Nombre')
    regla_ids = fields.Many2many('hr.salary.rule',string='Reglas')

class hr_planilla_egreso(models.Model):
    _name = 'hr_gt.egreso_columna'

    formato_id = fields.Many2one('hr_gt.formato_planilla','Formato')
    name = fields.Char('Nombre')
    regla_ids = fields.Many2many('hr.salary.rule',string='Reglas')


class HrGtOtraEntrada(models.Model):
    _name = 'hr_gt.otra_entrada'
    
    name = fields.Char('Referencia')
    empleado_id = fields.Many2one('hr.employee','Empleado')
    mes = fields.Selection([
        ('1', 'Enero'),
        ('2', 'Febrero'),
        ('3', 'Marzo'),
        ('4', 'Abril'),
        ('5', 'Mayo'),
        ('6', 'Junio'),
        ('7', 'Julio'),
        ('8', 'Agosto'),
        ('9', 'Septiembre'),
        ('10', 'Octubre'),
        ('11', 'Noviembre'),
        ('12', 'Diciembre'),
        ], string='Mes')
    anio = fields.Integer('Año')
    codigo = fields.Char(string='Código',required=True)
    monto = fields.Float('Monto')
    tipo = fields.Selection([('bonificacion', 'Bonificacion'), ('descuento', 'Descuento')], string='Tipo')
    company_id = fields.Many2one('res.company',string='Compañia',required=True, default=lambda self: self.env.company, readonly=False)
    
class HrGtDescuento(models.Model):
    _name = 'hr_gt.descuento'

class HrGtBonificación(models.Model):
    _name = 'hr_gt.bonificacion'

class HrGtMunicipio(models.Model):
    _name = "hr_gt.municipio"
    _description = "Municipios Guatemala"

    code = fields.Integer(string="Código", required=True, index=True)
    name = fields.Char(string="Municipio", required=True)
