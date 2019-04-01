# -*- coding=utf-8 -*-
import utils,time,log,re,sys,json,simplejson,random,requests
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
		
	def call_rest_api(self, API_URL, REQ_TYPE, hallCode=None, username=None,
					  		password=None, files=None,data_rtn=None, header=True,
					  		get_err_msg=True, token=None, timeout=None):
		retry_num = 1
		retry_interval_time = 10
		cnt = 0
		while cnt < retry_num:
			if token == None:
				token = self.loginYuntu()
			else:
				token = token

			headers = {
				'token': token,
				'Content-Type': 'application/json;charset=UTF-8'
			}
			try:
				if data_rtn != None:
					if REQ_TYPE == "POST":
						values = json.dumps(data_rtn)
						# obj_log.info values
						req = requests.post(API_URL, data=values, headers=headers)
						print(req)
					elif REQ_TYPE == "PUT":
						# obj_log.info API_URL
						values = json.dumps(data_rtn)
						req = requests.put(API_URL, data=values, headers=headers,timeout=timeout)

					elif REQ_TYPE == "GET":
						# obj_log.info API_URL
						req = requests.get(API_URL, params=data_rtn, headers=headers,timeout=timeout)
					elif REQ_TYPE == "DELETE":
						# obj_log.info API_URL

						req = requests.delete(API_URL, params=data_rtn, headers=headers,timeout=timeout)
				else:
					if REQ_TYPE == "POST":
						values = json.dumps(data_rtn)
						req = requests.post(API_URL, headers=headers)

					elif REQ_TYPE == "PUT":
						# obj_log.info API_URL
						req = requests.put(API_URL, headers=headers,timeout=timeout)

					elif REQ_TYPE == "GET":
						obj_log.info(API_URL)
						req = requests.get(API_URL, headers=headers, timeout=timeout)
					elif REQ_TYPE == "DELETE":
						obj_log.info(API_URL)
						req = requests.delete(API_URL, headers=headers, timeout=timeout)
			except Exception as e:
				if get_err_msg == True:
					try:
						return e.read()
					except Exception:
						return e
				continue
			if str(req.status_code) == "200":
				rtn_temp = req.text
				# rtn_temp = str(rtn_temp)
				# obj_log.info type(rtn_temp)
				rtn = json.loads(rtn_temp)
				req.close()
				return rtn
			else:
				obj_log.error("ERROR : Failed to requests API!")
				time.sleep(retry_interval_time)
				cnt += 1
				obj_log.error('retry: %d' % cnt)
				req.close()

		return False
	
		
	def loginYuntu(self, hallCode="",username = '',password=''):
		REQ_TYPE = "POST"
		temp_dict = {}
		if hallCode == "":
			temp_dict['hallCode'] = self.hallCode
		else:
			temp_dict['hallCode'] = hallCode
		if username == '':
			temp_dict['username'] = "admin"
		else:
			temp_dict['username'] = username
		temp_dict['forceLogin'] = "True"
		if password == '':
			temp_dict['password'] = self._get_libraryuser_info(hallCode)['password']
		else:
			temp_dict['password'] = password
		values = json.dumps(temp_dict)
		API_URL = "http://" + self.add + "/api/libraryuser/login"
		headers = {
			'Content-Type': 'application/json;charset=UTF-8'
		}
		req = requests.post(API_URL, data=values, headers=headers)
		if str(req.status_code) == "200":
			obj_log.info('登录图书馆{}成功.......'.format(hallCode))
			rtn_temp = req.text
			rtn = json.loads(str(rtn_temp))
			rtn = rtn['data']
			req.close()
			return rtn
		else:
			obj_log.info('登录图书馆{}失败.......'.format(hallCode))
			return False
		
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
	
	def _getReaderIdAndPassword(self, idCard):
		'''获取读者密码
		:param idCard : 身份者或者手机号
		:rtype : dict
		'''
		if len(str(idCard)) == 18:
			sql_statement = '''SELECT id,idpassword from reader WHERE idCard=''' + str(
				idCard)
		elif len(str(idCard)) == 11:
			sql_statement = '''SELECT id,idpassword from reader WHERE phone=''' + str(
				idCard)
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
		token = self.loginYuntu(hallCode, get_user, get_pwd)
		req = self.call_rest_api(API_URL, REQ_TYPE,data_rtn=temp_dict, token=token)
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
		token = self.loginYuntu(hallCode, get_user, get_pwd)
		req = self.call_rest_api(API_URL, REQ_TYPE, token=token)
		if req['status'] == 200:
			obj_log.info('获取图书馆:{}还书单号成功........'.format(hallCode))
			return req['data']
		else:
			obj_log.info('获取图书馆:{}还书单号失败........'.format(hallCode))
			return False
		return True
	
	def _get_borrowNumber(self,hallCode):
		'''获取图书馆还书单号.
		:param hallCode : 图书馆代码
		:rtype : str
		'''
		REQ_TYPE = 'GET'
		temp_dict = {}
		API_URL = "http://" + self.add + "/api/number/getBorrowNumber"
		get_user_info = self._get_libraryuser_info(hallCode)
		get_user = get_user_info['userName']
		get_pwd = get_user_info['password']
		token = self.loginYuntu(hallCode, get_user, get_pwd)
		req = self.call_rest_api(API_URL, REQ_TYPE, token=token)
		if req['status'] == 200:
			obj_log.info('获取图书馆:{}借书单号成功........'.format(hallCode))
			return req['data']
		else:
			obj_log.info('获取图书馆:{}借书单号失败........'.format(hallCode))
			return False
		return True

	def _get_userborrowlist(self,idCard):
		'''获取图书馆还书单号.
		:param idcard : 读者身份证
		:rtype : list
		'''
		if len(str(idCard)) == 18:
			sql_statement = '''SELECT DATE_FORMAT(borrowTime,'%Y-%m-%d %H:%i:%S'),
								limit_borrow_days,
								hallCode,
								belongLibraryHallCode,
								barNumber
							FROM
								library_borrower_books
							WHERE
								reader_id=(SELECT id from reader WHERE idCard=''' + str(
				idCard) + ''') and  borrowState=5'''
		elif len(str(idCard)) == 11:
			sql_statement = '''SELECT DATE_FORMAT(borrowTime,'%Y-%m-%d %H:%i:%S'),
								limit_borrow_days,
								hallCode,
								belongLibraryHallCode,
								barNumber
									FROM
										library_borrower_books
									WHERE
									reader_id=(SELECT id from reader WHERE phone=''' + str(
				idCard) + ''') and  borrowState=5'''
		else:
			obj_log.info("idCard或者手机号输入错误，请检查！")
			return False
		sql_rtn = self.obj_tools.sql_event(sql_statement)
		if len(sql_rtn) == 0:
			print("当前读者没有在借书籍！")
		return sql_rtn
	
	def _getReaderLoginInfo(self,condition,hallCode):
		'''获取读者登录时的信息.
		:param hallCode : 图书馆馆号
		:param condition : 读者身份证或者手机号
		:rtype : dict
		'''
		REQ_TYPE = 'POST'
		temp_dict = {}
		temp_dict['condition'] = condition
		temp_dict['password'] = self._getReaderIdAndPassword(condition)['idpassword']
		API_URL = "http://" + self.add + "/api/libraryreader/login"
		token = self.loginYuntu(hallCode)
		req = self.call_rest_api(API_URL, REQ_TYPE,data_rtn=temp_dict, token=token)
		if req['status'] == 200:
			obj_log.info('获取读者{}在图书馆{}的登录信息成功........'.format(condition,hallCode))
			return req['data']
		else:
			obj_log.info('获取读者{}在图书馆{}的登录信息失败........'.format(condition,hallCode))
			return False

		return req['data']
	
	def _getReaderInfoWithHallCode(self,idCard,hallCode):
		'''获取读者登录图书馆的的信息（可借数量，已借书量，图书馆协议等）.
		:param hallCode : 图书馆馆号
		:param idCard : 读者身份证或者手机号
		:rtype : dict
		'''
		REQ_TYPE = 'GET'
		temp_dict = {}
		temp_dict['depositUsedType'] = 1
		reader_id = self._getReaderIdAndPassword(idCard)['id']
		API_URL = "http://" + self.add + "/api/libraryreader/" + str(reader_id)
		token = self.loginYuntu(hallCode)
		req = self.call_rest_api(API_URL, REQ_TYPE,data_rtn=temp_dict, token=token)
		if req['status'] == 200:
			obj_log.info('获取读者{}在图书馆{}的信息成功........'.format(idCard,hallCode))
			return req['data']
		else:
			obj_log.info('获取读者{}在图书馆{}的信息失败........'.format(idCard,hallCode))
			return False

		return req['data']
	
	def _getHandlePenaltyInfo(self,idCard,hallCode):
		'''
		 获取读者罚金信息，如果能够处理执行处理操作
		:param
		:return:
		'''
		REQ_TYPE = "PUT"
		reader_id = self._getReaderIdAndPassword(idCard)['id']
		API_URL = "http://" + self.add + "/api/libraryreader/" + str(reader_id) + "/handlePenaltyAlone"
		token = self.loginYuntu(hallCode)
		req = self.call_rest_api(API_URL, REQ_TYPE, token=token)
		if req['status'] == 200:
			obj_log.info('获取读者{}在图书馆{}的信息成功........'.format(idCard, hallCode))
			return req['data']
		else:
			obj_log.info('获取读者{}在图书馆{}的信息失败........'.format(idCard, hallCode))
			return False
		
	def _penalty_free(self,idCard,hallCode):
		'''
		 提交免单申请
		:param idCard
		:return:
		'''
		REQ_TYPE = "PUT"
		temp_dict = {}
		temp_dict['readerId'] = self._getReaderIdAndPassword(idCard)['id']
		temp_dict['operCode'] = self._get_returnNumber(hallCode)
		temp_dict['applyRemark'] = "测试免单"
		API_URL = "http://" + self.add + "/api/penaltyfree/applyPenaltyFree"
		token = self.loginYuntu(hallCode)
		req = self.call_rest_api(API_URL, REQ_TYPE,data_rtn=temp_dict,token=token)
		if req['status'] == 200:
			obj_log.info('读者{}在图书馆{}提交免单申请成功........'.format(idCard, hallCode))
			return True
		else:
			obj_log.info('读者{}在图书馆{}提交免单申请失败........'.format(idCard, hallCode))
			return False
		
	def _getLibraryBookId(self,barNumberList):
		'''
		 获取图书libraryBookId
		:param barNumberList
		:return: list
		'''
		library_bookId_list = []
		for barNumber in barNumberList:
			sql_statement = '''SELECT id from library_books where	full_bar_number = "''' + str(barNumber).strip() + '''"'''
			sql_rtn = self.obj_tools.sql_event(sql_statement)
			library_bookId_list.append(sql_rtn[0]['id'])
		return library_bookId_list
	
	def _behalfPay(self,idCard,hallCode,amount,index):
		'''
		 图书馆代缴押金
		:param idCard
		:param index index=1,使用备用金账户代充共享押金,2:馆押金
		:return:
		'''
		REQ_TYPE = "PUT"
		temp_dict = {}
		reader_id= self._getReaderIdAndPassword(idCard)['id']
		temp_dict['accountType'] = {"index":index}
		temp_dict['amount'] = amount
		temp_dict['operOrder'] = self._get_borrowNumber(hallCode)
		API_URL = "http://" + self.add + "/api/libraryreader/" + str(reader_id)+ "/behalfPay"
		token = self.loginYuntu(hallCode)
		req = self.call_rest_api(API_URL, REQ_TYPE,data_rtn=temp_dict,token=token)
		if req['status'] == 200:
			obj_log.info('读者{}在图书馆{}充值{}元成功........'.format(idCard, hallCode, amount))
			return True
		else:
			obj_log.info('读者{}在图书馆{}充值{}元失败........'.format(idCard, hallCode, amount))
			return False
		
	def _getBorrowBookByHallCodeAndBarNumber(self,stayLibraryHallCode,barNumber,idCard):
		'''
		获取所借图书图书信息（是否需要押金等）
		:param stayLibraryHallCode ：所在馆
		:param barNumber
		:param readerId
		:rtype: dict
		'''
		REQ_TYPE = "GET"
		temp_dict = {}
		reader_id= self._getReaderIdAndPassword(idCard)['id']
		temp_dict['stayLibraryHallCode'] = stayLibraryHallCode
		temp_dict['barNumber'] = barNumber
		temp_dict['readerId'] = reader_id
		API_URL = "http://" + self.add + "/api/librarybook/getBorrowBookByHallCodeAndBarNumber"
		token = self.loginYuntu(stayLibraryHallCode)
		req = self.call_rest_api(API_URL, REQ_TYPE,data_rtn=temp_dict,token=token)
		if req['status'] == 200:
			obj_log.info('读者{}在图书馆{}获取图书{}成功........'.format(idCard, stayLibraryHallCode, barNumber))
			return req['data']
		else:
			obj_log.info('读者{}在图书馆{}获取图书{}失败........'.format(idCard, stayLibraryHallCode, barNumber))
			return False
		
	def _checkAndHandlePenalty(self,idCard,hallCode):
		'''
		检查读者在图书馆是否有罚金，并处理
		:param hallCode ：所在馆
		:param idCard
		:rtype: dict
		'''
		reader_info = self._getReaderInfoWithHallCode(idCard, hallCode)
		get_reader_penalty = self._getHandlePenaltyInfo(idCard, hallCode)
		penalty = get_reader_penalty['failPenalty'] - reader_info['readerDeposit']['onlineDeposit'][
			'availableBalance']
		penalty = float('%.2f' % penalty)
		if reader_info["hasAgreement"] == 1 or reader_info["hasAgreement"] == 2:
			obj_log.info("一级协议和二级协议均按照在二级协议馆AAGYC代充方式处理！")
			# put_penalty_free = self._penalty_free(idCard,hallCode)
			behalf_pay = self._behalfPay(idCard=idCard, hallCode="AAGYC", amount=penalty, index=1)
			get_reader_penalty = self._getHandlePenaltyInfo(idCard, hallCode)
			obj_log.info("处理读者{}罚金{}成功".format(idCard,penalty))
		else:
			obj_log.info("三级协议四级协议均按照在图书馆交押金方式处理！")
			penalty = get_reader_penalty['failPenalty'] - reader_info['readerDeposit']['offlineDeposit'][
				'availableBalance']
			penalty = float('%.2f' % penalty)
			# 交押金
			behalf_pay = self._behalfPay(idCard=idCard, hallCode=hallCode, amount=penalty, index=2)
			# 处理罚金
			get_reader_penalty = self._getHandlePenaltyInfo(idCard, hallCode)
			obj_log.info("处理读者{}罚金{}成功".format(idCard, penalty))
		return True
	
	def _getLoginUserInfo(self,hallCode):
		'''
		:param hallCode
		管理员登陆管理系统后获取的图书馆配置信息
		:rtype: dict
		'''
		REQ_TYPE = "GET"
		API_URL = "http://" + self.add + "/api/libraryuser/getLoginUserInfo"
		token = self.loginYuntu(hallCode)
		req = self.call_rest_api(API_URL, REQ_TYPE,token=token)
		if req['status'] == 200:
			obj_log.info('获取图书馆{}配置信息成功........'.format(hallCode))
			return req['data']
		else:
			obj_log.info('获取图书馆{}配置信息成功........'.format(hallCode))
			return False