# -*- coding=utf-8 -*-
import utils,time,log,re,sys,json,simplejson,random
obj_log = log.get_logger()

class Runner:
	def __init__(self, all_config):
		self.obj_tools = utils.Tools()
		# self.hallCode =  self.obj_utils.hallCode
		self.user = all_config['username']
		self.pwd = all_config['pwd']
		self.port = all_config['port']
		self.ip = all_config['ip']
		self.my_user1 = all_config['my_user1']
		self.my_pwd1 = all_config['my_pwd1']
		self.add = self.obj_tools.add
	def _get_libraryuser_info(self,hallCode):
		'''获取图书馆admin账号密码
		:param hallCode : 图书馆代码
		:rtype : dict
		'''
		hallCode = hallCode.upper()
		sql_statement = '''SELECT id,
							userName,
							password
						FROM
							librarys_users
						WHERE
							libraryHallCode = "''' +  hallCode + '''" AND isManager = 1
							AND isEffective = 1'''
		sql_rtn = self.obj_tools.sql_event(sql_statement)
		return sql_rtn[0]

	def _get_librarybooks(self,hallCode,bookState=1,byHallCode=1,storeroom=2):
		'''获取图书馆图书.
		:param hallCode : 图书馆代码
		:param byHallCode : 本馆： 1，异馆：2 /馆号
		:param bookState : 图书状态 1：在馆 2：在借 and so on
		:rtype : dict
		'''
		REQ_TYPE = 'GET'
		temp_dict = {}
		books_list = []
		full_barnumber_list = []
		temp_dict['byHallCode'] = byHallCode
		if byHallCode == 1:
			temp_dict['storeroom'] = storeroom
		temp_dict['bookState'] = bookState
		temp_dict['hallCode'] = hallCode
		API_URL = "http://" + self.add + "/api/statistics/getLibraryStatics"
		get_user_info = self._get_libraryuser_info(hallCode)
		get_user = get_user_info['userName']
		get_pwd = get_user_info['password']
		token = self.obj_tools.loginYuntu(hallCode, get_user, get_pwd)
		req = self.obj_tools.call_rest_api(API_URL, REQ_TYPE,data_rtn=temp_dict, token=token)
		if req['status'] == 200:
			obj_log.info('获取图书馆:{}书籍成功........'.format(hallCode))
			books_list = req['data']['resultList']
			for temp in books_list:
				full_barnumber_temp =" " + temp["belongLibraryHallCode"] + "-"  + temp["barNumber"]
				# full_barnumber_temp = temp["belongLibraryHallCode"] + "-"  + temp["barNumber"]
				full_barnumber_list.append(full_barnumber_temp)
			return  full_barnumber_list
		else:
			obj_log.info('获取图书馆:{}书籍失败........'.format(hallCode))
			return False

		return first_category_rtn

	def _get_returnNumber(self,hallCode):
		'''获取图书馆还书单号.
		:param hallCode : 图书馆代码
		:rtype : str
		'''
		REQ_TYPE = 'GET'
		temp_dict = {}
		API_URL = "http://" + self.add + "/api/number/getReturnNumber"
		get_user_info = self._get_libraryuser_info(hallCode)
		get_user = get_user_info['userName']
		get_pwd = get_user_info['password']
		token = self.obj_tools.loginYuntu(hallCode, get_user, get_pwd)
		req = self.obj_tools.call_rest_api(API_URL, REQ_TYPE, token=token)
		if req['status'] == 200:
			obj_log.info('获取图书馆:{}还书单号成功........'.format(hallCode))
			return req['data']
		else:
			obj_log.info('获取图书馆:{}还书单号失败........'.format(hallCode))
			return False

		return False

	def _get_userborrowlist(self,idCard):
		'''获取图书馆还书单号.
		:param idcard : 读者身份证
		:rtype : list
		'''
		if len(str(idCard)) == 18:
			sql_statement = '''SELECT hallCode,belongLibraryHallCode,barNumber
							from library_borrower_books 
							WHERE idCard=''' + str(idCard) + ''' and  borrowState=5'''
		elif len(str(idCard)) == 11:
			sql_statement = '''SELECT hallCode,
										belongLibraryHallCode,
										barNumber
									FROM
										library_borrower_books
									WHERE
										idCard = (
											SELECT
												idCard
											FROM
												reader
											WHERE
												phone = ''' + str(idCard) + '''
										)
									AND borrowState = 5'''
		else:
			obj_log.info("idCard或者手机号输入错误，请检查！")
			return False
		sql_rtn = self.obj_tools.sql_event(sql_statement)
		return sql_rtn