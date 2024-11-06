from machine import Pin,reset,Timer,I2C,ADC
import time
import network
import socket
import io
import gc,json
import binascii
import deflate, io
mapA2={ "lamp":0, \
        "sensoradc":0, \
        "sensorbin":0, \
        "mode":"manOff"}

#---------------------------
# Обработчик прерывания нажатия кнопки включения
def ledOn(pin):
    mapA2["mode"]="manOn"
    mapA2["lamp"]=1
    led.value(1)
    return
#-------------------------------------------------
# обработчик кнопки выключения
def ledOff(pin):
    mapA2["mode"]="manOff"
    mapA2["lamp"]=0
    led.value(0)
    return
#-------------------------------
# обработчик кнопки авто включения
#countLed=0 # счетчик срабатывания включения
def autoMode(pin):
    mapA2["mode"]="auto"
    if (sensor.value()==1):
        mapA2["lamp"]=1
        led.value(1)
    else:
        mapA2["lamp"]=0
        led.value(0)
    return 
 
def autoEn(t):
    #print("timer1")
    mapA2["sensoradc"]=sensorAdc.read_uv() // 1000
    mapA2["sensorbin"]=sensor.value()
    #print(f"SensorTim= {s//1000} mV")
    if (mapA2["mode"]=="auto"):
        if (mapA2["sensorbin2"]==1):
            mapA2["lamp"]=1
            led.value(1)
        else:
            mapA2["lamp"]=0
            led.value(0)
    elif (mapA2["mode"]=="manOn"):
        mapA2["lamp"]=1
        led.value(1)
    else:
        mapA2["lamp"]=0
        led.value(0)
    return
   
    


