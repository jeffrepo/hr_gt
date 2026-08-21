# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
import datetime
import time
import dateutil.parser
from odoo.fields import Date, Datetime
import calendar
from collections import defaultdict
from odoo.fields import Domain


# class HrPayslipEmployees(models.TransientModel):
#     _inherit = 'hr.payslip.employees'

#     def _get_employees(self):
#         res = super(HrPayslipEmployees, self)._get_employees()
#         return False

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    fin_mes = fields.Boolean('Fin de mes')
    dias_nomina = fields.Integer('Días de nomina')
    dia_mes = fields.Integer('Dias del mes')

    def _get_otra_entrada_periodo_gt(self):
        """
        Devuelve mes y año tomando como base la fecha final de la nómina.
        """
        self.ensure_one()

        fecha_base = self.date_to or self.date_from or fields.Date.context_today(self)

        return str(fecha_base.month), fecha_base.year

    def _sync_otras_entradas_gt_to_inputs(self):
        """
        Llena las entradas salariales del payslip usando el modelo hr_gt.otra_entrada.

        Relación:
            hr_gt.otra_entrada.codigo = hr.payslip.input.input_type_id.code
            hr_gt.otra_entrada.monto  = hr.payslip.input.amount
        """
        OtraEntrada = self.env['hr_gt.otra_entrada']

        for payslip in self:
            if not payslip.employee_id:
                continue

            mes, anio = payslip._get_otra_entrada_periodo_gt()

            otras_entradas = OtraEntrada.search([
                ('empleado_id', '=', payslip.employee_id.id),
                ('mes', '=', mes),
                ('anio', '=', anio),
                ('company_id', '=', payslip.company_id.id),
            ])

            if not otras_entradas:
                continue

            # Agrupamos por código por si hay más de una entrada con el mismo código
            montos_por_codigo = {}

            for entrada in otras_entradas:
                if not entrada.codigo:
                    continue

                codigo = entrada.codigo.strip()

                if codigo not in montos_por_codigo:
                    montos_por_codigo[codigo] = 0.0

                monto = entrada.monto or 0.0

                # Si quieres que los descuentos se guarden negativos, deja esto activo.
                # Si prefieres manejarlos positivos y restarlos desde la regla salarial,
                # comenta este bloque.
                montos_por_codigo[codigo] += monto

            for codigo, monto in montos_por_codigo.items():
                input_line = payslip.input_line_ids.filtered(
                    lambda line: line.input_type_id and line.input_type_id.code == codigo
                )

                if input_line:
                    input_line.write({
                        'amount': monto,
                    })
                else:
                    input_type = self.env['hr.payslip.input.type'].search([
                        ('code', '=', codigo),
                    ], limit=1)

                    if input_type:
                        self.env['hr.payslip.input'].create({
                            'payslip_id': payslip.id,
                            'input_type_id': input_type.id,
                            'name': input_type.name,
                            'amount': monto,
                        })

        return True
    
    def existe_entrada(self,entrada_ids,entrada_id):
        existe_entrada = False
        for entrada in entrada_ids:
            if entrada.input_type_id.id == entrada_id.id:
                existe_entrada = True
        return existe_entrada

    @api.depends('employee_id', 'version_id', 'struct_id', 'date_from', 'date_to', 'struct_id')
    def _compute_input_line_ids(self):
        res = super(HrPayslip, self)._compute_input_line_ids()
        for slip in self:
            if slip.employee_id and slip.struct_id and slip.struct_id.input_line_type_ids:
                mes_nomina = slip.date_from.month
                anio_nomina = slip.date_from.year
                dia_nomina = slip.date_to.day
                descuentos = {}
                bonificaciones = {}
                descuento_ids = self.env["hr_gt.otra_entrada"].search([("tipo",'=','descuento'),("mes",'=',mes_nomina), ("anio","=",anio_nomina), ("empleado_id","=", slip.employee_id.id)])
                bonificacion_ids = self.env["hr_gt.otra_entrada"].search([("tipo",'=','bonificacion'), ("anio","=",anio_nomina),("mes",'=',mes_nomina) ,("empleado_id","=", slip.employee_id.id)])

                logging.warning(descuento_ids)
                logging.warning(bonificacion_ids)

                if descuento_ids:
                    for descuento in descuento_ids:
                        if descuento.codigo not in descuentos:
                            descuentos[descuento.codigo] = 0
                        descuentos[descuento.codigo] += descuento.monto

                if bonificacion_ids:
                    for bonifcacion in bonificacion_ids:
                        if bonifcacion.codigo not in bonificaciones:
                            bonificaciones[bonifcacion.codigo] = 0
                        bonificaciones[bonifcacion.codigo] += bonifcacion.monto

                input_line_vals = []
                if slip.input_line_ids:
                    slip.input_line_ids.unlink()

                for line in slip.struct_id.input_line_type_ids:
                    monto = 0
                    if line.code in bonificaciones:
                        monto = bonificaciones[line.code]

                    if line.code in descuentos:
                        monto = descuentos[line.code]

                    input_line_vals.append((0,0,{
                        'name': line.name,
                        'amount': monto,
                        'input_type_id': line.id,
                    }))
                slip.update({'input_line_ids': input_line_vals})
        return res

    def compute_sheet(self):
        self._sync_otras_entradas_gt_to_inputs()
        for nomina in self:
            reference_calendar = nomina._get_out_of_contract_calendar()
            dias_de_quincena = reference_calendar.get_work_duration_data(Datetime.from_string(nomina.date_from), Datetime.from_string(nomina.date_to), compute_leaves=False,domain = False)
            nomina.dias_nomina = dias_de_quincena['days']
            logging.warning(nomina.date_to.year)
            numero_dias = calendar.monthrange(nomina.date_to.year, nomina.date_to.month)
            logging.warning(numero_dias)
            nomina.dia_mes = numero_dias[1]
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

    # def _get_worked_day_lines(self):
    #     res = super(HrPayslip, self)._get_worked_day_lines()
    #     tipos_ausencias_ids = self.env['hr.leave.type'].search([])
    #     datos = self.horas_sumar(res)
    #     ausencias_restar = []

    #     dias_ausentados_restar = 0
    #     contracts = False
    #     if self.employee_id.contract_id:
    #         contracts = self.employee_id.contract_id

    #     for ausencia in tipos_ausencias_ids:
    #         if ausencia.work_entry_type_id and ausencia.work_entry_type_id.descontar_nomina:
    #             logging.warn(ausencia.work_entry_type_id.code)
    #             ausencias_restar.append(ausencia.work_entry_type_id.id)

    #     trabajo_id = self.env['hr.work.entry.type'].search([('code','=','DIAS')])
    #     logging.warn('TRABAJO ID')
    #     logging.warn(trabajo_id)
    #     for r in res:
    #         tipo_id = self.env['hr.work.entry.type'].search([('id','=',r['work_entry_type_id'])])
    #         if tipo_id and tipo_id.is_leave == False:
    #             r['number_of_hours'] += datos['horas']
    #             r['number_of_days'] += datos['dias']

    #         if len(ausencias_restar)>0:
    #             if r['work_entry_type_id'] in ausencias_restar:
    #                 dias_ausentados_restar += r['number_of_days']
    #     if contracts:
    #         if contracts.date_start and self.date_from <= contracts.date_start <= self.date_to:
    #             dias_laborados = self.employee_id._get_work_days_data(Datetime.from_string(contracts.date_start), Datetime.from_string(self.date_to), calendar=contracts.resource_calendar_id)
    #             dia_inicio_contrato = int(contracts.date_start.strftime('%d'))
    #             res.append({'work_entry_type_id': trabajo_id.id, 'sequence': 10, 'number_of_days': (dias_laborados['days']+1 - dias_ausentados_restar) if (dias_laborados['days'] - dias_ausentados_restar) <= 30 else 30})
    #         elif contracts.date_end and self.date_from <= contracts.date_end <= self.date_to:
    #             dias_laborados = self.employee_id._get_work_days_data(Datetime.from_string(self.date_from), Datetime.from_string(contracts.date_end), calendar=contracts.resource_calendar_id)
    #             dias_trabajo = int(contracts.date_end.strftime('%d'))
    #             res.append({'work_entry_type_id': trabajo_id.id, 'sequence': 10, 'number_of_days': (dias_laborados['days'] + 1 - dias_ausentados_restar) if (dias_laborados['days'] + 1 - dias_ausentados_restar) <= 30 else 30})
    #         else:
    #             if contracts.structure_type_id.default_schedule_pay == 'monthly':
    #                 res.append({'work_entry_type_id': trabajo_id.id,'sequence': 10,'number_of_days': 30 - dias_ausentados_restar})
    #             if contracts.structure_type_id.default_schedule_pay == 'bi-monthly':
    #                 dias_de_quincena = self.employee_id._get_work_days_data(Datetime.from_string(self.date_from), Datetime.from_string(self.date_to), calendar=self.employee_id.resource_calendar_id)
    #                 dias_de_quincena = dias_de_quincena['days'] + 1
    #                 res.append({'work_entry_type_id': trabajo_id.id,'sequence': 10,'number_of_days': dias_de_quincena - dias_ausentados_restar})
    #             # Cálculo de días para catorcena
    #             if contracts.structure_type_id.default_schedule_pay == 'bi-weekly':
    #                 dias_laborados = self.employee_id._get_work_days_data(Datetime.from_string(nomina.date_from), Datetime.from_string(nomina.date_to), calendar=contracts.resource_calendar_id)
    #                 res.append({'work_entry_type_id': trabajo_id.id,'sequence': 10,'number_of_days': (dias_laborados['days']+1 - dias_ausentados_restar)})

    #     logging.warn(res)
    #     return res


    def _obtener_info_nomina_anterior(self,empleado_id,fecha_inicio):
        salario = 0
        anio_nomina_busqueda = int(datetime.datetime.strptime(str(fecha_inicio), '%Y-%m-%d').date().strftime('%Y'))
        mes_nomina_busqueda = int(datetime.datetime.strptime(str(fecha_inicio), '%Y-%m-%d').date().strftime('%m'))
        fecha_inicial_busqueda = '01/'+str(mes_nomina_busqueda)+'/'+str(anio_nomina_busqueda)
        nomina_ids = self.env['hr.payslip'].search([('employee_id', '=',  empleado_id.id),('date_to','<', fecha_inicio),('fin_mes','=',False),('date_from','>=',fecha_inicial_busqueda)])
        logging.warning('_obtener_info_nomina_anterior')
        logging.warning(nomina_ids)
        if nomina_ids:
            for nomina in nomina_ids:
                for linea in nomina.line_ids:
                    if linea.code == 'NET':
                        salario = linea.total
        return salario

