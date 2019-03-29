# -*- coding=utf-8 -*-
import utils,runner,log,time,json,simplejson,datetime
obj_tools = utils.Tools()
obj_log = log.get_logger()
isbn_list = {'A': '9787308156417', 'B': '9787516143261', 'C': '9787509745816', 'D': '9787040213607', 'E': '9787509755280', 'F': '9787516410790', 'G': '9787561466584',
			 'H': '9787561460207', 'I': '9787108032911', 'J': '9787561460232', 'K': '9787509748985','N': '9787030334282', 'O': '9787513535663', 'P': '9787500672012',
			 'Q': '9787502554774', 'R': '9787200008715', 'S': '9787030323859', 'T': '9787121212437', 'U': '9787111465300', 'V': '9787515901701', 'X': '9787511107633',
			 'Z': '9787500086062', 'Test_null': '123456789'}
class Test_case(runner.Runner):
	def __init__(self, all_config):
		runner.Runner.__init__(self, all_config)
	def borrow_books(self,idCard,hallCode,num,byHallCode=1):
		'''图书馆借书.
		:param hallCode : 图书馆代码
		:param idCard : 身份证或者手机号
		:param num : 借书数量
		:param byHallCode : 1: 本馆 2：异馆（也可以直接跟馆号）
		:rtype : str
		'''
		REQ_TYPE = "POST"
		temp_dict={}
		deposit_count = 0
		reader_login_info = self._getReaderLoginInfo(condition=idCard,hallCode=hallCode)
		reader_info = self._getReaderInfoWithHallCode(idCard,hallCode)
		can_borrow_num = reader_info["canBorrowNum"]
		if can_borrow_num < num:
			obj_log.info("预期借阅数量{}小于可借数量{}，将执行归还所有书籍操作.".format(num,can_borrow_num))
			obj_log.info('还书开始................')
			return_books = self.return_books(idCard)
		# 检查是否有罚金
		get_reader_penalty = self._getHandlePenaltyInfo(idCard, hallCode)
		if get_reader_penalty['succeedPenalty'] != 0:
			obj_log.info("读者{}在图书馆{}交罚金{}成功.".format(idCard, hallCode, get_reader_penalty['succeedPenalty']))
		if get_reader_penalty['failPenalty'] != 0:
			obj_log.info("读者{}在图书馆{}欠罚金{}.".format(idCard, hallCode, get_reader_penalty['failPenalty']))
			handle_penalty = self._checkAndHandlePenalty(idCard,hallCode)
		
		# 获取图书馆可借图书
		bookBar_list = self._get_librarybooks(hallCode,byHallCode=byHallCode)[:num]
		if len(bookBar_list) == 0:
			raise Exception("图书馆{}没有可借书籍.".format(hallCode))
		print("待借书籍：{}".format(bookBar_list[:num]))
		
		#判断读者押金是否足够
		#获取所借书籍的押金
		for barNumber in bookBar_list:
			get_bookinfo = self._getBorrowBookByHallCodeAndBarNumber(hallCode,barNumber,idCard)
			deposit = get_bookinfo['deposit']
			deposit = float('%.2f' % deposit)
			deposit_count = deposit_count + deposit
		#一级协议只能用线上押金借书
		reader_info = self._getReaderInfoWithHallCode(idCard,hallCode)
		if reader_info["hasAgreement"] == 1:
			onlineDeposit = reader_info['readerDeposit']['onlineDeposit']['availableBalance']
			obj_log.info("读者{}线上押金{}元.".format(idCard,onlineDeposit))
			if onlineDeposit < deposit_count:
				need_handle_deposit = deposit_count - onlineDeposit
				need_handle_deposit = float('%.2f' % need_handle_deposit)
				obj_log.info("图书总共需要押金{}元".format(deposit_count))
				obj_log.info("押金不足，一级协议按照在二级协议馆AAGYC代充方式交线上押金！")
				behalf_pay = self._behalfPay(idCard=idCard, hallCode="AAGYC", amount=need_handle_deposit, index=1)
		# 二级协议能用线上押金和馆押金，不能混用，只能选择一种
		elif reader_info["hasAgreement"] == 2 or reader_info["hasAgreement"] == 3:
			onlineDeposit = reader_info['readerDeposit']['onlineDeposit']['availableBalance']
			offlineDeposit = reader_info['readerDeposit']['offlineDeposit']['availableBalance']
			obj_log.info("读者{}线上押金{}元,在图书馆{}馆押金{}元".format(idCard, onlineDeposit,hallCode,offlineDeposit))
			if onlineDeposit < deposit_count and offlineDeposit < deposit_count:
				obj_log.info("图书总共需要押金{}元".format(deposit_count))
				obj_log.info("押金不足，读者线上与线下的押金都不足，采用在图书馆交馆押金的方式借书.")
				need_handle_deposit = deposit_count - offlineDeposit
				need_handle_deposit = float('%.2f' % need_handle_deposit)
				behalf_pay = self._behalfPay(idCard=idCard, hallCode=hallCode, amount=need_handle_deposit, index=2)
		else:
			offlineDeposit = reader_info['readerDeposit']['offlineDeposit']['availableBalance']
			obj_log.info("读者{}在图书馆{}馆押金{}元.".format(idCard, hallCode, offlineDeposit))
			if offlineDeposit < deposit_count:
				obj_log.info("读者线下的押金都不足，采用在图书馆交馆押金的方式借书.")
				need_handle_deposit = deposit_count - offlineDeposit
				need_handle_deposit = float('%.2f' % need_handle_deposit)
				behalf_pay = self._behalfPay(idCard=idCard, hallCode=hallCode, amount=need_handle_deposit, index=2)
		# 生成图书条码号对应的二维码
		# if len(get_allbooks_rtn) >= 5:
		# 	qr_show = obj_tools.qrcode_make(get_allbooks_rtn[:5])
		# else:
		# 	qr_show = obj_tools.qrcode_make(get_allbooks_rtn)
		temp_dict['bookIds'] = self._getLibraryBookId(bookBar_list)
		temp_dict['borrowNumber'] = self._get_borrowNumber(hallCode)
		reader_id = self._getReaderIdAndPassword(idCard)['id']
		API_URL = "http://" + self.add + "/api/libraryreader/" + str(reader_id) + "/borrowBooks"
		token = self.loginYuntu(hallCode)
		req = self.call_rest_api(API_URL, REQ_TYPE, data_rtn=temp_dict, token=token)
		if req['status'] == 200:
			obj_log.info('读者{}在图书馆:{}借书:{}成功........'.format(idCard, hallCode, bookBar_list))
		else:
			obj_log.info('读者{}在图书馆:{}借书:{}失败........'.format(idCard, hallCode, bookBar_list))
			obj_log.info(req)
			return False
		return True


	def return_books(self,idCard,isPenalty=False, overduedays=10, hallCode=None):
		'''图书馆还书.
		:param hallCode : 图书馆代码
		:param overduedays : 逾期天数
		:rtype : str
		'''
		REQ_TYPE = 'POST'
		temp_dict = {}
		return_list = self._get_userborrowlist(idCard)
		# 逾期天数默认值为10
		if isPenalty:
			obj_log.info("开始修改借书时间为逾期{}天..........".format(overduedays))
			for book in return_list:
				delta_days = overduedays + (book['limit_borrow_days']) - 1
				time_temp = datetime.datetime.now()
				delta = datetime.timedelta(days=delta_days)
				n_days = time_temp - delta
				days_temp = n_days.strftime('%Y-%m-%d %H:%M:%S')
				update_statement = '''UPDATE library_borrower_books
										SET borrowTime = ''' + "'" + str(days_temp) + "'" + '''
										WHERE
											belongLibraryHallCode = ''' + "'" + str(book['belongLibraryHallCode']) + "'" + '''
										AND barNumber = ''' + book['barNumber']
				change_borrowdays = self.obj_tools.sql_event(update_statement)
				obj_log.info("修改书籍：{}-{}借书时间为：{}成功.".format(book['belongLibraryHallCode'], book['barNumber'], days_temp))
		else:
			obj_log.info("正常还书，未修改借书时间..........")
		
		
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
			token = self.loginYuntu(return_hallCode, get_user, get_pwd)
			req = self.call_rest_api(API_URL, REQ_TYPE,data_rtn=temp_dict,token=token)
			if req['status'] == 200:
				obj_log.info('图书馆:{}还书:{}成功........'.format(return_hallCode,bar_number))
			else:
				obj_log.info('图书馆:{}还书:{}失败........'.format(return_hallCode,bar_number))
				return False

		return True
		

