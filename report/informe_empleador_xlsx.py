# -*- coding: utf-8 -*-
from odoo import models, fields
from datetime import date, datetime

class InformeEmpleadorXlsx(models.AbstractModel):
    _name = "report.hr_gt.informe_empleador_xlsx"
    _description = "Informe Empleador (GT) XLSX"

    # 🔧 Mapeo por CÓDIGOS de reglas salariales (ajusta a tus codes)
    RULE_CODES = {
        "SALARIO_BASE": {"codes": ["BASIC"], "sum": "total"},
        "BONIF_250": {"codes": ["BON250"], "sum": "total"},
        "AGUINALDO": {"codes": ["AGUI"], "sum": "total"},
        "BONO14": {"codes": ["BONO14"], "sum": "total"},
        "COMISIONES": {"codes": ["COMM"], "sum": "total"},
        "VIATICOS": {"codes": ["VIAT"], "sum": "total"},
        "BONIF_ADIC": {"codes": ["BONADIC"], "sum": "total"},
        "VACACIONES": {"codes": ["VAC"], "sum": "total"},
        "INDEMNIZACION": {"codes": ["IND"], "sum": "total"},
        "HORAS_EXTRAS_MONTO": {"codes": ["OT"], "sum": "total"},
        # Horas extra: normalmente no es salary rule; se obtiene de worked days (ver abajo)
    }

    # 🔧 Codes de worked days para horas extra (ajusta a tu nómina)
    WORKED_DAY_OT_CODES = ["OT", "HE", "HHE", "HORASEXTRA"]

    def _year_range(self, year: int):
        dfrom = date(year, 1, 1)
        dto = date(year, 12, 31)
        return dfrom, dto

    def _get_payslip_domain(self, date_from, date_to, payslip_states):
        states = []
        if payslip_states == "done":
            states = ["done"]
        elif payslip_states == "paid":
            states = ["paid"]
        else:
            states = ["done", "paid"]

        # Nota: dependiendo tu operación, puede convenir usar date_to o date_from.
        return [
            ("state", "in", states),
            ("date_from", ">=", date_from),
            ("date_to", "<=", date_to),
        ]

    def _get_contract_domain(self):
        return [("state", "in", ["open", "close", "cancel"])]

    def _contracts_in_year(self, contracts, date_from, date_to):
        """Contratos que se cruzan con el año."""
        res = self.env["hr.contract"]
        for c in contracts:
            c_start = c.date_start or date.min
            c_end = c.date_end or date.max
            if c_start <= date_to and c_end >= date_from:
                res |= c
        return res

    def _sum_rules(self, slip, codes):
        total = 0.0
        for line in slip.line_ids:
            if line.code in codes:
                total += line.total or 0.0
        return total

    def _sum_overtime_hours(self, slip):
        hours = 0.0
        for wd in slip.worked_days_line_ids:
            if (wd.code or "").strip() in self.WORKED_DAY_OT_CODES:
                # worked_days_line: number_of_hours es lo normal
                hours += (wd.number_of_hours or 0.0)
        return hours

    def _compute_employee_year_data(self, employees, date_from, date_to, payslip_states):
        Payslip = self.env["hr.payslip"]
        Contract = self.env["hr.contract"]

        contracts_all = Contract.search(self._get_contract_domain())
        contracts_year = self._contracts_in_year(contracts_all, date_from, date_to)

        # Empleados elegibles: con contrato válido (open/close/cancel) cruzando año
        eligible_emps = contracts_year.mapped("employee_id")
        if employees:
            eligible_emps = eligible_emps & employees

        slips = Payslip.search(self._get_payslip_domain(date_from, date_to, payslip_states) + [
            ("employee_id", "in", eligible_emps.ids)
        ])

        # Agrupar por empleado
        agg = {}
        for emp in eligible_emps:
            agg[emp.id] = {
                "employee": emp,
                "slips": self.env["hr.payslip"],
                "ot_hours": 0.0,
                "rules": {k: 0.0 for k in self.RULE_CODES.keys()},
            }

        for slip in slips:
            bucket = agg.get(slip.employee_id.id)
            if not bucket:
                continue
            bucket["slips"] |= slip
            bucket["ot_hours"] += self._sum_overtime_hours(slip)
            for key, conf in self.RULE_CODES.items():
                bucket["rules"][key] += self._sum_rules(slip, conf["codes"])

        return agg, contracts_year

    def generate_xlsx_report(self, workbook, data, wizard):
        # Wizard llega como recordset del modelo hr.gt.informe.empleador.wizard
        year = int((data or {}).get("year") or wizard.year)
        payslip_states = (data or {}).get("payslip_states") or wizard.payslip_states

        date_from, date_to = self._year_range(year)

        # Si quisieras permitir filtrar por empleados seleccionados desde contexto:
        employees = self.env["hr.employee"]
        ctx_emp_ids = self.env.context.get("active_ids") if self.env.context.get("active_model") == "hr.employee" else []
        if ctx_emp_ids:
            employees = self.env["hr.employee"].browse(ctx_emp_ids)

        agg, contracts_year = self._compute_employee_year_data(employees, date_from, date_to, payslip_states)

        # ====== AQUI: Generación de la hoja "Empleados" igual al template ======
        sheet = workbook.add_worksheet("Empleados")

        headers = [
            "Número de empleado ","Primer nombre","Segundo nombre","Tercer nombre","Primer apellido","Segundo apellido",
            "Apellido de casada","Nacionalidad","Tipo de discapacidad","Estado civil",
            "Documento identificación (DPI, Pasaporte u otro)","Número de documento","País de origen",
            "Número de expediente del permiso de extranjero","Lugar de nacimiento (municipio)",
            "Número de Identificación Tributaria (NIT)","Número de afiliación\n\u00A0IGSS","Sexo","Fecha de nacimiento",
            "Nivel académico más alto alcanzado","Titulo o diploma (profesión)","\u00A0 Pueblo de pertenencia",
            "Comunidad Lingüística","Cantidad de hijos","Temporalidad del contrato","Tipo de contrato",
            "Fecha de inicio de labores","Fecha  de reinicio de labores","Fecha de finalización de labores",
            "Ocupación (puesto)","Jornada de trabajo","Días laborados en el año","Salario mensual nominal",
            "Salario anual nominal","Bonificación Decreto    \n78-89  (Q.250.00)","Total horas extras anuales",
            "Valor de la hora extra ","Monto Aguinaldo Decreto    \n76-78","Monto Bono 14  Decreto  \n42-92",
            "Retribución por comisiones","Viáticos","Bonificaciones adicionales","Retribución por vacaciones",
            "Retribución por indemnización (Artículo 82 Código de Trabajo)","Sucursal",
        ]

        widths = [
            18.7109375,11.5703125,13.0,13.0,13.0,13.0,13.0,17.85546875,20.5703125,12.42578125,
            25.85546875,17.5703125,13.7109375,16.28515625,18.28515625,23.140625,14.0,11.5703125,13.42578125,17.28515625,
            19.0,13.7109375,14.42578125,13.0,14.0,11.5703125,11.42578125,13.0,13.0,38.28515625,
            16.28515625,12.85546875,12.140625,12.140625,13.7109375,14.140625,15.28515625,14.5703125,15.7103125,13.5703125,
            14.5703125,14.42578125,13.5703125,16.28515625,21.42578125
        ]
        for col, w in enumerate(widths):
            sheet.set_column(col, col, w)

        header_fmt = workbook.add_format({
            "bold": True, "font_name": "Arial", "font_size": 10,
            "align": "center", "valign": "vcenter", "text_wrap": True,
            "border": 2, "bg_color": "#D9D9D9",
        })
        date_fmt = workbook.add_format({"num_format": "yyyy-mm-dd"})
        money_fmt = workbook.add_format({"num_format": "#,##0.00"})
        int_fmt = workbook.add_format({"num_format": "0"})

        sheet.set_row(0, 78.75)
        for col, h in enumerate(headers):
            sheet.write(0, col, h, header_fmt)

        # Para datos de contrato, toma “el más relevante” del año (ej: último que cruza el año)
        Contract = self.env["hr.contract"]
        row = 1
        for emp_id, info in agg.items():
            emp = info["employee"]

            # contrato “principal” en el año (último por date_start)
            emp_contracts = contracts_year.filtered(lambda c: c.employee_id.id == emp.id).sorted(
                key=lambda c: c.date_start or date.min
            )
            contract = emp_contracts[-1] if emp_contracts else False

            # salario mensual nominal: si tu nómina paga quincenal/semanal, esto debe ajustarse.
            wage_month = contract.wage if contract and contract.wage else 0.0
            wage_year = info["rules"]["SALARIO_BASE"]  # mejor que wage*12 si hubo cambios

            # valor hora extra: si lo tienes como regla salarial separada, úsalo; si no, calcula:
            # ejemplo simple: hourly = wage_month / 30 / 8
            hour_extra = 0.0
            if info["ot_hours"]:
                ot_amount = info["rules"]["HORAS_EXTRAS_MONTO"]
                hour_extra = (ot_amount / info["ot_hours"]) if info["ot_hours"] else 0.0

            # Días laborados: ideal desde worked_days del año; aquí aproximación sumando days de slips
            days_worked = 0
            for slip in info["slips"]:
                for wd in slip.worked_days_line_ids:
                    # Ajusta según tus worked day codes (WORK100, etc.)
                    days_worked += int(wd.number_of_days or 0)

            # Sucursal
            sucursal = (getattr(emp, "x_sucursal_id", False) and emp.x_sucursal_id.name) or (emp.company_id.name if emp.company_id else "")

            # Fechas del contrato
            start_date = contract.date_start if contract else False
            end_date = contract.date_end if contract else False

            values = ["" for _ in range(45)]
            values[0] = emp.barcode or emp.identification_id or str(emp.id)

            # Nombres/apellidos: usa tus campos reales (cambia x_* por los tuyos)
            values[1] = getattr(emp, "x_primer_nombre", "") or ""
            values[2] = getattr(emp, "x_segundo_nombre", "") or ""
            values[3] = getattr(emp, "x_tercer_nombre", "") or ""
            values[4] = getattr(emp, "x_primer_apellido", "") or ""
            values[5] = getattr(emp, "x_segundo_apellido", "") or ""
            values[6] = getattr(emp, "x_apellido_casada", "") or ""

            values[7] = emp.country_id.name if emp.country_id else ""
            values[8] = getattr(emp, "x_tipo_discapacidad", "") or ""
            values[9] = getattr(emp, "x_estado_civil", "") or ""
            values[10] = getattr(emp, "x_tipo_documento", "") or ""
            values[11] = emp.identification_id or ""
            values[12] = getattr(emp, "x_pais_origen", "") or ""
            values[13] = getattr(emp, "x_expediente_permiso_extranjero", "") or ""
            values[14] = getattr(emp, "x_municipio_nacimiento", "") or ""
            values[15] = getattr(emp, "x_nit", "") or ""
            values[16] = getattr(emp, "x_igss", "") or ""
            values[17] = getattr(emp, "x_sexo", "") or ""
            values[18] = emp.birthday or ""

            values[19] = getattr(emp, "x_nivel_educativo", "") or ""
            values[20] = getattr(emp, "x_titulo_diploma", "") or ""
            values[21] = getattr(emp, "x_pueblo_pertenencia", "") or ""
            values[22] = getattr(emp, "x_comunidad_linguistica", "") or ""
            values[23] = getattr(emp, "x_cantidad_hijos", 0) or 0
            values[24] = getattr(contract, "x_temporalidad_contrato", "") if contract else ""
            values[25] = getattr(contract, "x_tipo_contrato", "") if contract else ""
            values[26] = start_date or ""
            values[27] = getattr(contract, "x_fecha_reinicio", "") if contract else ""
            values[28] = end_date or ""
            values[29] = emp.job_id.name if emp.job_id else ""
            values[30] = getattr(contract, "x_jornada_trabajo", "") if contract else ""

            values[31] = days_worked
            values[32] = wage_month
            values[33] = wage_year
            values[34] = info["rules"]["BONIF_250"]
            values[35] = info["ot_hours"]
            values[36] = hour_extra
            values[37] = info["rules"]["AGUINALDO"]
            values[38] = info["rules"]["BONO14"]
            values[39] = info["rules"]["COMISIONES"]
            values[40] = info["rules"]["VIATICOS"]
            values[41] = info["rules"]["BONIF_ADIC"]
            values[42] = info["rules"]["VACACIONES"]
            values[43] = info["rules"]["INDEMNIZACION"]
            values[44] = sucursal

            for col, val in enumerate(values):
                if col in (18, 26, 28) and val:
                    sheet.write_datetime(row, col, val, date_fmt)
                elif col in (31, 23) and isinstance(val, (int, float)):
                    sheet.write_number(row, col, int(val), int_fmt)
                elif col in (32,33,34,35,36,37,38,39,40,41,42,43) and isinstance(val, (int, float)):
                    sheet.write_number(row, col, float(val), money_fmt)
                else:
                    sheet.write(row, col, val)
            row += 1
