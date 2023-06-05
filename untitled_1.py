from Maix import GPIO, I2S,  FFT
import image, lcd, math
from fpioa_manager import fm
import KPU as kpu

############################################USART的初始化began
import struct

from fpioa_manager import fm
from machine import UART
fm.register(15, fm.fpioa.UART1_TX, force=True)


fm.register(17, fm.fpioa.UART1_RX, force=True)
uart = UART(UART.UART1, 115200, 8, 0, 1, timeout=1000, read_buf_len=4096)
############################################USART的初始化end

############################################发送数据区域began
def send_int_data(int_data_list):
    frame_header = 0xAA
    frame_footer = 0xBB
    # 构造数据包
    # 'i' 表示一个整数，'<' 表示使用小端字节序
    freq_bytes = struct.pack('<i', int_data_list)

    packet = bytes([0xAA]) + freq_bytes + bytes([0xCC])

    uart.write(packet)
    print(packet)

############################################发送数据区域end



# 设置采样率和采样点数
sample_rate = 32000
sample_points = 1024
fft_points = 512
hist_x_num = 128

lcd.init()
# close WiFi
# 关闭 WiFi，节省电力并防止干扰
fm.register(8,  fm.fpioa.GPIO0)
wifi_en=GPIO(GPIO.GPIO0,GPIO.OUT)
wifi_en.value(0)
# 配置 I2S 接口
fm.register(20,fm.fpioa.I2S0_IN_D0)
fm.register(30,fm.fpioa.I2S0_WS)    # 30 on dock/bit Board
fm.register(32,fm.fpioa.I2S0_SCLK)  # 32 on dock/bit Board
# 初始化 I2S 设备
rx = I2S(I2S.DEVICE_0)
rx.channel_config(rx.CHANNEL_0, rx.RECEIVER, align_mode = I2S.STANDARD_MODE)
rx.set_sample_rate(sample_rate)
# 初始化一个 128x128 的灰度图像
img = image.Image(size=(128,128))
img=img.to_grayscale()


while True:
# 从 I2S 设备录制音频
    audio = rx.record(sample_points)
     # 对音频数据进行 FFT 转换
    fft_res = FFT.run(audio.to_bytes(),fft_points)
     # 获取 FFT 转换的幅度
    fft_amp = FFT.amplitude(fft_res)

# 获取最大频率
    max_freq = fft_amp.index(max(fft_amp))
    # 计算实际的最大频率
    actual_freq = max_freq * sample_rate / sample_points * fft_points / hist_x_num
    avg_freq_int = int(actual_freq)
    # 打印平均频率

    print('Max frequency: {} Hz'.format(actual_freq))

    send_int_data(avg_freq_int)



     # 将图像向上移动一行
    img_tmp = img.cut(0,0,128,127)

    img.draw_image(img_tmp, 0,1)
     # 将 FFT 转换的幅度绘制到图像的最后一行
    for i in range(hist_x_num):
        img[i] = fft_amp[i]
    del(img_tmp)
    # 将灰度图像转换为彩虹色彩图像
    imgc = img.to_rainbow(1)
     # 在 LCD 上显示彩色图像
    lcd.display(imgc)
    # 释放内存
    del(imgc)
    fft_amp.clear()
