# -*- coding: utf-8 -*-
from odoo import fields, models
from datetime import date
import io
import base64
import xlsxwriter
import logging

class HrGtInformeEmpleadorWizard(models.TransientModel):
    _name = "hr.gt.informe.empleador.wizard"
    _description = "Wizard Informe Empleador (GT)"

    year = fields.Integer(
        string="Año devengado",
        required=True,
        default=lambda self: fields.Date.today().year - 1,
    )
    file_data = fields.Binary(string="Archivo XLSX", readonly=True)
    file_name = fields.Char(string="Nombre archivo", readonly=True)

    def action_generate(self):
        self.ensure_one()

        # 1) Filtrar contratos por estado
        Contract = self.env["hr.contract"]
        contracts = Contract.search([("state", "in", ["open", "close", "cancel"])])

        # 2) Obtener payslips del año seleccionado (done/paid típico)
        date_from = date(self.year, 1, 1)
        date_to = date(self.year, 12, 31)

        Payslip = self.env["hr.payslip"]
        slips = Payslip.search([
            ("state", "in", ["done", "paid"]),
            ("date_from", ">=", date_from),
            ("date_to", "<=", date_to),
            ("employee_id", "in", contracts.mapped("employee_id").ids),
        ])

        # 3) Agrupar por empleado (aquí simplificado: tú sumarías por codes como ya platicamos)
        data_by_emp = {}
        for slip in slips:
            emp = slip.employee_id
            contrato = slip.contract_id
            data_by_emp.setdefault(emp.id, {"emp": emp, "slips": self.env["hr.payslip"], "contrato": contrato})
            data_by_emp[emp.id]["slips"] |= slip

        # 4) Generar XLSX en memoria
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        sheet = workbook.add_worksheet("Empleados")

        headers = [
            "Número de empleado ","Primer nombre","Segundo nombre","Tercer nombre","Primer apellido","Segundo apellido",
            "Apellido de casada","Nacionalidad","Tipo de discapacidad","Estado civil",
                "Documento identificación (DPI, Pasaporte u otro)","Número de documento","País de origen",
            "Número de expediente del permiso de extranjero","Lugar de nacimiento (municipio)",
            "Número de Identificación Tributaria (NIT)","Número de afiliación\n IGSS","Sexo","Fecha de nacimiento",
            "Nivel académico más alto alcanzado","Titulo o diploma (profesión)"," Pueblo de pertenencia",
            "Comunidad Lingüística","Cantidad de hijos","Temporalidad del contrato","Tipo de contrato",
            "Fecha de inicio de labores","Fecha  de reinicio de labores","Fecha de finalización de labores",
            "Ocupación (puesto)","Jornada de trabajo","Días laborados en el año","Salario mensual nominal",
            "Salario anual nominal","Bonificación Decreto\n78-89  (Q.250.00)","Total horas extras anuales",
            "Valor de la hora extra ","Monto Aguinaldo\n76-78","Monto Bono 14\n42-92",
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
            "bold": True,
            "font_name": "Arial",
            "font_size": 10,
            "align": "center",
            "valign": "vcenter",
            "text_wrap": True,
            "border": 2,
            "bg_color": "#D9D9D9",
        })
        sheet.set_row(0, 78.75)
        for col, h in enumerate(headers):
            sheet.write(0, col, h, header_fmt)

        # Ejemplo: escribir filas (aquí pondrías tus 45 columnas calculadas)
        row = 1
        logging.warning(data_by_emp)
        for emp_id, info in data_by_emp.items():
            emp = info["emp"]
            contrato = info["contrato"]
            estado_civil_emp = getattr(emp, "marital", "")
            genero_emp = getattr(emp, "gender", "")
            values = [""] * 45   # ✅ SIEMPRE primero
            sheet.write(row, 0, str(row))
            logging.warning(emp.primer_nombre)
            values[1]  = getattr(emp, "primer_nombre", "") or ""
            values[2]  = getattr(emp, "segundo_nombre", "") or ""
            values[3]  = getattr(emp, "tercer_nombre", "") or ""
            values[4]  = getattr(emp, "primer_apellido", "") or ""
            values[5]  = getattr(emp, "segundo_apellido", "") or ""
            values[6]  = getattr(emp, "apellido_casada", "") or ""
            values[7]  = emp.country_id.name if emp.country_id else ""
            values[8]  = getattr(emp, "tipo_discapacidad", "") or ""
            estado_civil = ""
            if estado_civil_emp:
                if estado_civil_emp == "single":
                    estado_civil = 1
                elif estado_civil_emp == "married":
                    estado_civil = 2
                else:
                    estado_civil = 0
            values[9]  = estado_civil
            values[10] = "1"
            values[11] = emp.identification_id or ""
            values[12] = "GTM"
            values[13] = getattr(emp, "trabajo_extranjero", "") or ""
            values[14] = emp.municipio_nacimiento_id.code or ""
            values[15] = getattr(emp, "nit", "") or ""
            values[16] = getattr(emp, "igss", "") or ""
            genero = ""
            if emp.gender:
                if emp.gender == "male":
                    genero = "1"
                else:
                    genero = "2"
                
            values[17] = genero
            values[18] = emp.birthday or ""
            
            values[19] = getattr(emp, "nivel_academico", "") or ""
            values[20] = getattr(emp, "titulo_obtenido", "") or ""
            values[21] = getattr(emp, "pueblo_pertenencia", "") or ""
            values[22] = "99"
            values[23] = getattr(emp, "cantidad_hijos", 0) or 0
            
            values[24] = getattr(contrato, "temporalidad_contrato", "") if contrato else ""
            values[25] = getattr(contrato, "tipo_contrato", "") if contrato else ""
            values[26] = contrato.date_start if contrato else ""
            values[27] = ""
            values[28] = contrato.date_end if contrato else ""
            values[29] = emp.puesto_codigo if emp.puesto_codigo else ""
            values[30] = getattr(contrato, "codigo_jornada", "") if contrato else ""
            
            # values[31] = dias_laborados
            # values[32] = wage_month
            # values[33] = salario_anual
            # values[34] = bonif_250
            # values[35] = horas_ot
            # values[36] = valor_hora_extra
            # values[37] = aguinaldo
            # values[38] = bono14
            # values[39] = comisiones
            # values[40] = viaticos
            # values[41] = bonif_adic
            # values[42] = vacaciones
            # values[43] = indemnizacion
            # values[44] = (getattr(emp, "x_sucursal_id", False) and emp.x_sucursal_id.name) or (emp.company_id.name if emp.company_id else "")
            for col, val in enumerate(values):
                sheet.write(row, col, val)
            row += 1

        workbook.close()
        output.seek(0)

        filename = f"Informe_Empleador_{self.year}.xlsx"
        self.write({
            "file_name": filename,
            "file_data": base64.b64encode(output.read()),
        })

        # Reabrir wizard con botón de descarga (mismo wizard)
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

