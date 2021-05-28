# -*- coding: utf-8 -*-

from odoo import models, fields, api
import datetime
import logging
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError, AccessError
from dateutil.relativedelta import *
import calendar

class hr_employee(models.Model):
    _inherit = 'hr.employee'

    id_sistema = fields.Char('ID sistema')
    igss = fields.Char('IGSS')
    irtra = fields.Char('IRTRA')
    nit = fields.Char('NIT')
    primer_nombre = fields.Char('Primer nombre')
    segundo_nombre = fields.Char('Segundo nombre')
    primer_apellido = fields.Char('Primer apellido')
    segundo_apellido = fields.Char('Segundo apellido')
    apellido_casada = fields.Char('Apellido casada')
    centro_trabajo_id = fields.Many2one('res.company.centro','Centro de trabajo')
    codigo_ocupacion = fields.Char('Codigo ocupacion')
    tipo_sangre = fields.Char('Tipo sangre')
    condicion_laboral = fields.Selection([('P', 'Permanente'), ('T', 'Temporal')], 'Condicion laboral')
    estado_civil_igss = fields.Char('Estado civil IGSS')
    codigo_documento = fields.Char('Codigo documento')
    codigo_pais = fields.Char('Codigo pais')
    codigo_nacimiento = fields.Char('Codigo nacimiento')
    cantidad_hijos = fields.Float('Cantidad hijos')
    trabajo_extranjero = fields.Char('Trabajo extranjero')
    forma = fields.Char('Forma')
    pais_trabajo = fields.Char('Pais trabajo')
    motivo_retiro_extranjero = fields.Char('Motivo retiro extranjero')
    etnia = fields.Char('Etnia')
    idioma = fields.Char('Idioma')
    puesto_codigo = fields.Char('Puesto codigo')
    nivel_academico = fields.Selection([('0', 'No sabe Leer y/o escribir'), ('1', 'Sabe leer y/oescribir'),
        ('2','Primaria incompleta'),('3','Primaria completa '),('4','Secundaria incompleta'),('5','Secundaria completa'),
        ('6','Diversificado incompleto'),('7','Diversificado completo'),('8','Universidad incompleta'),('9','Universidad completa'),
        ('10','Postgrados'),('11','Diplomados')], 'Nivel academico')
    codigo_jornada = fields.Char('Codigo Jornada')
    temporalidad_contrato = fields.Char('Temporalidad contrato')
    tipo_contrato = fields.Char('tipo contrato')
    edad = fields.Integer(compute='_get_edad',string='Edad')
    numero_liquidacion = fields.Char('Numero liquidación')
    deposito = fields.Boolean('Deposito')
    tipo_planilla_id = fields.Many2one('res.company.tipo_planilla','Tipo planilla')
    nacionalidad  = fields.Char('Nacionalidad')
    tipo_discapacidad  = fields.Char('Tipo discapacidad')
    permit_no  = fields.Char('Permitir')
    titulo_obtenido  = fields.Char('Titulo obtenido')
    pueblo_pertenencia  = fields.Char('Pueblo pertenecia')
    lugar_nacimiento = fields.Char('Lugar de nacimiento')

    def _get_edad(self):
        for employee in self:
            if employee.birthday:
                dia_nacimiento = int(datetime.datetime.strptime(str(employee.birthday),'%Y-%m-%d').date().strftime('%d'))
                mes_nacimiento = int(datetime.datetime.strptime(str(employee.birthday),'%Y-%m-%d').date().strftime('%m'))
                anio_nacimiento = int(datetime.datetime.strptime(str(employee.birthday),'%Y-%m-%d').date().strftime('%Y'))
                dia_actual = int(datetime.date.today().strftime('%d'))
                mes_actual = int(datetime.date.today().strftime('%m'))
                anio_actual = int(datetime.date.today().strftime('%Y'))

                resta_dia = dia_actual - dia_nacimiento
                resta_mes = mes_actual - mes_nacimiento
                resta_anio = anio_actual - anio_nacimiento

                if (resta_mes < 0):
                    resta_anio = resta_anio - 1
                elif (resta_mes == 0):
                    if (resta_dia < 0):
                        resta_anio = resta_anio - 1
                    if (resta_dia > 0):
                        resta_anio = resta_anio
                employee.edad = resta_anio

class hr_prestamo(models.Model):
    _name = 'hr.prestamo'

    name = fields.Char('Prestamo')
    empleado_id = fields.Many2one('hr.employee','Empleado')
    fecha_inicio = fields.Date('Fecha inicio')
    numero_pagos = fields.Integer('Numero de pagos')
    codigo = fields.Char(string='Código',required=True)
    valor_prestamo = fields.Float('Valor de prestamo')
    estado = fields.Selection([
        ('nuevo', 'Nuevo'),
        ('proceso','Proceso'),
        ('pagado', 'Pagado')
    ], string='Estado', help='Estado del prestamo',readonly=True, default='nuevo')
    prestamo_ids = fields.One2many('hr.prestamo.linea','prestamo_id',string='Lineas')
    company_id = fields.Many2one('res.company',string='Compañia',required=True, readonly=True, default=lambda self: self.env.user.company_id)
    referencia = fields.Char('Referencia')
    fin_mes = fields.Boolean('Fin de mes')

    def generar_datos_prestamo(self):
        prestamo_igual = self.env['hr.prestamo'].search([('referencia','=',self.referencia),('id','!=', self.id),('empleado_id','=', self.empleado_id.id)])
        if len(prestamo_igual) == 0:
            if self.estado == 'nuevo':
                self.prestamo_ids.unlink()
                if self.valor_prestamo > 0 and self.numero_pagos > 0 and self.fecha_inicio:
                    mensualidad = self.valor_prestamo / self.numero_pagos
                    mes_inicio = datetime.datetime.strptime(str(self.fecha_inicio), '%Y-%m-%d').date()
                    mes = 0
                    contador = 0
                    while contador < self.numero_pagos:
                        mes = mes_inicio + relativedelta(months=+contador)
                        logging.warn(mes)
                        anio = mes.strftime('%Y')
                        mes = str(int(mes.strftime('%m')))
                        self.env['hr.prestamo.linea'].create({'prestamo_id': self.id,'mes': mes,'anio': anio,'valor': mensualidad})
                        contador += 1
        return True

    def unlink(self):
        for prestamo in self:
            if not prestamo.estado == 'nuevo':
                raise UserError(_('No puede eliminar prestamo, por que ya existen nominas asociadas'))
        return super(hr_prestamo, self).unlink()

class hr_prestamo_linea(models.Model):
    _name = 'hr.prestamo.linea'

    prestamo_id = fields.Many2one('hr.prestamo','Prestamo')
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
    valor = fields.Float('valor')
    anio = fields.Integer('Año')
    nomina_ids = fields.Many2many('hr.payslip','prestamo_nominas_id_rel',string='Nomina')

class hr_comision(models.Model):
    _name = 'hr.comision'

    name = fields.Char('Comisión')
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
    total = fields.Float('Comision')
    codigo = fields.Char('Código')
    fin_mes = fields.Boolean('Fin de mes')
    anio = fields.Integer('Año')
    company_id = fields.Many2one('res.company',string='Compañia',required=True, readonly=True, default=lambda self: self.env.user.company_id)

class hr_historial_salario(models.Model):
    _name = "hr.historial_salario"

    fecha = fields.Date('Fecha')
    salario = fields.Float('Salario')
    nomina_id = fields.Many2one('hr.payslip','Nomina')
    contrato_id = fields.Many2one('hr.contract','Contato')
