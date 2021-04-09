# -*- coding: utf-8 -*-

from odoo import models, fields, api

class res_company(models.Model):
    _inherit = 'res.company'

    centro_ids = fields.One2many('res.company.centro','company_id',string="Centros")
    # igss empresa
    # numero_patronal = fields.Char('Numero patronal')
    version_mensaje = fields.Char('Version del mensaje')
    tipo_planilla_ids = fields.One2many('res.company.tipo_planilla','company_id',string="Tipo planilla")
    liquidacion_ids = fields.One2many('res.company.liquidacion','company_id',string="Liquidacion")



class res_company_centro(models.Model):
    _name = 'res.company.centro'

    company_id = fields.Many2one('res.company',string='Compañia',required=True, readonly=True, default=lambda self: self.env.company.id)
    codigo = fields.Char('Código')
    nombre = fields.Char('Nombre')
    direccion = fields.Char('Dirección')
    zona = fields.Char('Zona')
    telefono = fields.Char('Teléfono')
    fax = fields.Char('Fax')
    nombre_contacto = fields.Char('Nombre contacto')
    centro = fields.Char('Centro')
    correo_electronico = fields.Char('Correo electronico')
    codigo_departamento = fields.Char('Codigo departamento')
    codigo_municipio = fields.Char('Código municipio')
    codigo_actividad_economica = fields.Char('Codigo actividad economica')
    cuenta_analitica_id = fields.Many2one('account.analytic.account',string='Cuenta analitica',required=True, readonly=True)



class res_company_tipo_planilla(models.Model):
    _name = 'res.company.tipo_planilla'

    company_id = fields.Many2one('res.company',string='Compañia',required=True, readonly=True, default=lambda self: self.env.company.id)
    identificacion_tipo_planilla = fields.Char('Identificación tipo de planilla')
    nombre_tipo_planilla = fields.Char('Nombre tipo de planilla')
    tipo_afiliados = fields.Char('Tipo de afiliado')
    periodo_planilla = fields.Char('Periodo de planilla')
    departamento_republica = fields.Char('Departamento de la república donde laboran los empleados ')
    actividad_economica = fields.Char('Actividad económica')
    clase_planilla = fields.Char('Clase de planilla')

class res_company_tipo_planilla(models.Model):
    _name = 'res.company.liquidacion'

    company_id = fields.Many2one('res.company',string='Compañia',required=True, readonly=True, default=lambda self: self.env.company.id)
    name = fields.Char('Numero de liquidadcion')
    tipo_planilla_id = fields.Many2one('res.company.tipo_planilla', 'Tipo planilla')
    liquidacion_complementario = fields.Char('Liquidadcion complementarios')
    numero_nota_cargo =fields.Char('Numero nota cargo')