class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    porcentaje_prestamo = fields.Float('Prestamo (%)')
    bono = fields.Boolean("Bono")
    aguinaldo = fields.Boolean("Aguinaldo")

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

class HrPayslipRun(models.Model):
    _inherit = "hr.payslip.run"

    def _get_valid_version_ids(
        self,
        date_start=None,
        date_end=None,
        structure_id=None,
        company_id=None,
        employee_ids=None,
        schedule_pay=None,
    ):
        date_start = fields.Date.to_date(date_start or self.date_start)
        date_end = fields.Date.to_date(date_end or self.date_end)

        structure = (
            self.env["hr.payroll.structure"].browse(structure_id)
            if structure_id
            else self.structure_id
        )
        schedule_pay = schedule_pay or self.schedule_pay
        company_id = company_id or self.company_id.id

        is_second_fortnight = (
            date_start
            and date_end
            and date_start.day >= 16
            and date_start.year == date_end.year
            and date_start.month == date_end.month
        )

        contract_search_start = (
            date_start.replace(day=1)
            if is_second_fortnight
            else date_start
        )

        version_domain = Domain([
            ("company_id", "=", company_id),
            ("employee_id", "!=", False),
            ("contract_date_start", "<=", date_end),
            "|",
                ("contract_date_end", "=", False),
                ("contract_date_end", ">=", contract_search_start),
            ("date_version", "<=", date_end),
            ("structure_type_id", "!=", False),
        ])

        # En la segunda quincena también se incluyen empleados archivados
        # que finalizaron contrato durante la primera quincena.
        if not is_second_fortnight:
            version_domain &= Domain([
                ("active_employee", "=", True),
            ])

        if structure:
            version_domain &= Domain([
                ("structure_type_id", "=", structure.type_id.id),
            ])

        if employee_ids:
            version_domain &= Domain([
                ("employee_id", "in", employee_ids),
            ])

        if schedule_pay:
            version_domain &= Domain([
                ("schedule_pay", "=", schedule_pay),
            ])

        all_versions = self.env["hr.version"]._read_group(
            domain=version_domain,
            groupby=["employee_id", "date_version:day"],
            order="date_version:day DESC",
            aggregates=["id:recordset"],
        )

        versions_by_employee = defaultdict(list)

        for employee, _, versions in all_versions:
            versions_by_employee[employee] += [*versions]

        valid_versions = self.env["hr.version"]

        for employee_versions in versions_by_employee.values():
            employee_valid_versions = self.env["hr.version"]

            for index, version in enumerate(employee_versions):
                if (
                    version.date_version <= date_start
                    or employee_versions[-1] == version
                ):
                    employee_valid_versions |= version
                    break

                if employee_valid_versions:
                    if (
                        employee_valid_versions[-1].contract_date_start
                        > version.contract_date_start
                        and (
                            version.contract_date_start
                            >= version.date_version
                            or version.contract_date_start
                            > employee_versions[index + 1].contract_date_start
                        )
                    ):
                        employee_valid_versions |= version

                elif (
                    version.contract_date_start >= version.date_version
                    or version.contract_date_start
                    > employee_versions[index + 1].contract_date_start
                ):
                    employee_valid_versions |= version

            valid_versions |= employee_valid_versions

        return valid_versions.ids
