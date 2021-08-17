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

class igss_wizard(models.TransientModel):
    _name = 'hr_gt.igss.wizard'

    nomina_ids = fields.Many2many('hr.payslip.run', string='Planillas', required=True)
    # formato_recibo_pago_id = fields.Many2one('hr_gt.recibo_pago','Formato recibo pago', required=True)
    archivo = fields.Binary('Archivo')
    name =  fields.Char('File Name', size=32)
    # columna_igss = fields.Boolean('Agregar columna IGSS')
    # agrupar_departamento = fields.Boolean('Agrupa por departamento')
    fecha_inicio = fields.Date('Fecha inicio')
    fecha_fin = fields.Date('Fecha fin')


    def busqueda_nominas(self, empleado_id,mes):
        nomina_ids = self.env['hr.payslip'].search([('employee_id','=',empleado_id.id)])
        nominas = []
        for nomina in nomina_ids:
            mes_nomina = int(datetime.datetime.strptime(str(nomina.date_to), '%Y-%m-%d').date().strftime('%m'))
            if empleado_id.id == nomina.employee_id.id and mes == mes_nomina:
                nominas.append(nomina)
        return nominas

    def generar_excel(self):
        datos = ''
        for w in self:
            logging.warn(w.nomina_ids[0].slip_ids)
            fecha_planilla = datetime.datetime.strptime(str(w.fecha_inicio), '%Y-%m-%d')
            mes_planilla = fecha_planilla.month
            anio_planilla = fecha_planilla.year
            fecha_hoy = date.today().strftime("%d/%m/%Y")
            mes_nomina = int(datetime.datetime.strptime(str(w.fecha_inicio), '%Y-%m-%d').date().strftime('%m'))
            anio_nomina = int(datetime.datetime.strptime(str(w.fecha_inicio), '%Y-%m-%d').date().strftime('%Y'))
            compania = w.nomina_ids[0].slip_ids[0].employee_id.company_id
            datos += str(compania.version_mensaje) +'|'+ str(fecha_hoy)+'|'+str(compania.numero_patronal)+'|'+str(mes_nomina)+'|'+str(anio_nomina)+'|'+str(compania.name)+'|'+str(compania.vat)+'|'+str(compania.email)+'|'+'1'+'\r\n'
            datos += '[centros]' + '\r\n'
            logging.warn(datos)
            if compania.centro_ids:
                for c in compania.centro_ids:
                    datos += str(c.codigo)+'|'+str(c.nombre)+'|'+str(c.direccion)+'|'+str(c.zona)+'|'+str(c.telefono)+'|'+(str(c.fax) if c.fax else '' )+'|'+str(c.nombre_contacto)+'|'+str(c.correo_electronico)
                    datos +='|'+str(c.codigo_departamento)+'|'+str(c.codigo_municipio)+'|'+str(c.codigo_actividad_economica)+'\r\n'
            datos += '[tiposplanilla]' + '\r\n'
            if compania.tipo_planilla_ids:
                for t in compania.tipo_planilla_ids:
                    datos += t.identificacion_tipo_planilla + '|' + t.nombre_tipo_planilla + '|' + t.tipo_afiliados + '|' + t.periodo_planilla + '|' + t.departamento_republica + '|' + t.actividad_economica + '|' + t.clase_planilla + '|' +'\r\n'
            datos += '[liquidaciones]' + '\r\n'
            datos += '[empleados]' + '\r\n'

            nominas_lista = {}
            for nomina in w.nomina_ids:
                for slip in nomina.slip_ids:
                    if slip.employee_id.id not in nominas_lista:
                        nominas_lista[slip.employee_id.id] = {'nominas': [], 'empleado': slip.employee_id}
                    nominas_lista[slip.employee_id.id]['nominas'].append(slip)

            logging.warn(nominas_lista)

            for nomina in nominas_lista:

                datos += '1' + '|' + (str(nominas_lista[nomina]['empleado'].igss) if nominas_lista[nomina]['empleado'].igss else '') + '|' + (nominas_lista[nomina]['empleado'].primer_nombre if nominas_lista[nomina]['empleado'].primer_nombre else '')+ '|'+(nominas_lista[nomina]['empleado'].segundo_nombre if nominas_lista[nomina]['empleado'].segundo_nombre else '' ) + '|'
                datos +=  (nominas_lista[nomina]['empleado'].primer_apellido if nominas_lista[nomina]['empleado'].primer_apellido else '' )+'|' + (nominas_lista[nomina]['empleado'].segundo_apellido if nominas_lista[nomina]['empleado'].segundo_apellido else '') + '|'+ (nominas_lista[nomina]['empleado'].apellido_casada if nominas_lista[nomina]['empleado'].apellido_casada else '') + '|'
                if nominas_lista[nomina]['nominas']:
                    salario = 0
                    for n in nominas_lista[nomina]['nominas']:
                        # fecha_planilla_buscada = datetime.datetime.strptime(str(n.date_to), '%Y-%m-%d')
                        # mes_planilla_buscada = fecha_planilla_buscada.month
                        # anio_planilla_buscada = fecha_planilla_buscada.year
                        # if mes_planilla_buscada == mes_planilla and anio_planilla == anio_planilla_buscada:
                        for linea in n.line_ids:
                            if linea.code == 'SNT':
                                salario += linea.total
                datos += str(salario) + '|'

                for contrato in nominas_lista[nomina]['empleado'].contract_id:
                    if contrato.date_end:
                        mes_contrato= datetime.datetime.strptime(str(contrato.date_end), '%Y-%m-%d')
                        mes_final_contrato = mes_contrato.month
                        anio_final_contrato = mes_contrato.year
                        if mes_planilla == mes_final_contrato and anio_final_contrato == anio_planilla:
                            datos += str(datetime.datetime.strptime(str(contrato.date_start),'%Y-%m-%d').date().strftime('%d/%m/%Y')) + '|' + str(datetime.datetime.strptime(str(contrato.date_end),'%Y-%m-%d').date().strftime('%d/%m/%Y')) + '|'
                    else:
                        mes_contrato = datetime.datetime.strptime(str(contrato.date_start), '%Y-%m-%d')
                        mes_final_contrato = mes_contrato.month
                        anio_final_contrato = mes_contrato.year
                        if mes_final_contrato == mes_planilla and anio_final_contrato == anio_planilla:
                            datos += str(datetime.datetime.strptime(str(contrato.date_start),'%Y-%m-%d').date().strftime('%d/%m/%Y')) + '|' + '|'
                        else:
                            datos +='|' + '' + '|'

                datos += str(nominas_lista[nomina]['empleado'].centro_trabajo_id.codigo if nominas_lista[nomina]['empleado'].centro_trabajo_id else '' ) + '|' + str(nominas_lista[nomina]['empleado'].nit if nominas_lista[nomina]['empleado'].nit else '') + '|' + str(nominas_lista[nomina]['empleado'].codigo_ocupacion if nominas_lista[nomina]['empleado'].codigo_ocupacion else '')
                datos+= '|' + str(nominas_lista[nomina]['empleado'].condicion_laboral if nominas_lista[nomina]['empleado'].condicion_laboral else '')
                datos += '|' + '|' + '\r\n'
            datos += '[suspendidos]' + '\r\n'
            ausencia_ids = self.env['hr.holidays'].search([('state','=','validate')])
            if ausencia_ids:
                for ausencia in ausencia_ids:
                    if ausencia.holiday_status_id.name == 'IGSS':
                        ausencia_mes = int(datetime.datetime.strptime(str(ausencia.date_to),'%Y-%m-%d %H:%M:%S').date().strftime('%m'))
                        ausencia_inicio = datetime.datetime.strptime(str(ausencia.date_from),'%Y-%m-%d %H:%M:%S').date().strftime('%d/%m/%Y')
                        ausencia_fin = datetime.datetime.strptime(str(ausencia.date_to),'%Y-%m-%d %H:%M:%S').date().strftime('%d/%m/%Y')

                        ausencia_anio = int(datetime.datetime.strptime(str(ausencia.date_to),'%Y-%m-%d %H:%M:%S').date().strftime('%Y'))
                        if ausencia_mes == mes_nomina and anio_nomina == ausencia_anio:
                            logging.warn(ausencia)
                            datos += str(ausencia.employee_id.numero_liquidacion) + '|'+ str(ausencia.employee_id.igss)+'|' + ausencia.employee_id.primer_nombre + '|'+(ausencia.employee_id.segundo_nombre if ausencia.employee_id.segundo_nombre else '' )
                            datos += '|' + (ausencia.employee_id.primer_apellido if ausencia.employee_id.primer_apellido else '' )
                            datos +='|' + (ausencia.employee_id.segundo_apellido if ausencia.employee_id.segundo_apellido else '') + '|'+ (ausencia.employee_id.apellido_casada if ausencia.employee_id.apellido_casada else '') +'|'+ str(ausencia_inicio) + '|' + str(ausencia_fin)+ '\r\n'
            datos += '[licencias]' + '\r\n'
            datos += '[juramento]' + '\r\n'
            datos += 'BAJO MI EXCLUSIVA Y ABSOLUTA RESPONSABILIDAD, DECLARO QUE LA INFORMACION QUE AQUI CONSIGNO ES FIEL Y EXACTA, QUE ESTA PLANILLA INCLUYE A TODOS LOS TRABAJADORES QUE ESTUVIERON A MI SERVICIO Y QUE SUS SALARIOS SON LOS EFECTIVAMENTE DEVENGADOS, DURANTE EL MES ARRIBA INDICADO'+ '\r\n'
            datos += '[finplanilla]'
            # for nomina in w.nomina_id.slip_ids:
            #     logging.warn(nomina)

        datos = base64.b64encode(datos.encode("utf-8"))
        self.write({'archivo': datos, 'name':'igss.txt'})
        return {
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hr_gt.igss.wizard',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }



    @api.multi
    def print_report(self):
        data = {
             'ids': [],
             'model': 'hr_gt.igss.wizard',
             'form': self.read()[0]
        }
        return self.env.ref('hr_gt.action_igss').report_action(self, data=data)

    # @api.multi
    # def print_report(self):
    #     datas = {'ids': self.env.context.get('active_ids', [])}
    #     res = self.read(['nomina_ids','formato_recibo_pago_id'])
    #     res = res and res[0] or {}
    #     datas['form'] = res
    #     return self.env.ref('hr_gt.action_recibo_pago').report_action([], data=datas)