if __name__ == "__main__":
    time.sleep(2)
    # инициализация пинов
    sensor=Pin(35, Pin.IN, Pin.PULL_UP) # Датчик света
    butOff = Pin(12, Pin.IN)  # Выключение светодиода
    butAuto = Pin(13, Pin.IN)  # Включение автоматического режима
    butOn = Pin(14, Pin.IN)    # Включение светодиода
    led=Pin(2,Pin.OUT)
    sensorAdc=ADC(Pin(32))
    sensorAdc.atten(ADC.ATTN_11DB)
    s=sensorAdc.read()
    print(sensorAdc.read_uv())
    # -- регистрация прерываний по нажатию кнопки
    butOff.irq(handler=ledOff, trigger=Pin.IRQ_FALLING)
    butAuto.irq(handler=autoMode, trigger=Pin.IRQ_FALLING)
    butOn.irq(handler=ledOn, trigger=Pin.IRQ_FALLING)
    # регистрация прерываний таймер
    tim1 = Timer(1)
    tim1.init(period=500, mode=Timer.PERIODIC, callback=autoEn)
    # инициализируем пин для управления светодиодом
    #led=Pin(2,Pin.OUT)
    led.off()
    i2c = I2C(0, scl=Pin(18), sda=Pin(19), freq=100000)    
    #Настройка точки доступа
    ap_if = network.WLAN(network.AP_IF)
    ap_if.active(True)
    ap_if.config(essid="MyPoint", password="12345678")
    #Настройка проверки пароля точки доступа
    #ap_if.config(authmode=network.AUTH_WPA_WPA2_PSK)
    # Создание сервера
    
    while ap_if.active() == False:
      pass
    print('Connection successful')
    print(ap_if.ifconfig())
    # создаем сокет для прием сообщений
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(('', 80))
    except OSError:
        reset()
    s.listen(5)
    while True:
        if gc.mem_free() < 80000:
            gc.collect()
        # ожидаем входящих сообщений
        conn, addr = s.accept()
        data=time.localtime()
        print(f"Время {data[3]:02d}:{data[4]:02d}:{data[5]:02d}")
        mem=gc.mem_free()
        print(f"Осталось памяти начало {mem}")
        #print(f"Got a connection from {str(adr)}")
        request = conn.recv(4096)
        
        # переводим из бинарного формата в строку
        request=request.decode('UTF-8')
        # печатаем входящий запрос
        #print(request)
        request=request.split();
        print(request)
        conn.send('HTTP/1.1 200 OK\n')
        conn.send('Content-Type: text/html\n')
        conn.send('Connection: close\n\n')
        #-------------------------------------------------------
        #-------------------------------------------------------
        FileSend={  "send":False, # Заполняем что необходимо отправить данные на сервер
                    "typefile":"r", # если тип данных текстовый html,js, css то "r", иначе бинарный "rb"
                    "namefile":"",   #  имя файла для отправки
                    "sizeblock": 8192 # размер блока для отправки
                   }
        # проверяем что данные для парсинга 
        try:
            if (request[0]=="GET"):
                pass
        except:
            mem=gc.mem_free()
            print(f"Осталось памяти в конце {mem}")
            del request
            conn.close()
            print("Ошибка запроса")
            continue
        # Парсим данные для отправи файлов
        if (request[0]=="GET"):
            
            if (request[1]=="/"):
                FileSend["send"]=True
                FileSend["typefile"]="r"
                FileSend["namefile"]="/index.html"
            elif (request[1].find(".html")>0 ) or \
                (request[1].find(".js")>0 ) or \
                (request[1].find(".css")>0 ):
                # отрправляем данные в текстовом режиме 
                FileSend["send"]=True
                FileSend["typefile"]="r"
                FileSend["namefile"]=request[1]
                
            elif (request[1].find(".png")>0 ) or \
                 (request[1].find(".jpg")>0 ) or \
                 (request[1].find(".ico")>0 ):
                # отрправляем данные в данные бинарном режиме 
                FileSend["send"]=True
                FileSend["typefile"]="rb"
                FileSend["namefile"]=request[1] # отбрасываем косую черту
        # обработка данных из        
        elif (request[0]=="POST"):
            # заменяем символы unicode на соответсующие символы
            request[1]=request[1].replace("%7B","{")
            request[1]=request[1].replace("%7D","}")
            request[1]=request[1].replace("%22",'"')
            request[1]=request[1].replace("%20"," ")
            print(f"Запрос: {request[1]}")
            #request[1]=request[1][1:]     # Удаляем первый символ косая черта
            requestJSON=request[1].split() # Делим строку на вид запроса и данные JSON
            #print(requestJSON)
            print(f"Запрос: {requestJSON}")
            # обрабатываем данные
            st=""
            if (requestJSON[0]=="/readData"):
                #print(mapA2)
                # преобразуем в текст для отправки
                st=json.dumps(mapA2)
            elif (requestJSON[0]=="/sendData"):
                mapA2send=json.loads(requestJSON[1])
                print("Приняты данные для отправки")
                #print(mapA2send)
                
                st=json.dumps(mapA2)
            # отправка данных
            if (len(st)>0):
                try:
                    conn.sendall(st)
                    del st
                except:
                    print("Ошибка отправки данных-377")
                    print(st)
        
        #-------- данные для обработки не получены
        else:
            print("Запрос отклонен")
        #----Отправка файла-----
        if (FileSend["send"]):
            try:
                with io.open(FileSend["namefile"],FileSend["typefile"]) as file:
                    i=-1
                    while(True):
                        st=file.read(FileSend["sizeblock"])
                        # Отправляем данные браузеру
                        sizeblockfile=len(st)
                        i=i+1
                        try:
                            conn.send(st)
                        except:
                            print("Ошибка страницы")
                            del sizeblockfile
                            del i
                            del st
                            break
                        del st
                        mem=gc.mem_free()
                        print(f"Блок {i} файла {FileSend["namefile"]}")
                        print(f"Отравлено {sizeblockfile} байт. Осталось ОЗУ {mem} байт")     
                        if (sizeblockfile<FileSend["sizeblock"]):
                            del sizeblockfile
                            del i
                            break
                        del sizeblockfile        
            except:
                print("File not found")  
        del FileSend
        del request
        conn.close()
        mem=gc.mem_free()
        print(f"Осталось памяти в конце {mem} байт")
        print("------------------------------------")
        
#===========================================

        
        
        
        
        
