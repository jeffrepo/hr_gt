# -*- encoding: utf-8 -*-

from odoo import api, models, fields
from datetime import date
import datetime
import time
import dateutil.parser
from dateutil.relativedelta import relativedelta
from dateutil import relativedelta as rdelta
from odoo.fields import Date, Datetime
import logging

class ReportPlanilla(models.AbstractModel):
    _name = 'report.hr_gt.planilla'

    def mes_letras(self,fecha):
        mes_nomina = int(datetime.datetime.strptime(str(fecha), '%Y-%m-%d').date().strftime('%m'))
        mes =  ''
        if mes_nomina == 1:
            mes = 'ENERO'
        if mes_nomina == 2:
            mes = 'FEBRERO'
        if mes_nomina == 3:
            mes = 'MARZO'
        if mes_nomina == 4:
            mes = 'ABRIL'
        if mes_nomina == 6:
            mes = 'MAYO'
        if mes_nomina == 6:
            mes = 'JUNIO'
        if mes_nomina == 7:
            mes = 'JULIO'
        if mes_nomina == 8:
            mes = 'AGOSTO'
        if mes_nomina == 9:
            mes = 'SEPTIEMBRE'
        if mes_nomina == 10:
            mes = 'OCTUBRE'
        if mes_nomina == 11:
            mes = 'NOVIEMBRE'
        if mes_nomina == 12:
            mes = 'DICIEMBRE'
        return mes

    def busqueda_nominas(self, empleado_id,mes):
        nomina_ids = self.env['hr.payslip'].search([('employee_id','=',empleado_id.id)])
        nominas = []
        for nomina in nomina_ids:
            mes_nomina = int(datetime.datetime.strptime(str(nomina.date_to), '%Y-%m-%d').date().strftime('%m'))
            if empleado_id.id == nomina.employee_id.id and mes == mes_nomina:
                nominas.append(nomina)
        return nominas

    def _get_nomina(self,nomina_id):
        nomina = False
        nomina = self.env['hr.payslip.run'].search([('id','=',nomina_id[0])])

        return nomina


    def resumen(self,slip,igss,general):
        slip = self.env['hr.payslip.run'].search([('id','=',slip[0])])
        company = slip.slip_ids[0].employee_id.company_id
        departamentos = self.env['hr.department'].search([('company_id','=',company.id)])

        # datos = []
        datos_departamento = []
        # d = {
        # 'nominas': [],
        #
        # }
        # for nomina in o.slip_ids:
        #     faltas = 0
        #     trabajado = 0
        #     suspension = 0
        #     vacas = 0
        #     sueldo = 0
        #     vacaciones = 0
        #     bonificacion = 0
        #     bono_otro = 0
        #     total = 0
        #     calc = 0
        #     vales = 0
        #     ajuste = 0
        #     igss = 0
        #     isr = 0
        #     otros_descuentos = 0
        #     vale = 0
        #     comision = 0
        #     uniformes = 0
        #     anticipo_quincena = 0
        #     for dias_linea in nomina.worked_days_line_ids:
        #         if dias_linea.code == 'DIAS':
        #             trabajado = dias_linea.number_of_days
        #         if dias_linea.code == 'FALTA':
        #             falta = dias_linea.number_of_days
        #         if dias_linea.code == 'IGSS':
        #             suspension = dias_linea.number_of_days
        #         if dias_linea.code == 'VACAS':
        #             vacas = dias_linea.number_of_days
        #     for regla in nomina.line_ids:
        #         if regla.code == 'SNT':
        #             sueldo = regla.total
        #         if regla.salary_rule_id.id in nomina.employee_id.company_id.vacacion_ids.ids:
        #             vacaciones = regla.total
        #         if regla.code == 'BONI':
        #             bonificacion = regla.total
        #         if regla.code == 'IGSSLABORAL':
        #             igss = regla.total
        #         if regla.code == 'ISR':
        #             isr = regla.total
        #         if regla.code == 'PRES':
        #             otros_descuentos = regla.total
        #         if regla.code == 'VALE':
        #             vales = regla.total
        #         if regla.code == 'COMI':
        #             comision = regla.total
        #         if regla.code == 'AQ':
        #             anticipo_quincena = regla.total
        #         if regla.code == 'OB':
        #             bono_otro = regla.total
        #         if regla.code == 'UNI':
        #             uniformes = regla.total
        #     datos.append({
        #     'nombre_empleado': nomina.employee_id.name,
        #     'trabajado': trabajado,
        #     'faltas': faltas,
        #     'vacas': vacas,
        #     'suspension': suspension,
        #     'igss': igss,
        #     'isr': isr,
        #     'uniformes': uniformes,
        #     'comision': comision,
        #     'otros_descuentos': otros_descuentos,
        #     'vales': vales,
        #     'sueldo': sueldo,
        #     'vacaciones': vacaciones,
        #     'bonificacion': bonificacion,
        #     'bono_otro': bono_otro,
        #     'total': sueldo + bonificacion + vacaciones + bono_otro + comision,
        #     'total_descuentos': igss + isr+ otros_descuentos + vales+uniformes,
        #     'calc': calc,
        #     'ajuste': ajuste,
        #     'anticipo_quincena': anticipo_quincena,
        #     'total_liquido': sueldo
        #     })


        # logging.warn(datos)

        for departamento in departamentos:
            d = {
                'nombre': departamento.name,
                'nominas': [],
                'id': departamento.id
            }
            datos_departamento.append(d)
        logging.warn(datos_departamento)
        if general:
            for slip in slip.slip_ids:
                mes_actual = int(datetime.datetime.strptime(str(slip.date_to), '%Y-%m-%d').date().strftime('%m'))
                nominas_buscadas = self.busqueda_nominas(slip.employee_id, mes_actual)
                logging.warn(nominas_buscadas)
                for dato in datos_departamento:
                    if int(slip.employee_id.department_id.id) ==  int(dato['id']):
                        renuncia = 0
                        falta = 0
                        trabajado = 0
                        suspension = 0
                        vacas = 0
                        sueldo = 0
                        vacaciones = 0
                        bonificacion = 0
                        bono_otro = 0
                        total = 0
                        calc = 0
                        vales = 0
                        ajuste = 0
                        igss = 0
                        isr = 0
                        otros_descuentos = 0
                        vale = 0
                        comision = 0
                        uniformes = 0
                        anticipo_quincena = 0
                        total = 0
                        total_descuentos = 0
                        total_descuentos2 = 0
                        total_liquido = 0
                        comi = 0
                        for nomina in nominas_buscadas:
                            for entrada in nomina.input_line_ids:
                                if entrada.code == 'SBANTERIOR':
                                    if nomina.employee_id.id == 273:
                                        logging.warn('asdasdsadsadsadsadsadsadsadsadasd')
                                    quincena_anterior = (-1 *entrada.amount)
                                if entrada.code == 'COMIANTERIOR':
                                    comi = (entrada.amount*-1)
                            for dias_linea in nomina.worked_days_line_ids:
                                if dias_linea.code == 'DIAS':
                                    trabajado += dias_linea.number_of_days
                                if dias_linea.code == 'FALTA' or dias_linea.code == 'Falta':
                                    falta += dias_linea.number_of_days
                                if dias_linea.code == 'IGSS':
                                    suspension += dias_linea.number_of_days
                                if dias_linea.code == 'VACAS' or dias_linea.code == 'Vacaciones':
                                    vacas += dias_linea.number_of_days
                                if dias_linea.code == 'SUSPE':
                                    suspension += dias_linea.number_of_days
                                if dias_linea.code == 'RENUNCIA':
                                    renuncia += dias_linea.number_of_days
                            for regla in nomina.line_ids:
                                if nomina.fin_mes:
                                    if regla.code == 'SBASE':
                                        sueldo += regla.total
                                else:
                                    if regla.code == 'AQ':
                                        sueldo += regla.total
                                if regla.salary_rule_id.id in nomina.employee_id.company_id.vacacion_ids.ids:
                                    vacaciones += regla.total
                                if regla.code == 'BONI':
                                    bonificacion += regla.total
                                if regla.code == 'IGSSLABORAL':
                                    igss += regla.total
                                if regla.code == 'ISR':
                                    isr += regla.total
                                if regla.code == 'PRES':
                                    otros_descuentos += (regla.total *-1) if regla.total > 0 else regla.total
                                if regla.code == 'VALES':
                                    vales += (regla.total *-1) if regla.total > 0 else regla.total
                                if regla.code == 'COMI':
                                    comision += regla.total
                                if regla.code == 'AQ':
                                    anticipo_quincena += regla.total
                                if regla.code == 'OB':
                                    bono_otro += regla.total
                                if regla.code == 'UNI':
                                    uniformes += (regla.total *-1) if regla.total > 0 else regla.total

                            # for dias_linea in nomina.worked_days_line_ids:
                            #     if dias_linea.code == 'DIAS':
                            #         trabajado += dias_linea.number_of_days
                            #     if dias_linea.code == 'FALTA':
                            #         falta += dias_linea.number_of_days
                            #     if dias_linea.code == 'SUSPE':
                            #         suspension += dias_linea.number_of_days
                            #     if dias_linea.code == 'RENUNCIA':
                            #         renuncia += dias_linea.number_of_days
                            # salario_anterior = 0
                            # for o in nomina.input_line_ids:
                            #     if o.code == 'SBANTERIOR':
                            #         salario_anterior += o.amount
                            # for regla in nomina.line_ids:
                            #     if regla.salary_rule_id.id in nomina.employee_id.company_id.ordinario_ids.ids:
                            #         sueldo += regla.total
                            #     if regla.salary_rule_id.id in nomina.employee_id.company_id.vacacion_ids.ids:
                            #         vacaciones += regla.total
                            #     if regla.salary_rule_id.id in nomina.employee_id.company_id.bonificacion_ids.ids:
                            #         bonificacion += regla.total
                        if self.env.user.company_id.id == 1 and nomina.fin_mes == False:
                            logging.warn('compa')
                            total = sueldo + bonificacion + vacaciones + bono_otro + comision
                        elif self.env.user.company_id.id == 1 and nomina.fin_mes:
                            total = sueldo + bonificacion + vacaciones + bono_otro + comision
                        else:
                            total = sueldo + bonificacion + vacaciones + bono_otro + comision
                        total_descuentos = igss + isr+ otros_descuentos + vales+uniformes
                        total_descuentos2 = igss + isr+ otros_descuentos + vales+uniformes + (quincena_anterior - comi)
                        total_liquido = total + total_descuentos2 +anticipo_quincena
                        dato['nominas'].append({
                            'nombre_empleado': nomina.employee_id.name,
                            'trabajado': trabajado,
                            'faltas': falta,
                            'vacas': vacas,
                            'suspension': suspension,
                            'igss': igss,
                            'isr': isr,
                            'uniformes': uniformes,
                            'comision': comision,
                            'otros_descuentos': otros_descuentos,
                            'vales': vales,
                            'sueldo': sueldo,
                            'vacaciones': vacaciones,
                            'bonificacion': bonificacion,
                            'bono_otro': bono_otro,
                            'total': total,
                            'total_descuentos': total_descuentos2,
                            'calc': calc,
                            'ajuste': ajuste,
                            'quincena_anterior': (quincena_anterior*-1),
                            'total_liquido': total_liquido
                        })
        elif igss:
            for slip in slip.slip_ids:
                mes_actual = int(datetime.datetime.strptime(str(slip.date_to), '%Y-%m-%d').date().strftime('%m'))
                nominas_buscadas = self.busqueda_nominas(slip.employee_id, mes_actual)
                logging.warn(nominas_buscadas)
                for dato in datos_departamento:
                    if int(slip.employee_id.department_id.id) ==  int(dato['id']) and slip.employee_id.igss:
                        renuncia = 0
                        falta = 0
                        trabajado = 0
                        suspension = 0
                        vacas = 0
                        sueldo = 0
                        vacaciones = 0
                        bonificacion = 0
                        bono_otro = 0
                        total = 0
                        calc = 0
                        vales = 0
                        ajuste = 0
                        igss = 0
                        isr = 0
                        otros_descuentos = 0
                        vale = 0
                        comision = 0
                        uniformes = 0
                        anticipo_quincena = 0
                        total = 0
                        total_descuentos = 0
                        total_descuentos2 = 0
                        total_liquido = 0
                        comi = 0
                        for nomina in nominas_buscadas:
                            for entrada in nomina.input_line_ids:
                                if entrada.code == 'SBANTERIOR':
                                    if nomina.employee_id.id == 273:
                                        logging.warn('asdasdsadsadsadsadsadsadsadsadasd')
                                    quincena_anterior = (-1 *entrada.amount)
                                if entrada.code == 'COMIANTERIOR':
                                    comi = (entrada.amount*-1)
                            for dias_linea in nomina.worked_days_line_ids:
                                if dias_linea.code == 'DIAS':
                                    trabajado += dias_linea.number_of_days
                                if dias_linea.code == 'FALTA' or dias_linea.code == 'Falta':
                                    falta += dias_linea.number_of_days
                                if dias_linea.code == 'IGSS':
                                    suspension += dias_linea.number_of_days
                                if dias_linea.code == 'VACAS' or dias_linea.code == 'Vacaciones':
                                    vacas += dias_linea.number_of_days
                                if dias_linea.code == 'SUSPE':
                                    suspension += dias_linea.number_of_days
                                if dias_linea.code == 'RENUNCIA':
                                    renuncia += dias_linea.number_of_days
                            for regla in nomina.line_ids:
                                if nomina.fin_mes:
                                    if regla.code == 'SBASE':
                                        sueldo += regla.total
                                else:
                                    if regla.code == 'AQ':
                                        sueldo += regla.total
                                if regla.salary_rule_id.id in nomina.employee_id.company_id.vacacion_ids.ids:
                                    vacaciones += regla.total
                                if regla.code == 'BONI':
                                    bonificacion += regla.total
                                if regla.code == 'IGSSLABORAL':
                                    igss += regla.total
                                if regla.code == 'ISR':
                                    isr += regla.total
                                if regla.code == 'PRES':
                                    otros_descuentos += (regla.total *-1) if regla.total > 0 else regla.total
                                if regla.code == 'VALES':
                                    vales += (regla.total *-1) if regla.total > 0 else regla.total
                                if regla.code == 'COMI':
                                    comision += regla.total
                                if regla.code == 'AQ':
                                    anticipo_quincena += regla.total
                                if regla.code == 'OB':
                                    bono_otro += regla.total
                                if regla.code == 'UNI':
                                    uniformes += (regla.total *-1) if regla.total > 0 else regla.total

                            # for dias_linea in nomina.worked_days_line_ids:
                            #     if dias_linea.code == 'DIAS':
                            #         trabajado += dias_linea.number_of_days
                            #     if dias_linea.code == 'FALTA':
                            #         falta += dias_linea.number_of_days
                            #     if dias_linea.code == 'SUSPE':
                            #         suspension += dias_linea.number_of_days
                            #     if dias_linea.code == 'RENUNCIA':
                            #         renuncia += dias_linea.number_of_days
                            # salario_anterior = 0
                            # for o in nomina.input_line_ids:
                            #     if o.code == 'SBANTERIOR':
                            #         salario_anterior += o.amount
                            # for regla in nomina.line_ids:
                            #     if regla.salary_rule_id.id in nomina.employee_id.company_id.ordinario_ids.ids:
                            #         sueldo += regla.total
                            #     if regla.salary_rule_id.id in nomina.employee_id.company_id.vacacion_ids.ids:
                            #         vacaciones += regla.total
                            #     if regla.salary_rule_id.id in nomina.employee_id.company_id.bonificacion_ids.ids:
                            #         bonificacion += regla.total
                        if self.env.user.company_id.id == 1 and nomina.fin_mes == False:
                            logging.warn('compa')
                            total = sueldo + bonificacion + vacaciones + bono_otro + comision
                        elif self.env.user.company_id.id == 1 and nomina.fin_mes:
                            total = sueldo + bonificacion + vacaciones + bono_otro + comision
                        else:
                            total = sueldo + bonificacion + vacaciones + bono_otro + comision
                        total_descuentos = igss + isr+ otros_descuentos + vales+uniformes
                        total_descuentos2 = igss + isr+ otros_descuentos + vales+uniformes + (quincena_anterior - comi)
                        total_liquido = total + total_descuentos2 +anticipo_quincena
                        dato['nominas'].append({
                            'nombre_empleado': nomina.employee_id.name,
                            'trabajado': trabajado,
                            'faltas': falta,
                            'vacas': vacas,
                            'suspension': suspension,
                            'igss': igss,
                            'isr': isr,
                            'uniformes': uniformes,
                            'comision': comision,
                            'otros_descuentos': otros_descuentos,
                            'vales': vales,
                            'sueldo': sueldo,
                            'vacaciones': vacaciones,
                            'bonificacion': bonificacion,
                            'bono_otro': bono_otro,
                            'total': total,
                            'total_descuentos': total_descuentos2,
                            'calc': calc,
                            'ajuste': ajuste,
                            'quincena_anterior': (quincena_anterior*-1),
                            'total_liquido': total_liquido
                        })
        else:
            for slip in slip.slip_ids:
                mes_actual = int(datetime.datetime.strptime(str(slip.date_to), '%Y-%m-%d').date().strftime('%m'))
                nominas_buscadas = self.busqueda_nominas(slip.employee_id, mes_actual)
                logging.warn(nominas_buscadas)
                for dato in datos_departamento:
                    if int(slip.employee_id.department_id.id) ==  int(dato['id']) and slip.employee_id.igss == False:
                        renuncia = 0
                        falta = 0
                        trabajado = 0
                        suspension = 0
                        vacas = 0
                        sueldo = 0
                        vacaciones = 0
                        bonificacion = 0
                        bono_otro = 0
                        total = 0
                        calc = 0
                        vales = 0
                        ajuste = 0
                        igss = 0
                        isr = 0
                        otros_descuentos = 0
                        vale = 0
                        comision = 0
                        uniformes = 0
                        anticipo_quincena = 0
                        total = 0
                        total_descuentos = 0
                        total_descuentos2 = 0
                        total_liquido = 0
                        comi = 0
                        quincena_anterior = 0
                        for nomina in nominas_buscadas:
                            for entrada in nomina.input_line_ids:
                                if entrada.code == 'SBANTERIOR':
                                    if nomina.employee_id.id == 273:
                                        logging.warn('asdasdsadsadsadsadsadsadsadsadasd')
                                    quincena_anterior = (-1 *entrada.amount)
                                if entrada.code == 'COMIANTERIOR':
                                    comi = (entrada.amount*-1)
                            for dias_linea in nomina.worked_days_line_ids:
                                if dias_linea.code == 'DIAS':
                                    trabajado += dias_linea.number_of_days
                                if dias_linea.code == 'FALTA' or dias_linea.code == 'Falta':
                                    falta += dias_linea.number_of_days
                                if dias_linea.code == 'IGSS':
                                    suspension += dias_linea.number_of_days
                                if dias_linea.code == 'VACAS' or dias_linea.code == 'Vacaciones':
                                    vacas += dias_linea.number_of_days
                                if dias_linea.code == 'SUSPE':
                                    suspension += dias_linea.number_of_days
                                if dias_linea.code == 'RENUNCIA':
                                    renuncia += dias_linea.number_of_days
                            for regla in nomina.line_ids:
                                if nomina.fin_mes:
                                    if regla.code == 'SBASE':
                                        sueldo += regla.total
                                else:
                                    if regla.code == 'AQ':
                                        sueldo += regla.total
                                if regla.salary_rule_id.id in nomina.employee_id.company_id.vacacion_ids.ids:
                                    vacaciones += regla.total
                                if regla.code == 'BONI':
                                    bonificacion += regla.total
                                if regla.code == 'IGSSLABORAL':
                                    igss += regla.total
                                if regla.code == 'ISR':
                                    isr += regla.total
                                if regla.code == 'PRES':
                                    otros_descuentos += (regla.total *-1) if regla.total > 0 else regla.total
                                if regla.code == 'VALES':
                                    vales += (regla.total *-1) if regla.total > 0 else regla.total
                                if regla.code == 'COMI':
                                    comision += regla.total
                                if regla.code == 'AQ':
                                    anticipo_quincena += regla.total
                                if regla.code == 'OB':
                                    bono_otro += regla.total
                                if regla.code == 'UNI':
                                    uniformes += (regla.total *-1) if regla.total > 0 else regla.total

                            # for dias_linea in nomina.worked_days_line_ids:
                            #     if dias_linea.code == 'DIAS':
                            #         trabajado += dias_linea.number_of_days
                            #     if dias_linea.code == 'FALTA':
                            #         falta += dias_linea.number_of_days
                            #     if dias_linea.code == 'SUSPE':
                            #         suspension += dias_linea.number_of_days
                            #     if dias_linea.code == 'RENUNCIA':
                            #         renuncia += dias_linea.number_of_days
                            # salario_anterior = 0
                            # for o in nomina.input_line_ids:
                            #     if o.code == 'SBANTERIOR':
                            #         salario_anterior += o.amount
                            # for regla in nomina.line_ids:
                            #     if regla.salary_rule_id.id in nomina.employee_id.company_id.ordinario_ids.ids:
                            #         sueldo += regla.total
                            #     if regla.salary_rule_id.id in nomina.employee_id.company_id.vacacion_ids.ids:
                            #         vacaciones += regla.total
                            #     if regla.salary_rule_id.id in nomina.employee_id.company_id.bonificacion_ids.ids:
                            #         bonificacion += regla.total
                        if self.env.user.company_id.id == 1 and nomina.fin_mes == False:
                            logging.warn('compa')
                            total = sueldo + bonificacion + vacaciones + bono_otro + comision
                        elif self.env.user.company_id.id == 1 and nomina.fin_mes:
                            total = sueldo + bonificacion + vacaciones + bono_otro + comision
                        else:
                            total = sueldo + bonificacion + vacaciones + bono_otro + comision
                        total_descuentos = igss + isr+ otros_descuentos + vales+uniformes
                        total_descuentos2 = igss + isr+ otros_descuentos + vales+uniformes + (quincena_anterior - comi)
                        total_liquido = total + total_descuentos2 +anticipo_quincena
                        dato['nominas'].append({
                            'nombre_empleado': nomina.employee_id.name,
                            'trabajado': trabajado,
                            'faltas': falta,
                            'vacas': vacas,
                            'suspension': suspension,
                            'igss': igss,
                            'isr': isr,
                            'uniformes': uniformes,
                            'comision': comision,
                            'otros_descuentos': otros_descuentos,
                            'vales': vales,
                            'sueldo': sueldo,
                            'vacaciones': vacaciones,
                            'bonificacion': bonificacion,
                            'bono_otro': bono_otro,
                            'total': total,
                            'total_descuentos': total_descuentos2,
                            'calc': calc,
                            'ajuste': ajuste,
                            'quincena_anterior': (quincena_anterior*-1),
                            'total_liquido': total_liquido
                        })
        # logging.warn(datos_departamento)
        return datos_departamento

    def fecha_hoy(self):
        return date.today().strftime("%d/%m/%Y")
    # def pagos_deducciones(self,o):
    #     ingresos = 0
    #     descuentos = 0
    #     datos = {'ordinario': 0, 'extra_ordinario':0,'bonificacion':0}
    #     for linea in o.linea_ids:
    #         if linea.salary_rule_id.id in o.company_id.ordinario_ids.ids:
    #             datos['ordinario'] += linea.total
    #         elif linea.salary_rule_id.id in o.company_id.extra_ordinario_ids.ids:
    #             datos['extra_ordinario'] += linea.total
    #         elif linea.salary_rule_id.id in o.company_id.bonificacion_ids.ids:
    #             datos['bonificacion'] += linea.total
    #     return True

    @api.model
    def _get_report_values(self, docids, data=None):
        return self.get_report_values(docids, data)

    @api.model
    def get_report_values(self, docids, data=None):
        self.model = 'hr.payslip.run'
        nomina_id = data.get('form', {}).get('nomina_id', False)
        formato_planilla_id = data.get('form', {}).get('formato_planilla_id', False)
        docs = self.env[self.model].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': self.model,
            'docs': docs,
            'nomina_id': nomina_id,
            'formato_planilla_id': formato_planilla_id,
            # 'mes_letras': self.mes_letras,
            # 'fecha_hoy': self.fecha_hoy,
            # 'resumen': self.resumen,
            # 'igss': igss,
            # '_get_nomina': self._get_nomina,
            # 'general': general,
            # 'lineas': self.lineas,
            # 'horas_extras': self.horas_extras,
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
