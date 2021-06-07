# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.release import version_info
import logging
import datetime
import time
import dateutil.parser
from dateutil.relativedelta import relativedelta
from dateutil import relativedelta as rdelta
from odoo.fields import Date, Datetime

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    fin_mes = fields.Boolean('Fin de mes')

    def existe_entrada(self,entrada_ids,entrada_id):
        existe_entrada = False
        for entrada in entrada_ids:
            if entrada.input_type_id.id == entrada_id.id:
                existe_entrada = True
        return existe_entrada

    def compute_sheet(self):
        for nomina in self:
            mes_nomina = int(nomina.date_from.strftime('%m'))
            dia_nomina = int(nomina.date_to.strftime('%d'))
            anio_nomina = int(nomina.date_from.strftime('%Y'))
            valor_pago = 0
            porcentaje_pagar = 0
            if int(dia_nomina) > 15:
                nomina.fin_mes = True
            for entrada in nomina.input_line_ids:
                comisiones = self.env['hr.comision'].search([['empleado_id', '=', nomina.employee_id.id]])
                if comisiones:
                    for comision in comisiones:
                        if nomina.fin_mes == True and comision.fin_mes == True and int(omision.mes) ==  int(mes_nomina) and int(comision.anio) == int(anio_nomina) and str(entrada.input_type_id.code) == str(comision.codigo):
                            entrada.amount += comision.total
                        elif nomina.fin_mes == False and comision.fin_mes == False and int(comision.mes) == int(mes_nomina) and int(comision.anio) == int(anio_nomina) and str(entrada.input_type_id.code) == str(comision.codigo):
                            logging.warn('prueba')
                            entrada.amount += comision.total

                prestamos = self.env['hr.prestamo'].search([['empleado_id', '=', nomina.employee_id.id]])
                if prestamos:
                    for prestamo in prestamos:
                        anio_prestamo = int(prestamo.fecha_inicio.strftime('%Y'))
                        if (prestamo.codigo == entrada.input_type_id.code) and (nomina.fin_mes == True and prestamo.fin_mes == True) and ((prestamo.estado == 'nuevo') or (prestamo.estado == 'proceso')):
                            nominas = []
                            for lineas in prestamo.prestamo_ids:
                                if int(lineas.mes) == int(mes_nomina) and int(lineas.anio) == int(anio_nomina):
                                    nominas.append(nomina.id)
                                    lineas.nomina_ids = [(6, 0, nominas)]
                                    entrada.amount += lineas.valor
                        elif (prestamo.codigo == entrada.input_type_id.code) and (nomina.fin_mes == False and prestamo.fin_mes == False) and ((prestamo.estado == 'nuevo') or (prestamo.estado == 'proceso')):
                            nominas = []
                            for lineas in prestamo.prestamo_ids:
                                if int(lineas.mes) == int(mes_nomina) and int(lineas.anio) == int(anio_nomina):
                                    nominas.append(nomina.id)
                                    lineas.nomina_ids = [(6, 0, nominas)]
                                    entrada.amount += lineas.valor

        res =  super(HrPayslip, self).compute_sheet()
        return res

    def _obtener_entrada(self,contrato_id):
        entradas = False
        if contrato_id.structure_type_id and contrato_id.structure_type_id.default_struct_id:
            if contrato_id.structure_type_id.default_struct_id.input_line_type_ids:
                entradas = [entrada for entrada in contrato_id.structure_type_id.default_struct_id.input_line_type_ids]
        return entradas

    def horas_sumar(self,lineas):
        horas = 0
        dias = 0
        for linea in lineas:
            tipo_id = self.env['hr.work.entry.type'].search([('id','=',linea['work_entry_type_id'])])
            if tipo_id and tipo_id.is_leave and tipo_id.descontar_nomina == False:
                horas += linea['number_of_hours']
                dias += linea['number_of_days']
        return {'dias':dias, 'horas': horas}

    def _get_worked_day_lines(self):
        res = super(HrPayslip, self)._get_worked_day_lines()
        tipos_ausencias_ids = self.env['hr.leave.type'].search([])
        datos = self.horas_sumar(res)
        ausencias_restar = []

        dias_ausentados_restar = 0
        contracts = False
        if self.employee_id.contract_id:
            contracts = self.employee_id.contract_id

        for ausencia in tipos_ausencias_ids:
            if ausencia.work_entry_type_id and ausencia.work_entry_type_id.descontar_nomina:
                logging.warn(ausencia.work_entry_type_id.code)
                ausencias_restar.append(ausencia.work_entry_type_id.id)

        trabajo_id = self.env['hr.work.entry.type'].search([('code','=','DIAS')])
        for r in res:
            tipo_id = self.env['hr.work.entry.type'].search([('id','=',r['work_entry_type_id'])])
            if tipo_id and tipo_id.is_leave == False:
                r['number_of_hours'] += datos['horas']
                r['number_of_days'] += datos['dias']

            if len(ausencias_restar)>0:
                if r['work_entry_type_id'] in ausencias_restar:
                    dias_ausentados_restar += r['number_of_days']

        if contracts:
            if contracts.date_start and self.date_from <= contracts.date_start <= self.date_to:
                dias_laborados = self.employee_id._get_work_days_data(Datetime.from_string(contracts.date_start), Datetime.from_string(self.date_to), calendar=contracts.resource_calendar_id)
                dia_inicio_contrato = int(contracts.date_start.strftime('%d'))
                res.append({'work_entry_type_id': trabajo_id.id, 'sequence': 10, 'number_of_days': (dias_laborados['days']+1 - dias_ausentados_restar) if (dias_laborados['days'] - dias_ausentados_restar) <= 30 else 30})
            elif contracts.date_end and self.date_from <= contracts.date_end <= self.date_to:
                dias_laborados = self.employee_id._get_work_days_data(Datetime.from_string(self.date_from), Datetime.from_string(contracts.date_end), calendar=contracts.resource_calendar_id)
                dias_trabajo = int(contracts.date_end.strftime('%d'))
                res.append({'work_entry_type_id': trabajo_id.id, 'sequence': 10, 'number_of_days': (dias_laborados['days'] + 1 - dias_ausentados_restar) if (dias_laborados['days'] + 1 - dias_ausentados_restar) <= 30 else 30})
            else:
                if contracts.structure_type_id.default_schedule_pay == 'monthly':
                    res.append({'work_entry_type_id': trabajo_id.id,'sequence': 10,'number_of_days': 30 - dias_ausentados_restar})
                if contracts.structure_type_id.default_schedule_pay == 'bi-monthly':
                    res.append({'work_entry_type_id': trabajo_id.id,'sequence': 10,'number_of_days': 15 - dias_ausentados_restar})
                # Cálculo de días para catorcena
                if contracts.structure_type_id.default_schedule_pay == 'bi-weekly':
                    dias_laborados = self.employee_id._get_work_days_data(Datetime.from_string(self.date_from), Datetime.from_string(self.date_to), calendar=contracts.resource_calendar_id)
                    res.append({'work_entry_type_id': trabajo_id.id,'sequence': 10,'number_of_days': (dias_laborados['days']+1 - dias_ausentados_restar)})

        logging.warn(res)
        return res

    @api.onchange('employee_id','struct_id','contract_id', 'date_from', 'date_to')
    def _onchange_employee(self):
        logging.warn('ONCHANGE')
        res = super(HrPayslip, self)._onchange_employee()
        mes_nomina = self.date_from.strftime('%m')
        anio_nomina = self.date_from.strftime('%Y')
        dia_nomina = self.date_to.strftime('%d')
        entradas_nomina = []
        if self.contract_id:
            if int(dia_nomina) > 15:
                self.fin_mes = True
            entradas = self._obtener_entrada(self.contract_id)
            if entradas:
                for entrada in entradas:
                    existe_entrada = False
                    if self.input_line_ids:
                        existe_entrada = self.existe_entrada(self.input_line_ids,entrada)
                        logging.warn(existe_entrada)
                    if existe_entrada == False:
                        entradas_nomina.append((0, 0, {'input_type_id':entrada.id}))
            if entradas_nomina:
                self.input_line_ids = entradas_nomina

            # prestamos = self.env['hr.prestamo'].search([['empleado_id', '=', self.employee_id.id]])
            # if prestamos:
            #     for prestamo in prestamos:
            #         for entrada in self.input_line_ids:
            #             anio_prestamo = int(prestamo.fecha_inicio.strftime('%Y'))
            #             if (prestamo.codigo == entrada.input_type_id.code) and (self.fin_mes == True and prestamo.fin_mes == True) and ((prestamo.estado == 'nuevo') or (prestamo.estado == 'proceso')):
            #                 nominas = []
            #                 for lineas in prestamo.prestamo_ids:
            #                     if int(lineas.mes) == int(mes_nomina) and int(lineas.anio) == int(anio_nomina):
            #                         nominas.append(self.id)
            #                         # lineas.nomina_ids = [(6, 0, nominas)]
            #                         entrada.amount += lineas.valor
            #             elif (prestamo.codigo == entrada.input_type_id.code) and (self.fin_mes == False and prestamo.fin_mes == False) and ((prestamo.estado == 'nuevo') or (prestamo.estado == 'proceso')):
            #                 nominas = []
            #                 for lineas in prestamo.prestamo_ids:
            #                     if int(lineas.mes) == int(mes_nomina) and int(lineas.anio) == int(anio_nomina):
            #                         nominas.append(self.id)
            #                         # lineas.nomina_ids = [(6, 0, nominas)]
            #                         entrada.amount += lineas.valor
            #
            # comisiones = self.env['hr.comision'].search([['empleado_id', '=', self.employee_id.id]])
            # if comisiones:
            #     for comision in comisiones:
            #         for entrada in self.input_line_ids:
            #             if self.fin_mes == True and comision.fin_mes == True and comision.mes ==  int(mes_nomina) and comision.anio == anio_nomina and entrada.input_type_id.code == comision.codigo:
            #                 logging.warn('if')
            #                 entrada.amount += comision.total
            #             elif self.fin_mes == False and comision.fin_mes == False and comision.mes ==  int(mes_nomina) and comision.anio == anio_nomina and entrada.input_type_id.code == comision.codigo:
            #                 logging.warn('else')
            #                 entrada.amount += comision.total
        return res

class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    porcentaje_prestamo = fields.Float('Prestamo (%)')

    def generar_pagos(self):
        pagos = self.env['account.payment'].search([('nomina_id', '!=', False)])
        nominas_pagadas = []
        for pago in pagos:
            nominas_pagadas.append(pago.nomina_id.id)
        for nomina in self.slip_ids:
            if nomina.id not in nominas_pagadas:
                total_nomina = 0
                if nomina.employee_id.diario_pago_id and nomina.employee_id.address_home_id and nomina.state == 'done':
                    res = self.env['report.rrhh.recibo'].lineas(nomina)
                    total_nomina = res['totales'][0] + res['totales'][1]
                    pago = {
                        'payment_type': 'outbound',
                        'partner_type': 'supplier',
                        'payment_method_id': 2,
                        'partner_id': nomina.employee_id.address_home_id.id,
                        'amount': total_nomina,
                        'journal_id': nomina.employee_id.diario_pago_id.id,
                        'nomina_id': nomina.id
                    }
                    pago_id = self.env['account.payment'].create(pago)
        return True
