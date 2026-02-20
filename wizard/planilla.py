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
import re
_logger = logging.getLogger(__name__)


class planilla_wizard(models.TransientModel):
    _name = 'hr_gt.planilla.wizard'

    nomina_ids = fields.Many2many('hr.payslip.run', string='Planillas', required=True)
    formato_planilla_id = fields.Many2one('hr_gt.formato_planilla', 'Formato planilla', required=True)
    archivo = fields.Binary('Archivo')
    name = fields.Char('File Name', size=32)
    columna_igss = fields.Boolean('Agregar columna IGSS')
    agrupar_departamento = fields.Boolean('Agrupar por departamento')
    agrupar_estructura = fields.Boolean('Agrupar por estructura')
    base_mensual = fields.Boolean('Incluir base mensual')
    fecha_inicio = fields.Date('Fecha inicio')
    fecha_fin = fields.Date('Fecha fin')
    ordenar_secuencia = fields.Boolean('Por sequencia')

    def busqueda_nominas(self, empleado_id, mes):
        nomina_ids = self.env['hr.payslip'].search([('employee_id', '=', empleado_id.id)])
        nominas = []
        for nomina in nomina_ids:
            mes_nomina = int(datetime.datetime.strptime(str(nomina.date_to), '%Y-%m-%d').date().strftime('%m'))
            if empleado_id.id == nomina.employee_id.id and mes == mes_nomina:
                nominas.append(nomina)
        return nominas

    # ----------------------------
    # Helpers para hojas por etiqueta
    # ----------------------------
    def _get_tag(self, employee):
        """Devuelve recordset de 0 o 1 etiqueta (hr.employee.category)."""
        # El usuario indicó que cada empleado tiene solo 1 etiqueta
        return employee.category_ids[:1]

    def _sanitize_sheet_name(self, name):
        name = (name or "Sin etiqueta").strip()
        # Caracteres inválidos en nombres de hoja Excel: []:*?/\ (y también se limita a 31 chars)
        name = re.sub(r'[\[\]\:\*\?\/\\]', '-', name)
        name = name.strip()
        if not name:
            name = "Sin etiqueta"
        return name[:31]

    def _unique_sheet_name(self, base_name, used):
        """Garantiza nombre único dentro del archivo."""
        name = self._sanitize_sheet_name(base_name)
        if name not in used:
            used.add(name)
            return name

        i = 2
        while True:
            suffix = f" ({i})"
            trimmed = name[:31 - len(suffix)]
            candidate = f"{trimmed}{suffix}"
            if candidate not in used:
                used.add(candidate)
                return candidate
            i += 1

    def _ensure_bucket(self, bucket, group_id, group_name, w):
        """Estructura estándar para dept_id (o struct_id)."""
        if group_id not in bucket:
            bucket[group_id] = {
                'nombre_agrupado': group_name,
                'empleados': {},
                'totales_ingresos': [0] * len(w.formato_planilla_id.ingreso_ids),
                'totales_egresos': [0] * len(w.formato_planilla_id.egreso_ids),
            }

    def _ensure_employee(self, bucket, group_id, employee, w):
        if employee.id not in bucket[group_id]['empleados']:
            bucket[group_id]['empleados'][employee.id] = {
                'nombre_empleado': employee.name,
                'ingresos': [0] * len(w.formato_planilla_id.ingreso_ids),
                'egresos': [0] * len(w.formato_planilla_id.egreso_ids),
                'total_salario': 0,
            }

    def _accumulate_lines(self, bucket, group_id, nomina, w):
        """Acumula line_ids en bucket[group_id]."""
        emp_data = bucket[group_id]['empleados'][nomina.employee_id.id]

        for linea in nomina.line_ids:
            # INGRESOS
            if w.formato_planilla_id.ingreso_ids:
                for columna in w.formato_planilla_id.ingreso_ids:
                    if linea.salary_rule_id.id in columna.regla_ids.ids:
                        idx = w.formato_planilla_id.ingreso_ids.ids.index(columna.id)
                        if idx >= 0:
                            emp_data['ingresos'][idx] += linea.total
                            # Total salario / totales agrupados solo si la columna es "Total"
                            if "total" in (columna.name or "").lower():
                                emp_data['total_salario'] += linea.total
                                bucket[group_id]['totales_ingresos'][idx] += linea.total

            # EGRESOS
            if w.formato_planilla_id.egreso_ids:
                for columna in w.formato_planilla_id.egreso_ids:
                    if linea.salary_rule_id.id in columna.regla_ids.ids:
                        idx = w.formato_planilla_id.egreso_ids.ids.index(columna.id)
                        if idx >= 0:
                            emp_data['egresos'][idx] += linea.total
                            if "total" in (columna.name or "").lower():
                                emp_data['total_salario'] += linea.total
                                bucket[group_id]['totales_egresos'][idx] += linea.total

    def _write_sheet(self, libro, sheet_name, w, datos_bucket):
        """Pinta una worksheet con el mismo formato de la hoja original."""
        formato_fecha = libro.add_format({'num_format': 'dd/mm/yy'})
        cell_format_bold = libro.add_format({'bold': True})

        hoja = libro.add_worksheet(sheet_name[:31])

        hoja.write(0, 0, 'Planilla')
        if len(w.nomina_ids) == 1:
            hoja.write(0, 1, w.nomina_ids[0].name)
        elif len(w.nomina_ids) > 1:
            hoja.write(0, 1, ', '.join(w.nomina_ids.mapped('name')))
        else:
            hoja.write(0, 1, '')

        hoja.write(0, 2, 'Periodo')
        hoja.write(0, 3, w.fecha_inicio, formato_fecha)
        hoja.write(0, 4, w.fecha_fin, formato_fecha)

        total_general = 0
        fila = 2

        if datos_bucket:
            for dato in datos_bucket:
                if not datos_bucket[dato].get('empleados'):
                    continue

                columna_encabezado = 1
                fila += 1
                hoja.write(fila, 0, datos_bucket[dato]['nombre_agrupado'], cell_format_bold)

                fila += 1
                hoja.write(fila, 0, 'Nombre', formato_fecha)

                if w.formato_planilla_id.ingreso_ids:
                    for columna_ingreso in w.formato_planilla_id.ingreso_ids:
                        hoja.write(fila, columna_encabezado, columna_ingreso.name, cell_format_bold)
                        columna_encabezado += 1

                if w.formato_planilla_id.egreso_ids:
                    for columna_egreso in w.formato_planilla_id.egreso_ids:
                        hoja.write(fila, columna_encabezado, columna_egreso.name, cell_format_bold)
                        columna_encabezado += 1

                hoja.write(fila, columna_encabezado, 'Total', cell_format_bold)

                empleados_info = datos_bucket[dato]['empleados']
                fila += 1

                for emp_id in empleados_info:
                    columna_empleado = 0
                    hoja.write(fila, columna_empleado, str(empleados_info[emp_id]['nombre_empleado']))
                    columna_empleado += 1

                    for valor in empleados_info[emp_id]['ingresos']:
                        hoja.write(fila, columna_empleado, valor)
                        columna_empleado += 1

                    for valor in empleados_info[emp_id]['egresos']:
                        hoja.write(fila, columna_empleado, valor)
                        columna_empleado += 1

                    hoja.write(fila, columna_empleado, empleados_info[emp_id]['total_salario'])
                    fila += 1

                # Total general por agrupación (usando totales_ingresos/egresos)
                total_agrupado = 0
                for valor in datos_bucket[dato]['totales_ingresos']:
                    total_agrupado += valor
                for valor in datos_bucket[dato]['totales_egresos']:
                    total_agrupado += valor

                total_general += total_agrupado
                fila += 1

            hoja.write(fila, 0, 'TOTAL SALARIOS', cell_format_bold)
            hoja.write(fila, 1, total_general, cell_format_bold)

    # ----------------------------
    # Main
    # ----------------------------
    def generar_excel(self):
        for w in self:
            logging.warning("ODOOO -----")
            _logger.warning("agrupar_departamento=%s agrupar_estructura=%s", w.agrupar_departamento, w.agrupar_estructura)

            f = io.BytesIO()
            libro = xlsxwriter.Workbook(f)
            formato_fecha = libro.add_format({'num_format': 'dd/mm/yy'})

            # Si NO está agrupando por departamento, se mantiene el comportamiento original:
            # una sola hoja "Planilla" con el diccionario "datos" como antes.
            if not w.agrupar_departamento:
                hoja = libro.add_worksheet('Planilla')

                merge_format = libro.add_format({'align': 'center'})

                hoja.write(0, 0, 'Planilla')
                if len(w.nomina_ids) == 1:
                    hoja.write(0, 1, w.nomina_ids[0].name)
                elif len(w.nomina_ids) > 1:
                    lista_nominas = []
                    for n in w.nomina_ids:
                        lista_nominas.append(n.name)
                    hoja.write(0, 1, ', '.join(lista_nominas))
                else:
                    hoja.write(0, 1, '')
                hoja.write(0, 2, 'Periodo')
                hoja.write(0, 3, w.fecha_inicio, formato_fecha)
                hoja.write(0, 4, w.fecha_fin, formato_fecha)

                datos = {}
                ingresos_lista = []
                egresos_lista = []
                if w.formato_planilla_id.ingreso_ids:
                    ingresos_lista = [0] * len(w.formato_planilla_id.ingreso_ids)
                if w.formato_planilla_id.egreso_ids:
                    egresos_lista = [0] * len(w.formato_planilla_id.egreso_ids)

                if w.agrupar_estructura:
                    if w.nomina_ids:
                        for lote in w.nomina_ids:
                            if lote.slip_ids:
                                for nomina in lote.slip_ids:
                                    if nomina.line_ids and nomina.struct_id.id:
                                        if nomina.struct_id.id not in datos:
                                            datos[nomina.struct_id.id] = {
                                                'nombre_agrupado': nomina.struct_id.name,
                                                'empleados': {},
                                                'totales_ingresos': [0] * len(w.formato_planilla_id.ingreso_ids),
                                                'totales_egresos': [0] * len(w.formato_planilla_id.egreso_ids)
                                            }

                                        if nomina.employee_id.id not in datos[nomina.struct_id.id]['empleados']:
                                            datos[nomina.struct_id.id]['empleados'][nomina.employee_id.id] = {
                                                'nombre_empleado': nomina.employee_id.name,
                                                'ingresos': [0] * len(w.formato_planilla_id.ingreso_ids),
                                                'egresos': [0] * len(w.formato_planilla_id.egreso_ids),
                                                'total_salario': 0
                                            }

                                        for linea in nomina.line_ids:
                                            if w.formato_planilla_id.ingreso_ids:
                                                for columna in w.formato_planilla_id.ingreso_ids:
                                                    if linea.salary_rule_id.id in columna.regla_ids.ids:
                                                        pos = w.formato_planilla_id.ingreso_ids.ids.index(columna.id)
                                                        if pos >= 0:
                                                            datos[nomina.struct_id.id]['empleados'][nomina.employee_id.id]['ingresos'][pos] += linea.total
                                                            if "total" in (columna.name or "").lower():
                                                                datos[nomina.struct_id.id]['empleados'][nomina.employee_id.id]['total_salario'] += linea.total
                                                                datos[nomina.struct_id.id]['totales_ingresos'][pos] += linea.total

                                            if w.formato_planilla_id.egreso_ids:
                                                for columna in w.formato_planilla_id.egreso_ids:
                                                    if linea.salary_rule_id.id in columna.regla_ids.ids:
                                                        pos = w.formato_planilla_id.egreso_ids.ids.index(columna.id)
                                                        if pos >= 0:
                                                            datos[nomina.struct_id.id]['empleados'][nomina.employee_id.id]['egresos'][pos] += linea.total
                                                            if "total" in (columna.name or "").lower():
                                                                datos[nomina.struct_id.id]['empleados'][nomina.employee_id.id]['total_salario'] += linea.total
                                                                datos[nomina.struct_id.id]['totales_egresos'][pos] += linea.total

                total_general = 0
                cell_format_bold = libro.add_format({'bold': True})

                if datos:
                    fila = 2
                    for dato in datos:
                        if datos[dato]['empleados']:
                            columna_encabezado = 1
                            fila += 1
                            hoja.write(fila, 0, datos[dato]['nombre_agrupado'], cell_format_bold)
                            fila += 1
                            hoja.write(fila, 0, 'Nombre', formato_fecha)

                            if w.formato_planilla_id.ingreso_ids:
                                for columna_ingreso in w.formato_planilla_id.ingreso_ids:
                                    hoja.write(fila, columna_encabezado, columna_ingreso.name, cell_format_bold)
                                    columna_encabezado += 1

                            if w.formato_planilla_id.egreso_ids:
                                for columna_egreso in w.formato_planilla_id.egreso_ids:
                                    hoja.write(fila, columna_encabezado, columna_egreso.name, cell_format_bold)
                                    columna_encabezado += 1

                            hoja.write(fila, columna_encabezado, 'Total', cell_format_bold)

                            empleados_info = datos[dato]['empleados']
                            fila += 1
                            for empleado in empleados_info:
                                columna_empleado = 0
                                hoja.write(fila, columna_empleado, str(empleados_info[empleado]['nombre_empleado']))
                                columna_empleado += 1

                                for valor in empleados_info[empleado]['ingresos']:
                                    hoja.write(fila, columna_empleado, valor)
                                    columna_empleado += 1

                                for valor in empleados_info[empleado]['egresos']:
                                    hoja.write(fila, columna_empleado, valor)
                                    columna_empleado += 1

                                hoja.write(fila, columna_empleado, empleados_info[empleado]['total_salario'])
                                fila += 1

                            total_agrupado = sum(datos[dato]['totales_ingresos']) + sum(datos[dato]['totales_egresos'])
                            total_general += total_agrupado
                            fila += 1

                    hoja.write(fila, 0, 'TOTAL SALARIOS', cell_format_bold)
                    hoja.write(fila, 1, total_general, cell_format_bold)

                libro.close()
                datos_file = base64.b64encode(f.getvalue())
                self.write({'archivo': datos_file, 'name': 'planilla.xlsx'})
                return {
                    'context': self.env.context,
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'hr_gt.planilla.wizard',
                    'res_id': self.id,
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                }

            # -----------------------------------------------------------------
            # NUEVO: agrupar_departamento + hojas por etiqueta + Resumen
            # -----------------------------------------------------------------
            datos_resumen = {}       # {dept_id: {...}}
            datos_por_etiqueta = {}  # {tag_id: {'_tag_name': str, '_data': {dept_id: {...}}}}

            if w.nomina_ids:
                for lote in w.nomina_ids:
                    if not lote.slip_ids:
                        continue

                    for nomina in lote.slip_ids:
                        if not (nomina.line_ids and nomina.contract_id and nomina.contract_id.department_id):
                            continue

                        dept = nomina.contract_id.department_id
                        emp = nomina.employee_id
                        tag = self._get_tag(emp)

                        # --- RESUMEN (todo junto) ---
                        self._ensure_bucket(datos_resumen, dept.id, dept.name, w)
                        self._ensure_employee(datos_resumen, dept.id, emp, w)
                        self._accumulate_lines(datos_resumen, dept.id, nomina, w)

                        # --- POR ETIQUETA ---
                        tag_key = tag.id if tag else 0
                        tag_name = tag.name if tag else 'Sin etiqueta'

                        if tag_key not in datos_por_etiqueta:
                            datos_por_etiqueta[tag_key] = {'_tag_name': tag_name, '_data': {}}

                        data_tag = datos_por_etiqueta[tag_key]['_data']
                        self._ensure_bucket(data_tag, dept.id, dept.name, w)
                        self._ensure_employee(data_tag, dept.id, emp, w)
                        self._accumulate_lines(data_tag, dept.id, nomina, w)

            # Escribir hojas
            used_names = set()

            # 1) Resumen (primera pestaña)
            resumen_sheet = self._unique_sheet_name('Resumen', used_names)
            self._write_sheet(libro, resumen_sheet, w, datos_resumen)

            # 2) Una hoja por etiqueta (nombre = nombre de la etiqueta)
            for tag_key in sorted(datos_por_etiqueta.keys(), key=lambda k: (datos_por_etiqueta[k]['_tag_name'] or '')):
                tag_name = datos_por_etiqueta[tag_key]['_tag_name']
                sheet_name = self._unique_sheet_name(tag_name, used_names)
                self._write_sheet(libro, sheet_name, w, datos_por_etiqueta[tag_key]['_data'])

            libro.close()
            datos_file = base64.b64encode(f.getvalue())
            self.write({'archivo': datos_file, 'name': 'planilla.xlsx'})
            return {
                'context': self.env.context,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'hr_gt.planilla.wizard',
                'res_id': self.id,
                'view_id': False,
                'type': 'ir.actions.act_window',
                'target': 'new',
            }

    def print_report(self):
        datas = {'ids': self.env.context.get('active_ids', [])}
        res = self.read(['nomina_id', 'formato_planilla_id'])
        res = res and res[0] or {}
        datas['form'] = res
        return self.env.ref('hr_gt.action_planilla').report_action([], data=datas)
