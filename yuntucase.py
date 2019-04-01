# -*- coding=utf-8 -*-
import sys,utils,unittest,runner,log,time,HTMLTestRunner,os
from test_case import Test_case
import test_case
from selenium import webdriver
to_list = ["18782019436@163.com"]
obj_log = log.get_logger()
log_file = (os.path.split(os.path.realpath(__file__)))[0] + '\\' + 'log\yuntu.log'
fp = open(log_file,'w')
class Yuntu_case(unittest.TestCase):
	@classmethod
	def setUp(self):
		self.obj_test_case = Test_case(all_config)
	@classmethod
	def tearDown(self):
		# driver.close()
		pass
	def books_borrow(self):
		obj_log.info('借书开始................')
		self.assertEqual(self.obj_test_case.borrow_books(hallCode='AGZH',idCard='13980004762',num=2,byHallCode=1), True)
	def books_return(self):
		obj_log.info('还书开始................')
		self.assertEqual(self.obj_test_case.return_books(idCard=13980004762,isPenalty=True,overduedays=50), True)

def suite():
	suite = unittest.TestSuite()
	suite.addTest(Yuntu_case("books_borrow"))
	# suite.addTest(Yuntu_case("books_return"))
	return suite

if __name__ == '__main__':
	obj_tools = utils.Tools()
	all_config = obj_tools.all_config

	'''测试报告生成'''
	now_time = time.strftime("%Y%m%d%H%M", time.localtime(time.time()))
	# filename = (os.path.split(os.path.realpath(__file__)))[0] + '\\Report\\'+ now_time  + r'testReport.html'
	# fip = open(filename, 'wb')
	# unitrunner = HTMLTestRunner.HTMLTestRunner(
	# 	stream=fip,
	# 	title=u'云图测试报告',
	# 	description=u'测试用例详细信息'
	# )
	unitrunner = unittest.TextTestRunner()

	rtn1 = unitrunner.run(suite())
	fp.close()
	# html_report = fip.name
	'''邮件发送'''
	# sendmail = obj_tools.send_mail(to_list,html_report)
	print('Test Result:', rtn1)
