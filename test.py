# -*- coding=utf-8 -*-
import qrcode
from PIL import Image
import matplotlib.pyplot as plt
def qrcode_make(data_list):
	'''二维码生成器.
	:param data : list,生成内容
	'''
	qr = qrcode.QRCode(
		version=1,
		error_correction=qrcode.constants.ERROR_CORRECT_H,
		box_size=5,
		border=1
	)
	for i in data_list:
		qr.add_data(i)
		qr.make(fit=True)
		img = qr.make_image()
		img.save("img\%s.png"%(i))
		# img.show()
		pic = Image.open("img\%s.png"%(i))
		plt.figure(figsize=(2,2),dpi=100)
		plt.axis('off') #关掉axis（尺寸）
		plt.imshow(pic)
		plt.show()
		plt.close


temp = ["nihao","222"]
qrcode_make(temp)