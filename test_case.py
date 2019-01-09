# -*- coding=utf-8 -*-
import utils,runner,log,time,json,simplejson
obj_tools = utils.Tools()
obj_log = log.get_logger()
isbn_list = {'A': '9787308156417', 'B': '9787516143261', 'C': '9787509745816', 'D': '9787040213607', 'E': '9787509755280', 'F': '9787516410790', 'G': '9787561466584',
			 'H': '9787561460207', 'I': '9787108032911', 'J': '9787561460232', 'K': '9787509748985','N': '9787030334282', 'O': '9787513535663', 'P': '9787500672012',
			 'Q': '9787502554774', 'R': '9787200008715', 'S': '9787030323859', 'T': '9787121212437', 'U': '9787111465300', 'V': '9787515901701', 'X': '9787511107633',
			 'Z': '9787500086062', 'Test_null': '123456789'}
class Test_case(runner.Runner):
	def __init__(self, all_config):
		runner.Runner.__init__(self, all_config)
	def borrow_books(self,hallCode,byHallCode=1):
		get_allbooks_rtn = self._get_librarybooks(hallCode,byHallCode=byHallCode)
		print(get_allbooks_rtn)
		if len(get_allbooks_rtn) >= 5:
			qr_show = obj_tools.qrcode_make(get_allbooks_rtn[:5])
		else:
			qr_show = obj_tools.qrcode_make(get_allbooks_rtn)


	def return_books(self,idCard,hallCode=None):
		'''图书馆还书.
		:param hallCode : 图书馆代码
		:rtype : str
		'''
		REQ_TYPE = 'POST'
		temp_dict = {}
		return_list = self._get_userborrowlist(idCard)

		for temp in return_list:
			if hallCode is None:
				return_hallCode = temp['hallCode']
			else:
				return_hallCode = hallCode
			return_number = self._get_returnNumber(return_hallCode)
			bar_number =" " + temp['belongLibraryHallCode'] + "-" + temp['barNumber']
			temp_dict['barNumber'] = bar_number
			temp_dict['returnNumber'] = return_number
			API_URL = "http://" + self.add + "/api/libraryreader/returnBook"
			get_user_info = self._get_libraryuser_info(return_hallCode)
			get_user = get_user_info['userName']
			get_pwd = get_user_info['password']
			token = self.obj_tools.loginYuntu(return_hallCode, get_user, get_pwd)
			req = self.obj_tools.call_rest_api(API_URL, REQ_TYPE,data_rtn=temp_dict,token=token)
			if req['status'] == 200:
				obj_log.info('图书馆:{}还书:{}成功........'.format(return_hallCode,bar_number))
			else:
				obj_log.info('图书馆:{}还书:{}失败........'.format(return_hallCode,bar_number))
				return False

		return True
		

